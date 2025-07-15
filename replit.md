# Artwork Image Manager

## Overview

This is a Flask-based web application for managing artwork images with AI-powered content generation capabilities. The system allows users to upload artwork images, organize them by categories, and generate descriptions, hashtags, and other metadata using OpenAI's GPT service. It features a modern Bootstrap frontend with real-time content editing and export functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (configured via DATABASE_URL environment variable)
- **API Pattern**: RESTful endpoints for image management and content generation
- **File Storage**: Local file system storage in `static/uploads` directory
- **AI Integration**: OpenAI GPT service for content generation with rate limiting

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Styling**: Custom CSS with Bootstrap framework
- **Real-time Updates**: AJAX-based interactions for seamless user experience

## Key Components

### Data Models
- **Image Model**: Central entity storing artwork metadata
  - Fields: id, original_filename, stored_filename, description, hashtags, category, post_title, key_points, created_at
  - Includes `to_dict()` method for JSON serialization

### Core Services
- **GPT Service**: Handles OpenAI API integration with rate limiting
  - Generates descriptions and hashtags for artwork
  - Supports content refinement based on user feedback
  - Implements simple rate limiting to prevent API abuse

### File Management
- **Upload System**: Secure file handling with unique filename generation
- **File Validation**: Supports PNG, JPG, JPEG, GIF formats
- **Size Limits**: 16MB maximum file size
- **Storage**: Local storage with UUID-based naming convention

### Frontend Features
- **Image Table**: Dynamic table displaying all uploaded artwork
- **Content Editing**: In-place editing for titles and descriptions
- **Content Generation**: AI-powered content creation with feedback system
- **Export Functionality**: CSV export of artwork metadata
- **Progress Tracking**: Upload progress indicators

## Data Flow

1. **Image Upload**: User selects files → Validation → Unique filename generation → File storage → Database record creation
2. **Content Generation**: User triggers generation → GPT service call → Content display → User feedback loop
3. **Content Editing**: User modifies content → AJAX update → Database synchronization
4. **Export**: User requests export → Database query → CSV generation → File download

## External Dependencies

### Required APIs
- **OpenAI API**: For GPT-based content generation (requires OPENAI_API_KEY)

### Python Packages
- Flask & Flask-SQLAlchemy for web framework and ORM
- OpenAI client library for AI integration
- Standard libraries: os, uuid, datetime, csv, io

### Frontend Dependencies
- Bootstrap 5.3.2 (CDN)
- Bootstrap Icons (CDN)
- Custom CSS and JavaScript files

### Database Requirements
- PostgreSQL database accessible via DATABASE_URL
- Automatic table creation on startup
- Migration support for schema updates

## Deployment Strategy

### Environment Configuration
- **Database**: PostgreSQL connection via DATABASE_URL environment variable
- **Security**: Flask secret key via FLASK_SECRET_KEY or default for development
- **AI Service**: OpenAI API key via OPENAI_API_KEY environment variable
- **File Storage**: Local filesystem with automatic directory creation

### Application Structure
```
app.py           # Main application factory and configuration
main.py          # Application entry point
models.py        # Database models
routes.py        # API endpoints and request handlers
gpt_service.py   # OpenAI integration service
utils.py         # Utility functions and file handling
migrations.py    # Database migration scripts
templates/       # Jinja2 templates
static/          # CSS, JS, and uploaded files
```

### Development Features
- Automatic database table creation
- Development-friendly configuration defaults
- Error handling and user feedback
- Placeholder content generation for testing

### Future Enhancements
- Cloud storage integration (Google Drive/Dropbox) - placeholder code included
- Enhanced content generation with image analysis
- User authentication and authorization
- Advanced categorization and tagging systems
- Batch processing capabilities

The application follows Flask best practices with clear separation of concerns, comprehensive error handling, and a modern, responsive user interface. The GPT integration provides intelligent content generation while maintaining user control through feedback mechanisms.