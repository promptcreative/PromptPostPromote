# Painting Content Planner

## Overview

This is a Flask-based content planning and scheduling system for artwork across multiple social media platforms. The system integrates with Publer for automated content scheduling, supports .ics calendar imports for optimal time slot assignment, and provides AI-powered content generation for platform-specific needs (Instagram, Pinterest, Etsy, etc.).

## Recent Changes (November 2025)

**Calendar Priority Logic Fix (November 10, 2025):**
- Fixed calendar generation to properly prioritize AB (Astro Batching) events over YP/POF events on each day
- Per-day priority assignment: AB events get first slots, then YP and POF are mixed with equal priority
- Random optimal times now only used for days with ZERO astrology events (Fill All Days strategy)
- Example: Nov 10 with 2 AB + 1 YP assigns as [AB, AB, YP] not random mix

**Calendar Cleanup & Natural Synthetic Times (November 10, 2025):**
- Natural synthetic times: Changed from round hours (9:00, 12:00, 3:00) to varied times (9:17, 11:43, 14:28, 17:51, 20:14)
- Bulk Delete button: Select multiple items in Content tab and delete them all at once
- Delete Empty Slots button: Removes all calendar slot placeholders (`[Calendar Slot]`) with one click
- Reset Calendar Events button: Marks all astrology events as unassigned so they can be reused in new calendar generations
- Fixed placeholder overflow issue: 2,415+ placeholder slots were flooding the Content tab from repeated generations
- Automatic calendar event cleanup: Deleting items also resets their associated calendar events
- User workflow: Delete Empty Slots → Reset Calendar Events → Generate fresh schedule with astrology times

**Day-by-Day Schedule Preview (November 2025):**
- Simple calendar generation with defaults: 2 Instagram, 2 Pinterest, 3-hour spacing
- Interactive schedule preview modal showing day-by-day format with formatted dates
- Platform emojis (📸 Instagram, 📌 Pinterest) and calendar source badges (AB/YP/POF)
- Print-friendly layout for hard copy review of scheduling logic
- CSV export of generated schedule (Date, Time, Platform, Calendar Source)
- Backend chronological sorting by actual time (not string) prevents 10am-after-3pm bugs
- User workflow: Set sliders → Generate → Preview modal → Print/Export → Refresh to see in Content tab

**Collection/Series Management System:**
- Added Collection model for grouping artwork into series (e.g., "Accidental Iris", "Ocean Dreams")
- Grouped table view with expand/collapse per collection
- "Select All in Collection" and "Generate AI Content for Collection" quick actions
- Collection selector in upload form with inline collection creation
- Video file upload support (MP4, MOV, AVI, WEBM) alongside images
- GPT-4o Vision AI integration - analyzes actual artwork to generate platform-specific content
- CSV export includes collection name for organization in Publer
- AI-first workflow: Create Collection → Upload → AI Generate All → Edit → Export

**Previous: Publer Integration (November 2025):**
- Expanded database schema from 8 fields to 35+ Publer-compatible fields
- Added calendar import (.ics) functionality with midpoint time calculation
- Implemented batch processing for multi-platform content management
- Created comprehensive CSV export matching Publer's exact format
- Rebuilt frontend with tabbed interface for Content, Calendars, and Batch Actions

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (forced override of DATABASE_URL for stability)
- **API Pattern**: RESTful endpoints for content management, calendar import, batch operations
- **File Storage**: Local file system storage in `static/uploads` directory
- **AI Integration**: OpenAI GPT service for platform-specific content generation

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **JavaScript**: Vanilla JavaScript with Bootstrap 5 components
- **Styling**: Custom CSS with Bootstrap framework
- **Interface**: Three-tab layout (Content, Calendars, Batch Actions)
- **Interactions**: Double-click cell editing, batch selection, modal detail editing

## Key Components

### Data Models

#### Collection Model
Groups related artwork into series/collections:
- **Fields**: id, name, description, thumbnail_image_id, created_at, updated_at
- **Relationship**: One-to-many with Image (images can belong to one collection)
- **Use Case**: Organize artwork series like "Accidental Iris" for batch operations

#### Image Model (Content Item)
Stores all Publer-compatible fields for multi-platform content:
- **Core Fields**: id, original_filename, stored_filename, collection_id (FK to Collection), created_at, updated_at
- **Content Fields**: title, painting_name, text, video_pin_pdf_title
- **Media Types**: Images (PNG, JPG, GIF) and Videos (MP4, MOV, AVI, WEBM)
- **Platform Fields**: platform, post_subtype, status, labels
- **Scheduling Fields**: date, time, calendar_selection
- **Media Fields**: media, media_source, media_urls, cover_image_url, links
- **Platform-Specific**:
  - Instagram: instagram_first_comment
  - Pinterest: pinterest_description, pinterest_link_url, pin_board_fb_album_google_category
  - Etsy: etsy_description, etsy_listing_title, etsy_price, etsy_quantity, etsy_sku
  - SEO: seo_title, seo_description, seo_tags
  - Facebook: cta, comments
- **Other**: alt_text, post_url, reminder

#### Calendar Model
Stores imported calendar data:
- Fields: id, calendar_type (AB/YP/POF), calendar_name, created_at, updated_at
- Relationship: One-to-many with CalendarEvent

#### CalendarEvent Model
Stores individual calendar events with calculated midpoints:
- Fields: id, calendar_id, summary, start_time, end_time, midpoint_time, event_type, is_assigned
- Used for optimal time slot assignment to content items

### Core Services

#### GPT Service (gpt_service.py)
- **Vision AI**: Uses GPT-4o to analyze actual artwork images and generate content
- Generates platform-specific content based on what the AI sees (colors, style, composition)
- **Platforms**: Instagram (caption + hashtags), Pinterest (description + SEO), Etsy (full listing), or ALL at once
- Implements rate limiting to prevent API abuse
- Legacy text-based generation available for backward compatibility

#### Calendar Parser (utils.py)
- Parses .ics (iCalendar) file format
- Extracts VEVENT blocks with DTSTART and DTEND
- Calculates midpoint timestamps for optimal posting times
- Handles multiple datetime formats (YYYYMMDDTHHMMSS, YYYYMMDD)

#### Migration System (migrations.py)
- Safe schema migration with complete data preservation
- Legacy field mapping:
  - category → painting_name
  - post_title → title
  - description → text
  - hashtags → seo_tags
  - key_points → reminder
- Automatic detection of existing schema
- Calendar table creation

### API Endpoints

#### Collection Management
- `GET /collections` - List all collections
- `POST /collections` - Create new collection
- `PUT /collections/<id>` - Update collection details
- `DELETE /collections/<id>` - Delete collection (images preserved, collection_id nulled)
- `GET /collections/<id>/images` - Get all images in a collection

#### Content Management
- `POST /upload` - Upload artwork images/videos (with optional collection_id)
- `GET /images` - Retrieve all content items
- `POST /update/<id>` - Update single field
- `POST /batch_update` - Update multiple items at once (with field validation)
- `POST /generate_content/<id>` - Vision AI content generation for specific platform or all
- `POST /remove_image/<id>` - Delete content item

#### Calendar Management
- `GET /calendars` - List all imported calendars
- `POST /calendar/import` - Import .ics calendar file
- `GET /calendar/<id>/events` - Get available time slots
- `POST /assign_times` - Batch assign calendar times to selected content

#### Export
- `GET /export` - Download Publer-compatible CSV with all 33 required columns

### Frontend Features

#### Content Tab
- Image upload with progress tracking
- Content table with inline editing (double-click cells)
- Checkbox selection for batch operations
- Quick actions: Edit details modal, Remove item
- Visual indicators: Preview thumbnails, status badges, calendar assignments

#### Calendars Tab
- .ics file import interface
- Calendar type selection (AB, YP, POF)
- Display of loaded calendars with event counts
- Automatic calendar selector population

#### Batch Actions Tab
- **Assign Times**: Automatically assign optimal posting times from selected calendar
- **Batch Update**: Update platform, post type, or status for multiple items
- **AI Content Generation**: Generate platform-specific content for selected items

## Data Flow

### Complete Workflow
1. **Upload**: User uploads artwork images → Files saved to static/uploads → Database records created with default status
2. **Metadata Entry**: User edits painting names, platforms, post types via double-click or detail modal
3. **Calendar Import**: User uploads .ics files → Events parsed → Midpoints calculated → Stored in database
4. **Time Assignment**: User selects content items → Chooses calendar → System assigns optimal times sequentially
5. **Content Generation**: User triggers AI generation → Platform-specific content created → Stored in appropriate fields
6. **Export**: User downloads CSV → Publer-compatible format with all fields → Ready for import to Publer

### Legacy Data Migration Flow
1. Detect old schema (8 fields)
2. Backup all existing data
3. Drop old table
4. Create new schema (35+ fields)
5. Restore data with field mapping
6. Create Calendar tables

## External Dependencies

### Required APIs
- **OpenAI API**: For GPT-based content generation (OPENAI_API_KEY environment variable)

### Python Packages
- flask, flask-sqlalchemy: Web framework and ORM
- openai: AI content generation
- psycopg2-binary: PostgreSQL driver (unused, SQLite forced)
- email-validator: Email validation utilities

### Frontend Dependencies
- Bootstrap 5.3.2 (CDN): UI framework
- Bootstrap Icons (CDN): Icon library
- Custom CSS (style.css): Additional styling
- Custom JavaScript (main.js): Interactive functionality

### Database
- **Current**: SQLite (hardcoded in app.py)
- **Design**: PostgreSQL-compatible schema
- **Migration**: Automated with data preservation

## Security Features

- **Field Validation**: Batch updates restricted to safe fields only
- **File Upload**: Type validation, size limits (16MB), secure filename generation
- **SQL Injection**: Parameterized queries throughout
- **Immutable Fields**: id, created_at, updated_at protected from user modification

## Application Structure

```
app.py              # Flask app configuration, forced SQLite database
main.py             # Application entry point, database initialization
models.py           # Image, Calendar, CalendarEvent models
routes.py           # All API endpoints with field validation
gpt_service.py      # OpenAI integration for content generation
utils.py            # File handling, .ics parsing, unique filename generation
migrations.py       # Schema migration with complete data preservation
templates/
  base.html         # Base template with navigation
  index.html        # Main interface with three tabs
static/
  css/style.css     # Custom styling
  js/main.js        # Frontend logic (upload, editing, batch actions)
  uploads/          # Uploaded artwork images
```

## Development Features

- Automatic database initialization on startup
- Safe schema migration with data preservation
- Inline editing with instant feedback
- Progress indicators for uploads and batch operations
- Error handling with user-friendly messages
- Modal editing for detailed field access

## Future Enhancements

- Direct Publer API integration (currently CSV export only)
- Image analysis for automatic content generation
- Multi-language content generation
- Advanced scheduling algorithms (engagement optimization)
- User authentication and multi-user support
- Cloud storage integration (currently local only)
- Analytics dashboard for content performance

## Technical Notes

- SQLite database forced in app.py (line 13) for development stability
- Migration Runner workflow only needs to run once per schema change
- Calendar events marked as "assigned" to prevent time slot conflicts
- CSV export includes all 33 Publer-required columns in exact order
- Batch operations support checkbox selection for user convenience

The application now serves as a comprehensive content planning system for multi-platform artwork promotion, with calendar-based scheduling and AI-assisted content creation.
