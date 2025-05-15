# Flask Image Gallery Application

A responsive web application for managing and displaying images with user authentication.

## Features

- User authentication (register, login, logout)
- Image upload with title, description, and tags
- Responsive masonry grid layout for image display
- Filter images by tags
- Search images by title or description
- Image preview modal
- Responsive design for all devices

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript, HTML, and CSS
- **Authentication**: Flask-Login
- **Image Processing**: Pillow

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL database:
   ```
   python create_db.py
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Access the application at `http://localhost:5000`

## Database Configuration

The application uses PostgreSQL. You can configure the database connection in the `.env` file:

```
DATABASE_URL=postgresql://username:password@localhost:5432/gallery
```

## Default Login

- Username: admin
- Password: admin

## Project Structure

```
image_gallery/
├── app.py                 # Main Flask application
├── create_db.py           # Database initialization script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── static/
│   ├── css/
│   │   └── style.css      # CSS styles
│   ├── js/
│   │   └── main.js        # JavaScript functionality
│   └── uploads/           # Uploaded images
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Landing page
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── gallery.html       # Image gallery
    ├── upload.html        # Image upload form
    └── image.html         # Individual image view
```

## License

This project is open source and available under the MIT License.