# Painting Content Planner

## Overview

This project is a Flask-based content planning and scheduling system designed for artists to manage their artwork promotion across various social media platforms. Its primary purpose is to streamline content creation and scheduling by integrating with Publer for automated posting, leveraging .ics calendar imports for optimal time slot allocation, and utilizing AI-powered content generation tailored for platforms like Instagram, Pinterest, and Etsy. The system aims to provide an AI-first workflow, from artwork upload and content generation to organized export for social media management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The frontend uses Jinja2 templates with Bootstrap 5 dark theme for a modern and responsive interface. It features a three-tab layout (Content, Calendars, Batch Actions) to organize functionality, enhanced with vanilla JavaScript for interactive elements like double-click cell editing, batch selection, and modal detail editing. Platform-specific emojis and calendar source badges are used for visual clarity.

### Technical Implementations
- **Backend**: Built with Flask and SQLAlchemy ORM, using SQLite as the database for stability. It exposes RESTful endpoints for content, calendar, and batch operations.
- **Frontend**: Utilizes Bootstrap 5 and custom JavaScript for dynamic interactions.
- **AI Integration**: Employs OpenAI's GPT service, specifically GPT-4o Vision AI, to analyze uploaded artwork and generate platform-specific content (e.g., captions, descriptions, SEO tags) for various social media channels.
- **File Storage**: Uploaded artwork (images and videos) is stored locally in the `static/uploads` directory.
- **Calendar Processing**: Includes a robust parser for .ics files, capable of extracting event details and calculating midpoint times for scheduling. Priority logic ensures astrological events (AB/YP/POF) are scheduled optimally.
- **Data Models**:
    - `Collection`: Organizes artwork into series for batch actions.
    - `Image`: Stores all Publer-compatible fields for multi-platform content items, supporting both images and videos.
    - `Calendar`: Stores imported calendar data.
    - `CalendarEvent`: Stores individual events from imported calendars with calculated midpoints for scheduling.

### Feature Specifications
- **Content Management**: Supports uploading artwork, managing collections, inline editing of content details, and batch operations.
- **Calendar Management**: Allows importing .ics files, viewing calendars, and assigning optimal times to content based on calendar events.
- **AI Content Generation**: Generates platform-specific content by analyzing artwork visually.
- **Scheduling**: Enables day-by-day schedule previews, calendar event prioritization, and flexible assignment of time slots.
- **Export**: Generates Publer-compatible CSV files with 12-column or 33-column formats, including chronological ordering and placeholders for empty slots.
- **Migration System**: Ensures safe schema evolution with data preservation and automatic detection of existing database structures.

### System Design Choices
- **Modularity**: The system is structured into clear components (models, routes, services, utilities) for maintainability.
- **User Workflow**: Designed for an AI-first approach, guiding the user from uploading artwork to generating content and exporting schedules.
- **Robustness**: Includes features like bulk deletion, empty slot removal, and calendar event resetting for efficient content management.
- **Data Integrity**: Implements field validation, secure file handling, and parameterized queries to ensure data security and consistency.

## External Dependencies

### Required APIs
- **OpenAI API**: Used for GPT-based content generation, requiring an `OPENAI_API_KEY` environment variable.

### Python Packages
- `flask`: Web framework.
- `flask-sqlalchemy`: ORM for database interactions.
- `openai`: Python client for OpenAI API.
- `email-validator`: For email format validation.

### Frontend Dependencies
- **Bootstrap 5.3.2**: UI framework, sourced via CDN.
- **Bootstrap Icons**: Icon library, sourced via CDN.

### Database
- **SQLite**: The primary database used, hardcoded in `app.py` for development and stability. The schema is designed to be compatible with PostgreSQL for potential future scaling.