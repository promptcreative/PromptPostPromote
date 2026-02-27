# CONTEXT

**PROJECT NAME:** PromptPostPromote / Astrobatching

**GITHUB URL:** https://github.com/promptcreative/PromptPostPromote

**PURPOSE:** Astrobatch promotion calendar and agency tools that calculate personalized content posting times from birth data using multiple astrological calendar systems (Vedic, Magi/PTI, Personal Transit), find overlapping "golden windows" (OMNI, Double GO, Good classifications), filter microtransits to background days, compute Micro Bird precision posting times, and export via ICS calendar subscriptions and Publer API. Supports agency-style multi-client management with a client portal.

**CURRENT STATUS:** Functional. Core calculation engines, Power Days pipeline, background-filtered microtransits, Micro Bird precision timing, ICS calendar feeds, Publer integration, agency multi-client management, client portal with role-based auth (admin/client/user), and pastel UI design system are all operational. Brand Kit feature planned but not yet built.

**ARCHITECTURE:** Monolithic Python Flask application with blueprint-based route organization. PostgreSQL (Neon-hosted) for persistence. Separate modules for pages, API, clients, power days, publer, ICS feeds, microtransits, calendars, and downloads. Astrology engines in core/ and microtransits/ directories. Jinja2 templating with vanilla JS frontend. Session-based email auth with three-role system.

**TECH STACK:** Python 3.11, Flask, Flask-SQLAlchemy, PostgreSQL, SQLAlchemy, Requests, Pandas, pyswisseph, ephem, astral, pytz, icalendar, tabulate, gunicorn, psycopg2-binary

**USER FLOW:**
- **Regular user:** Signs up on landing page -> enters birth data on profile setup -> generates personal calendars -> views Power Days (OMNI/Double GO/Good) -> subscribes to ICS calendar feeds -> optionally pushes Micro Bird events to Publer.
- **Admin:** Logs in with admin email -> manages clients (CRUD) -> generates calendars per client -> views client results -> full access to all features.
- **Client:** Logs in with email matching a Client record -> lands on client portal dashboard -> views their Power Days, Calendar Feeds, and Publer integration (read-only, no regeneration).

**HOW TO RUN:** Application runs from the `rebuild/` directory. Set environment variables: `DATABASE_URL`, `ADMIN_EMAIL`, `PUBLER_API_KEY`, `PUBLER_WORKSPACE_ID`, `SESSION_SECRET`. Run with `cd rebuild && python app.py`.

**KEY FILES:**
- `rebuild/app.py` — Flask app setup, DB config, blueprint registration
- `rebuild/database/models.py` — SQLAlchemy models (UserProfile, CalendarData, Client, Settings, SubscriptionToken)
- `rebuild/database/manager.py` — Database manager for calendar data persistence
- `rebuild/routes/auth.py` — Email-based auth, role detection, profile management
- `rebuild/routes/pages.py` — Page routes (dashboards, clients, calendar feeds, power days)
- `rebuild/routes/clients.py` — Client CRUD + calendar generation/retrieval API (admin-only)
- `rebuild/routes/power_days.py` — Power Days API (classified days, filtered microtransits)
- `rebuild/routes/publer.py` — Publer integration (push microbird, push generic)
- `rebuild/routes/ics_feeds.py` — ICS calendar subscription feeds (all + background-filtered)
- `rebuild/helpers/utils.py` — Utilities including `get_effective_user_id()` for role-based data resolution
- `rebuild/helpers/dashboard.py` — Core dashboard generation logic
- `rebuild/core/` — Astrology engines (PTI/Magi, Vedic, Personal Transit, Combined Calendar)
- `rebuild/microtransits/` — Yogi Point, Part of Fortune, Western/Vedic bridge calculators
- `rebuild/templates/` — Jinja2 templates (landing, login, dashboards, power days, calendar feeds, client portal)

**DEPENDENCIES:**
- PostgreSQL (database) — User data, calendar data, client records, subscription tokens
- Publer API — Social media draft post creation from Micro Bird events
- Swiss Ephemeris (pyswisseph) — Planetary position calculations for all astrology engines

**BUSINESS SUMMARY:** Agency-style SaaS for content creators and social media managers who want astrologically-optimized posting schedules. Admin manages multiple clients, generates personalized calendars, clients access their own portal. Revenue model TBD.

**BUSINESS STATUS:** Pre-launch / Internal use
