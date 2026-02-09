# Prompt Post - Simplified Calendar-to-Publer Pipeline

## Overview
Simplified Flask app that fetches astrology calendars (ICS), parses events, and prepares them as drafts for Publer social media scheduling.

## Architecture
- **Backend:** Flask + SQLAlchemy ORM
- **Database:** PostgreSQL (Neon-hosted)
- **Social Media:** Publer API for draft creation
- **Calendar:** ICS format parsing (fetch from URL or upload file)
- **Auth:** Simple admin login (username/password)

## Core Flow
1. Fetch or upload astrology calendar (.ics) - supports AB, YP, POF types
2. Events are parsed and stored with dates/times
3. Write social media copy per event
4. Push ready events to Publer as drafts

## Project Structure
```
app.py              - Flask app setup, DB config
main.py             - Entry point
models.py           - Calendar, CalendarEvent, Settings models
routes.py           - All API endpoints
utils.py            - ICS parsing utilities
publer_service.py   - Publer API client
migrations.py       - Schema migrations
templates/          - Jinja2 templates (base, index, login, 403)
static/js/main.js   - Frontend JavaScript
static/css/style.css - Styles
```

## Database Models
- **Calendar** - stores calendar type (AB/YP/POF), name, ICS URL
- **CalendarEvent** - individual events with dates, social copy, Publer status
- **Settings** - brand settings (company name, hashtag, shop URL)

## API Endpoints
- `GET /api/calendars` - list calendars
- `POST /api/calendars/fetch` - fetch from ICS URL
- `POST /api/calendars/import` - upload .ics file
- `DELETE /api/calendars/:id` - delete calendar
- `GET /api/events` - list events (filterable by calendar_type)
- `POST /api/events/:id/copy` - update social copy
- `GET /api/publer/test` - test Publer connection
- `POST /api/publer/push` - push events to Publer
- `GET/POST /api/settings` - brand settings

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `PUBLER_API_KEY` - Publer API key
- `PUBLER_WORKSPACE_ID` - Publer workspace ID
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Login credentials (default: admin/123)
- `SESSION_SECRET` - Flask session secret

## Recent Changes (February 2026)
- Simplified from full artwork management system to focused calendar-to-Publer pipeline
- Removed: image uploads, collections, GPT vision, Dynamic Mockups, fal.ai video, FeedHive, schedule grid
- Added: ICS URL fetching, inline social copy editing, streamlined Publer push
