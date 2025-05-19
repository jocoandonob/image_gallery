
import os
import boto3
import json
from botocore.exceptions import ClientError
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'winston-gallery-secure-key-2025')

# Database Configuration - Use AWS RDS
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://postgres:unXcvu24cb7Y8yDV-Zicnko_QDLqP7@winston-public-1747647416.cpihf2p85fkq.us-east-1.rds.amazonaws.com:5432/winstongallery'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# S3 Configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET', 'winstongalleryvpcs3stack-winstonbucketa8d7d211-od7vfmty6wdu')
app.config['S3_REGION'] = os.environ.get('S3_REGION', 'us-east-1')
app.config['S3_URL_EXPIRATION'] = int(os.environ.get('S3_URL_EXPIRATION', 3600))  # 1 hour

# Initialize S3 client
s3_client = boto3.client('s3', region_name=app.config['S3_REGION'])

# Function to generate pre-signed URL for S3 objects
def get_presigned_url(object_name, expiration=3600):
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                   Params={'Bucket': app.config['S3_BUCKET'],
                                                           'Key': object_name},
                                                   ExpiresIn=expiration)
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
    return response

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # S3 object key
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category', backref='images')
    tags = db.relationship('Tag', secondary=image_tags, lazy='subquery',
                           backref=db.backref('images', lazy=True))
    
    def get_url(self):
        """Generate a pre-signed URL for the image"""
        return get_presigned_url(self.filename, app.config['S3_URL_EXPIRATION'])

class Tag(db.Model):
    __tablename__ = 'tags'
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
    category_filter = request.args.get('category')
    search_query = request.args.get('search')
    
    # Base query
    query = Image.query
    
    # Apply filters if provided
    if tag_filter and tag_filter.strip():
        tag = Tag.query.filter_by(name=tag_filter).first()
        if tag:
            query = query.filter(Image.tags.contains(tag))
    
    if category_filter and category_filter.strip():
        # Filter by category ID
        query = query.filter(Image.category_id == category_filter)
    
    if search_query and search_query.strip():
        query = query.filter(
            (Image.title.ilike(f'%{search_query}%')) | 
            (Image.description.ilike(f'%{search_query}%'))
        )
    
    # Get all images with filters applied
    images = query.order_by(Image.upload_date.desc()).all()
    
    # Get all tags and categories for the filter dropdowns
    all_tags = Tag.query.order_by(Tag.name).all()
    all_categories = Category.query.order_by(Category.name).all()
    
    return render_template('gallery.html', 
                          images=images, 
                          all_tags=all_tags,
                          all_categories=all_categories)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # Get all categories for the form
    categories = Category.query.order_by(Category.name).all()
    
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
            
            # Upload file to S3
            try:
                s3_client.upload_fileobj(
                    file,
                    app.config['S3_BUCKET'],
                    unique_filename,
                    ExtraArgs={
                        'ContentType': file.content_type
                    }
                )
            except ClientError as e:
                raise Exception(f"S3 upload failed: {str(e)}")
            
            # Get form data
            title = request.form.get('title')
            if not title:
                flash('Title is required', 'danger')
                return redirect(request.url)
                
            description = request.form.get('description', '')
            category_id = request.form.get('category')  # Now getting category_id directly
            if not category_id:
                flash('Category is required', 'danger')
                return redirect(request.url)
                
            tag_names = request.form.get('tags', '').split(',')
            
            # Create new image record
            new_image = Image(
                filename=unique_filename,  # Store S3 object key
                title=title,
                description=description,
                user_id=current_user.id,
                category_id=category_id
            )
            
            # Add and commit the image first to get an ID
            db.session.add(new_image)
            db.session.commit()
            
            # Now process tags
            for tag_name in tag_names:
                tag_name = tag_name.strip()
                if tag_name:
                    # Check if tag exists, create if not
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                        db.session.commit()  # Commit to get tag ID
                    
                    # Check if this tag is already associated with the image
                    if tag not in new_image.tags:
                        new_image.tags.append(tag)
            
            # Commit the tag associations
            db.session.commit()
            
            flash(f'Image "{title}" uploaded successfully!', 'success')
            return redirect(url_for('gallery'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading image: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html', categories=categories)

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

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            # Check if category already exists
            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('Category already exists', 'danger')
            else:
                category = Category(name=name)
                db.session.add(category)
                db.session.commit()
                flash('Category added successfully!', 'success')
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=categories)

# Create database tables
with app.app_context():
    try:
        # Create tables
        db.create_all()
        print("Database tables created successfully")
        
        # Create default categories if none exist
        if not Category.query.first():
            default_categories = ['Nature', 'Architecture', 'People', 'Animals', 'Travel', 'Food', 'Art', 'Other']
            for cat_name in default_categories:
                db.session.add(Category(name=cat_name))
            db.session.commit()
            print("Default categories created")
        
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
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
    
