# Astrobatching Platform

## Overview
Astrobatching platform that calculates personalized posting times from birth data using multiple astrological calendar systems (Vedic, Magi/PTI, Personal), finds overlapping "golden windows" through refined classification (OMNI, Double GO, Good), filters microtransits (Yogi Point, Part of Fortune) to background days only, computes Micro Bird precision posting times, and exports via calendar subscriptions (ICS) and Publer API. Supports agency-style multi-client management.

## Architecture
- **Backend:** Flask + SQLAlchemy ORM (Python 3.11)
- **Database:** PostgreSQL (Neon-hosted via DATABASE_URL)
- **Frontend:** Jinja2 templates with vanilla JS, pastel UI design
- **Social Media:** Publer API for draft creation
- **Astro Engines:** PTI Collective, Vedic Collective, Enhanced Personal Transit, Bird Batch Filter, AstroBatch Detector, Combined Calendar Analyzer
- **Microtransit Engines:** Yogi Point (yp.py), Part of Fortune (wb1.py), Western/Vedic bridges (wb2, wb3, vb1, vb2)
- **Auth:** Email-based session auth

## Design System
- Background: #FFF8F0
- Dark text: #2D2B3D
- Font: DM Sans
- Soft rounded elements, pastel accents
- Consistent across all pages

## Classification Rules (STRICT)
- **OMNI** = PTI (Best/Go) + Vedic (GO/Mild GO/Build) + Personal (power/supportive) — all 3 systems aligned
- **DOUBLE GO** = PTI (Best/Go) + Vedic (GO/Mild GO/Build) — ignores Personal
- **GOOD** = 2 systems positive, NEVER if PTI Worst
- **PTI Worst** = hard exclusion from background days
- **Background days** = OMNI + DOUBLE GO + GOOD only (these are "green" days for posting)

## Pipeline Flow
1. **Calendar Generation** → Run all 5 engines (PTI, Vedic, Personal, Bird Batch, Combined)
2. **Power Days** → Extract OMNI, Double GO, Good days from combined results
3. **Bird Batch on Background** → Filter bird batch periods to only background days
4. **Yogi Point on Background** → Calculate YP transits, filter to background days only
5. **Part of Fortune on Background** → Calculate PoF transits, filter to background days only
6. **Micro Bird** → Find where microtransits (YP/PoF) overlap with bird batch windows = precision posting times
7. **ICS Feeds** → Subscribe to background-filtered calendars in Google Calendar
8. **Publer Push** → Push Micro Bird events as scheduled draft posts

## Project Structure (rebuild/)
```
app.py                         - Flask app setup, DB config, blueprint registration
database/models.py             - All SQLAlchemy models (Profile, CalendarData, Client, etc.)
database/manager.py            - Database manager for calendar data persistence
routes/pages.py                - Page routes (dashboard, clients, results, etc.)
routes/clients.py              - Client CRUD + calendar generation/retrieval API
routes/api.py                  - Profile, calendar generation APIs
routes/power_days.py           - Power Days API (classified days, filtered microtransits, bird batch)
routes/publer.py               - Publer integration (test, accounts, push microbird, push generic)
routes/ics_feeds.py            - ICS calendar subscription feeds (all + background-filtered)
routes/microtransits.py        - Raw microtransit calculation endpoints
routes/calendars.py            - Calendar generation and retrieval
routes/downloads.py            - CSV/JSON download endpoints
helpers/dashboard.py           - Core dashboard generation logic
helpers/utils.py               - JSON serialization, normalization utilities
core/combined_calendar.py      - Combined calendar analyzer (merges all engines)
core/magi_collective.py        - PTI/Magi astrology engine
core/vedic_collective.py       - Vedic astrology engine
core/personal_transit.py       - Personal transit calculator
filters/bird_batch_filter.py   - Bird batch timing filter
filters/astro_batch_detector.py - AstroBatch detector
microtransits/yp.py            - Yogi Point transit calculator
microtransits/wb1.py           - Part of Fortune transit calculator
microtransits/wb2.py, wb3.py   - Western bridge calculators
microtransits/vb1.py, vb2.py   - Vedic bridge calculators
templates/                     - Jinja2 templates (pastel UI)
```

## Database Models
- **Profile** - user birth data and preferences
- **CalendarData** - generated calendar data (JSON) per user/client
- **Client** - agency clients with birth data, location, calendar status
- **Settings** - brand settings (company name, hashtag, shop URL)
- **SubscriptionToken** - ICS feed authentication tokens

## Key API Endpoints

### Calendar Generation
- `POST /api/generate-dashboard` - generate full calendar suite
- `GET /get-saved-calendar` - retrieve saved calendar data

### Power Days (Background-Filtered Pipeline)
- `GET /api/power-days` - classified power days (OMNI, Double GO, Good)
- `POST /api/power-days/generate` - regenerate + return power days
- `GET /api/power-days/bird-batch` - bird batch periods on background days only
- `GET /api/power-days/yogi-point` - Yogi Point transits on background days only
- `GET /api/power-days/part-of-fortune` - Part of Fortune transits on background days only

### PTI Calendar
- `GET /api/pti-calendar` - full PTI calendar with all classifications (PTI Best, PTI Go, Normal, PTI Slow, PTI Worst) with scores and details

### Publer Integration
- `GET /api/publer/test` - test Publer API connection
- `GET /api/publer/accounts` - list connected social accounts
- `POST /api/publer/push-microbird` - push Micro Bird events as scheduled drafts
- `POST /api/publer/push` - push generic events to Publer

### ICS Calendar Feeds
- `/calendar/bird_batch.ics` - all bird batch periods
- `/calendar/personal.ics` - personal transit calendar
- `/calendar/pti.ics` - PTI collective calendar
- `/calendar/vedic.ics` - Vedic collective calendar
- `/calendar/combined.ics` - combined classification calendar
- `/calendar/yogi_point.ics` - all Yogi Point transits
- `/calendar/nogo.ics` - NO GO (Rahu Kalam) periods
- `/calendar/bg_bird_batch.ics` - bird batch filtered to background days
- `/calendar/bg_yogi_point.ics` - Yogi Point filtered to background days
- `/calendar/bg_pof.ics` - Part of Fortune filtered to background days
- `/calendar/microbird.ics` - Micro Bird precision posting windows

### Client Management
- `GET /api/clients` - list clients for current admin
- `POST /api/clients` - create new client
- `PUT /api/clients/:id` - update client
- `DELETE /api/clients/:id` - delete client + calendar data
- `POST /api/clients/:id/generate` - generate all 5 calendars for client
- `GET /api/clients/:id/calendar` - retrieve client's calendar results

### Profile & Settings
- `GET/POST /api/profile` - user profile management
- `GET/POST /api/settings` - brand settings

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
- Mild GO counts toward Double GO classification
- PTI Worst = hard exclusion from background

## Recent Changes (February 2026)
- Built full Power Days pipeline: classify → filter → overlap → export
- Added background-filtered endpoints: bird batch, Yogi Point, PoF on background days only
- Implemented Micro Bird: precision posting times where microtransits overlap bird windows
- Created background-filtered ICS feeds (bg_bird_batch, bg_yogi_point, bg_pof)
- Replaced microbird.ics stub with real overlap computation
- Built Publer integration: push Micro Bird events as scheduled draft posts
- Built agency multi-client system with CRUD, generation, and results viewing
- Created client results page with golden windows, bird periods, full calendar table
- Fixed timezone_offset parameter handling in client generation flow
- Redesigned all pages to match pastel UI design system
