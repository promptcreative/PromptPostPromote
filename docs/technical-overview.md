# Technical Overview - Painting Content Planner

**Last Updated:** November 16, 2025  
**Tech Stack:** Flask (Python), PostgreSQL, OpenAI GPT-4 Vision, Publer API  
**Authentication:** Basic admin login (username: `admin`, password: `123`)

---

## System Architecture

**Backend:** Flask with SQLAlchemy ORM  
**Database:** PostgreSQL (Neon-hosted)  
**AI Service:** OpenAI GPT-4 Vision for platform-specific content generation  
**Social Media:** Publer API for automated posting to Instagram/Pinterest/Facebook  
**File Storage:** Local filesystem (`static/uploads/`)

---

## Core Features (Active)

### 1. Content Management
- **Upload:** Multi-file image upload with collection grouping
- **AI Generation:** GPT-4 Vision analyzes artwork and generates platform-specific content
  - Instagram captions + hashtags (`instagram_first_comment`)
  - Pinterest descriptions + hashtags (`pinterest_hashtags`)
  - SEO tags, Etsy descriptions, alt text
- **Settings:** Brand configuration (company name, tone, hashtag limits, shop URL)
- **Status Workflow:** Draft → Ready → Scheduled

### 2. Calendar Management
- **Import:** Parse .ics files from 3 astrology calendars (AB/YP/POF)
- **Midpoint Calculation:** Extracts optimal posting time from event start/end
- **Calendar Badges:** Visual indicators (🔮 AB, 🧘 YP, 💰 POF)
- **Assignment:** Manual slot-by-slot assignment or batch "Fill All Days"

### 3. Publer Integration
- **Auto-Post:** Push scheduled content to Publer with API
- **Post ID Tracking:** Saves `publer_post_id` in EventAssignment table
- **Auto-Delete on Sale:** Marks collection Pending/Shipped → deletes ALL Publer posts
- **Platform Support:** Instagram, Pinterest, Facebook (requires pre-configured accounts)

### 4. Export
- **Publer CSV:** 12-column format with media URLs, labels, timestamps
- **FeedHive CSV:** 7-column alternative export format

---

## Pending Features (Not Implemented)

### Smart Scheduler UI
- UI exists but AI auto-assignment logic NOT active
- Manual assignment works, batch "Fill All Days" works
- AI slot optimization pending

### Video Support
- Upload: Not implemented
- Mockups: Not implemented
- GPT-4 Vision can analyze videos, but upload UI blocks non-images

### Dynamic Mockups
- `dynamic_mockups_service.py` exists but NOT connected to UI
- No "Generate Mockups" button functionality yet

### Weekly Planner View
- Calendar grid shows day-by-day only
- No week-at-a-glance visualization

### Etsy Automation
- Awaiting Etsy API approval
- Will add webhook listener for sold-item detection
- Current: Manual mark as Pending/Shipped triggers auto-delete

---

## Key API Endpoints

### Authentication
- `POST /login` - Admin login (username/password)
- `GET /logout` - Clear session

### Content
- `POST /upload` - Upload images with optional collection_id
- `POST /generate_content` - GPT-4 Vision AI content generation
- `GET /images` - List all images with filters (status, availability)
- `POST /remove_image/<id>` - Delete image (checks for assignments)
- `POST /bulk_delete` - Delete multiple images (deletes EventAssignments first)

### Collections
- `POST /collections` - Create collection
- `GET /collections` - List all collections
- `PUT /collections/<id>` - Update collection (triggers auto-delete if Pending/Shipped)
- `DELETE /collections/<id>` - Delete collection (preserves images)

### Calendar
- `POST /upload_calendar` - Import .ics file
- `GET /calendars` - List all calendars
- `GET /api/calendar_events` - Get events for assignment modal
- `POST /api/assign` - Assign image to calendar slot (multi-platform support)
- `DELETE /api/assign/<id>` - Unassign content from slot

### Schedule
- `GET /api/scheduled` - List all scheduled assignments
- `POST /schedule/export_csv` - Export Publer CSV (selected slots)
- `POST /schedule/export_scheduled_csv` - Export all scheduled (Publer format)
- `POST /schedule/export_scheduled_feedhive` - Export all scheduled (FeedHive format)

### Publer
- `POST /publer/push` - Push scheduled content to Publer API (saves post IDs)
- Internal: `delete_post(post_id)` called when collection marked sold

### Settings
- `GET /api/settings` - Get brand settings
- `POST /api/settings` - Update settings (company name, tone, hashtags, shop URL)

---

## Database Schema

### Core Tables
- **image** - Artwork records (50+ columns for multi-platform content)
- **collection** - Groups related artwork (status: Available/Pending/Shipped/Sold)
- **calendar** - Imported .ics calendars (AB/YP/POF types)
- **calendar_event** - Individual events with midpoint_time
- **event_assignment** - Junction table (image_id + calendar_event_id + platform + publer_post_id)
- **settings** - Brand configuration (singleton table)

### Key Columns
- `image.painting_name` - Collection name or cleaned filename (used for display)
- `image.title` - Same as painting_name (Publer compatibility)
- `image.status` - Draft/Ready/Scheduled
- `image.availability_status` - Available/Sold/Hold
- `image.instagram_first_comment` - Instagram hashtags
- `image.pinterest_hashtags` - Pinterest hashtags (separate field!)
- `event_assignment.publer_post_id` - Tracks Publer post for deletion

---

## Platform Requirements

### Instagram
- Must link Instagram account to Facebook Business account (external to app)
- Required for automation features via Meta API

### Pinterest
- App auto-fetches "Original Art" board from Publer account
- Must have board created in Pinterest before scheduling

### Publer Account
- Requires API key + Workspace ID in environment variables
- Social accounts must be connected in Publer dashboard

---

## Known Issues & Limitations

### Astro Batching
- Calendar events divided at midpoint (start + end) / 2 for optimal time
- "Fill All Days" strategy:
  - **Astrology only**: Uses AB/YP/POF events exclusively
  - **Fill All**: Uses astrology events + default times (10am, 2pm, etc.) for gaps

### File Display Names
- New uploads: Uses collection name (clean display)
- Old uploads: May show raw filename (re-upload fixes this)
- Scheduled view shows `painting_name` field

### Deletion Logic
- Single image delete: Warns if scheduled, offers force delete
- Bulk delete: Auto-deletes EventAssignments before images (fixed Nov 16)
- Collection delete when Pending/Shipped: Calls Publer API to delete all posts

### Environment Variables
- `OPENAI_API_KEY` - Required for AI content generation
- `PUBLER_API_KEY` - Required for Publer integration
- `PUBLER_WORKSPACE_ID` - Publer workspace identifier
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Flask session encryption key
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Optional (defaults: admin/123)

---

## Testing Checklist

### Upload & Display
- [ ] Upload with collection → displays collection name
- [ ] Upload without collection → displays cleaned filename
- [ ] Scheduled tab shows painting name (not full caption)

### Deletion
- [ ] Delete unscheduled image → works immediately
- [ ] Delete scheduled image → shows warning with assignment details
- [ ] Bulk delete scheduled images → removes assignments first, no errors

### Calendar Assignment
- [ ] Import .ics → events appear with correct midpoint times
- [ ] Assign image to slot → saves in event_assignment table
- [ ] Multi-platform assignment → creates 3 separate records (IG + Pinterest + FB)

### Publer Integration
- [ ] Push to Publer → saves post IDs in event_assignment table
- [ ] Mark collection Pending/Shipped → deletes all Publer posts for that collection
- [ ] Pinterest posts use correct board ("Original Art")

### AI Content
- [ ] Generate with Vision AI → creates platform-specific content
- [ ] Settings brand name → appears in generated captions
- [ ] Hashtag limits → respects Instagram (3-15) and Pinterest (2-10) settings

---

## Migration Notes

**PostgreSQL Migration (Nov 16, 2025):**
- Migrated from SQLite to PostgreSQL
- Auto-migration script: `migrate_to_postgres.py`
- Schema updates via `migrations.py`
- Data loss during migration (user re-uploading 26 images)
- Old `flask_dance_oauth` and `users` tables removed (Replit Auth deprecated)

**Multi-Tenant Roadmap:**
- Future agency model documented in `docs/multi-tenant-roadmap.md`
- Not current priority (Etsy demo first)
