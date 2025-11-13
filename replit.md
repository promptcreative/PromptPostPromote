# Painting Content Planner

## Overview

This project is a Flask-based content planning and scheduling system designed for artists to manage their artwork promotion across various social media platforms. Its primary purpose is to streamline content creation and scheduling by integrating with Publer for automated posting, leveraging .ics calendar imports for optimal time slot allocation, and utilizing AI-powered content generation tailored for platforms like Instagram, Pinterest, and Etsy. The system aims to provide an AI-first workflow, from artwork upload and content generation to organized export for social media management.

## Recent Changes (November 2025)

**Pinterest Hashtags Separation - November 13, 2025:**
- ✅ **Dedicated Pinterest Hashtags Field** - Created separate `pinterest_hashtags` database column to prevent Instagram/Pinterest hashtag conflicts
- ✅ **Platform-Specific AI Generation** - GPT now generates distinct hashtags for Instagram (15-25) and Pinterest (15-20)
- ✅ **Isolated Export Logic** - FeedHive/Publer exports strictly use correct hashtag field per platform (no leakage!)
- ✅ **Character Limit Enforcement** - Runtime validation truncates Pinterest description (450 chars), board/title (90 chars)
- ✅ **7-Column FeedHive Format** - Added Notes column for calendar tracking (🔮 POF/YP/AB/General)
- Database migration: `pinterest_hashtags TEXT` column added via migrations.py
- Field mapping: `PINTEREST_HASHTAGS` → `pinterest_hashtags`, `IG_FIRST_COMMENT` → `instagram_first_comment`
- Export logic: Pinterest posts use `pinterest_hashtags`, Instagram posts use `instagram_first_comment`, other platforms default to Instagram hashtags
- ISO 8601 timestamp format: `2025-11-13T14:30:00.000Z`
- **User benefit**: No more hashtag overwriting! Each platform maintains its own optimized hashtag set 🎯

**FeedHive Export Integration - November 13, 2025:**
- ✅ **Dual Platform Export** - Now supports both Publer AND FeedHive CSV formats
- ✅ **7-Column FeedHive Format** - Text, Title, Media URLs, Labels, Social Medias, Scheduled, Notes
- ✅ **Complete AI Content Export** - Instagram captions + hashtags, Pinterest descriptions + hashtags, SEO tags all included
- ✅ **Dropdown Export Menus** - Both navbar and Scheduled tab have platform selection dropdowns
- Backend: `/export_feedhive` and `/schedule/export_scheduled_feedhive` endpoints
- Hashtags appear in Text column (published content) AND Labels column (tracking/filtering)
- User can now compare Publer vs FeedHive to see which platform better handles their AI-generated content! 🐝

**Scheduled Tab CSV Export Fix - November 12, 2025:**
- ✅ **Fixed Publer CSV Import** - Scheduled tab export now matches exact Publer format
- ✅ **Correct Column Names** - Updated to use "Media URLs" (plural), "Labels", "Alt text", "Comments", "Subtype"
- ✅ **HTTP Protocol for Media** - Changed URLs from https:// to http:// to match working format
- ✅ **12-Column Format** - Streamlined export with only essential Publer columns
- Backend: `/schedule/export_scheduled_csv` endpoint generates Publer-compatible CSV from EventAssignment records
- Images and content now import successfully into Publer without "Invalid URL" errors
- User workflow: Schedule Grid → Assign Content → Scheduled Tab → Export CSV → Import to Publer ✨

**Multi-Platform Assignment & Status Workflow - November 12, 2025:**
- ✅ **Status Tracking System** - Images now track workflow status (Draft → Ready → Scheduled)
- ✅ **Multi-Platform Assignments** - Assign one artwork to multiple platforms (Instagram, Pinterest, Facebook) in single action
- ✅ **Content Tab Filter** - Filter by All/Unscheduled/Scheduled status with live item count
- ✅ **Approve & Mark Ready Button** - Batch approve Draft items for scheduling (Edit & Review tab)
- ✅ **Checkbox Platform Selection** - Assignment modal now uses checkboxes with "All" toggle instead of dropdown
- ✅ **Smart Status Transitions** - Automatic Draft → Ready → Scheduled progression prevents downgrades
- ✅ **EventAssignment as Source of Truth** - Multi-platform data stored as separate records (one per platform)
- Backend: `/api/assign` endpoint handles multiple platforms in single transaction, skips duplicates gracefully
- User workflow: Upload → Generate AI Content → Approve → Assign to Calendar Slots → Export CSV ✨

**Schedule Grid CSV Export - November 11, 2025:**
- ✅ **CSV Export Working Perfectly** - Select individual time slots and export Publer-compatible CSV
- ✅ **Media URLs Included** - Publer automatically pulls images during CSV import (no API needed!)
- Event-level checkboxes for granular time slot selection
- Day-level checkboxes toggle all child events with indeterminate state
- Live selection counter badge (e.g., "3 selected")
- Backend endpoint `/schedule/export_csv` generates 12-column Publer format
- Chronological ordering, placeholder content for empty slots
- File download as `publer_schedule.csv` via Blob API
- **Publer API Research Documented** - See `docs/publer-api-integration.md` for full API attempt history
- **Auto-naming for uploads** - Images without collection now get auto-named from filename (title case)
- User workflow: Load Schedule → Check slots → Export CSV → Import to Publer ✨

**Key Discovery:** CSV export is more reliable than Publer API. Media hosting on Replit works perfectly - Publer pulls images directly from our URLs during import. No need for complex API integration!

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
    - `Image`: Stores all Publer-compatible fields for multi-platform content items, supporting both images and videos. Includes separate `instagram_first_comment` and `pinterest_hashtags` fields for platform-specific hashtag management.
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