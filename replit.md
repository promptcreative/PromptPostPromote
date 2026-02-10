# Astrobatching Platform

## Overview
Astrobatching platform that calculates personalized posting times from birth data using multiple astrological calendar systems (Vedic, Magi/PTI, Personal), finds overlapping "golden windows" through Double GO detection and Bird Batch timing, confirms with microtransits (Yogi Point, Part of Fortune, Ascendant), and exports results to Publer for social media scheduling. Supports agency-style multi-client management.

## Architecture
- **Backend:** Flask + SQLAlchemy ORM (Python 3.11)
- **Database:** PostgreSQL (Neon-hosted via DATABASE_URL)
- **Frontend:** Jinja2 templates with vanilla JS, pastel UI design
- **Social Media:** Publer API for draft creation
- **Astro Engines:** PTI Collective, Vedic Collective, Enhanced Personal Transit, Bird Batch Filter, AstroBatch Detector, Combined Calendar Analyzer
- **Auth:** Email-based session auth

## Design System
- Background: #FFF8F0
- Dark text: #2D2B3D
- Font: DM Sans
- Soft rounded elements, pastel accents
- Consistent across all pages

## Project Structure (rebuild/)
```
app.py                      - Flask app setup, DB config, blueprint registration
database/models.py          - All SQLAlchemy models (Profile, CalendarData, Client, etc.)
database/manager.py         - Database manager for calendar data persistence
routes/pages.py             - Page routes (dashboard, clients, results, etc.)
routes/clients.py           - Client CRUD + calendar generation/retrieval API
routes/api.py               - Profile, calendar generation, Publer APIs
helpers/dashboard.py        - Core dashboard generation logic
helpers/utils.py            - JSON serialization, normalization utilities
core/combined_calendar.py   - Combined calendar analyzer (merges all engines)
core/magi_collective.py     - PTI/Magi astrology engine
core/vedic_collective.py    - Vedic astrology engine
core/personal_transit.py    - Personal transit calculator
filters/bird_batch_filter.py - Bird batch timing filter
filters/astro_batch_detector.py - AstroBatch detector
templates/                  - Jinja2 templates (pastel UI)
  account_dashboard.html    - Main dashboard
  clients.html              - Client management page
  client_results.html       - Per-client calendar results
  login.html, base.html     - Auth and layout
```

## Database Models
- **Profile** - user birth data and preferences
- **CalendarData** - generated calendar data (JSON) per user/client
- **Client** - agency clients with birth data, location, calendar status
- **Settings** - brand settings (company name, hashtag, shop URL)

## Key API Endpoints
- `GET/POST /api/profile` - user profile management
- `POST /api/generate-dashboard` - generate full calendar suite
- `GET /api/clients` - list clients for current admin
- `POST /api/clients` - create new client
- `PUT /api/clients/:id` - update client
- `DELETE /api/clients/:id` - delete client + calendar data
- `POST /api/clients/:id/generate` - generate all 5 calendars for client
- `GET /api/clients/:id/calendar` - retrieve client's calendar results
- `GET/POST /api/settings` - brand settings
- `POST /api/publer/push` - push events to Publer

## Agency Multi-Client System
- Admin users manage multiple clients via `/clients` page
- Each client stores: name, birth data (date/time/location), current location
- Calendar generation runs all 5 engines per client using `generate_dashboard_core`
- Client data stored with `client_{id}` as user_id in CalendarData
- Calendar status: pending → generating → ready (or error)
- Results page at `/clients/{id}/results` shows golden windows, bird periods, full calendar

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `PUBLER_API_KEY` - Publer API key
- `PUBLER_WORKSPACE_ID` - Publer workspace ID
- `SESSION_SECRET` - Flask session secret

## User Preferences
- Modern pastel UI with soft rounded elements
- Agency-style multi-client management
- No redundant action buttons in dashboard
- DM Sans font throughout

## Recent Changes (February 2026)
- Built agency multi-client system with CRUD, generation, and results viewing
- Created client results page with golden windows, bird periods, full calendar table
- Fixed timezone_offset parameter handling in client generation flow
- Redesigned all pages to match pastel UI design system
- Wired calendar generation to existing 5-engine pipeline per client
