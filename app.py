import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
# Ensure instance folder exists
os.makedirs('instance', exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
print(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists with absolute path
current_dir = os.path.abspath(os.path.dirname(__file__))
uploads_dir = os.path.join(current_dir, 'static', 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Check database connection
def check_db_connection():
    try:
        with db.engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("Database connected successfully!")
            return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False

# Verify database connection
check_db_connection()

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    images = db.relationship('Image', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Tag-Image association table (many-to-many)
image_tags = db.Table('image_tags',
    db.Column('image_id', db.Integer, db.ForeignKey('images.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Image(db.Model):
    __tablename__ = 'images'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.relationship('Tag', secondary=image_tags, lazy='subquery',
                           backref=db.backref('images', lazy=True))

class Tag(db.Model):
    __tablename__ = 'tags'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('gallery'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('gallery'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('gallery'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('gallery'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/gallery')
@login_required
def gallery():
    tag_filter = request.args.get('tag')
    search_query = request.args.get('search')
    
    # Base query
    query = Image.query
    
    # Apply filters if provided
    if tag_filter and tag_filter.strip():
        tag = Tag.query.filter_by(name=tag_filter).first()
        if tag:
            query = query.filter(Image.tags.contains(tag))
    
    if search_query and search_query.strip():
        query = query.filter(
            (Image.title.ilike(f'%{search_query}%')) | 
            (Image.description.ilike(f'%{search_query}%'))
        )
    
    # Get all images with filters applied
    images = query.order_by(Image.upload_date.desc()).all()
    
    # Get all tags for the filter dropdown
    all_tags = Tag.query.order_by(Tag.name).all()
    
    return render_template('gallery.html', images=images, all_tags=all_tags)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            # Check if the post request has the file part
            if 'image' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
            
            file = request.files['image']
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if not allowed_file(file.filename):
                flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
                return redirect(request.url)
                
            # Generate a unique filename to prevent overwriting
            original_filename = secure_filename(file.filename)
            extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{extension}"
            
            # Get absolute path to upload directory
            current_dir = os.path.abspath(os.path.dirname(__file__))
            uploads_dir = os.path.join(current_dir, 'static', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save file with absolute path
            file_path = os.path.join(uploads_dir, unique_filename)
            file.save(file_path)
            
            # Verify file was saved
            if not os.path.exists(file_path):
                raise Exception("Failed to save image file")
            
            # Get form data
            title = request.form.get('title')
            if not title:
                flash('Title is required', 'danger')
                return redirect(request.url)
                
            description = request.form.get('description', '')
            tag_names = request.form.get('tags', '').split(',')
            
            # Create new image record
            new_image = Image(
                filename=unique_filename,
                title=title,
                description=description,
                user_id=current_user.id
            )
            
            # Process tags
            for tag_name in tag_names:
                tag_name = tag_name.strip()
                if tag_name:
                    # Check if tag exists, create if not
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    
                    new_image.tags.append(tag)
            
            db.session.add(new_image)
            db.session.commit()
            
            flash(f'Image "{title}" uploaded successfully!', 'success')
            return redirect(url_for('gallery'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading image: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/image/<int:image_id>')
@login_required
def view_image(image_id):
    image = Image.query.get_or_404(image_id)
    return render_template('image.html', image=image)

@app.route('/api/tags')
@login_required
def get_tags():
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify([{'id': tag.id, 'name': tag.name} for tag in tags])

# Create database tables
with app.app_context():
    try:
        # Create tables
        db.create_all()
        print("Database tables created successfully")
        
        # Create a default admin user if no users exist
        if not User.query.first():
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        print("Try running create_db.py first to initialize the database")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)