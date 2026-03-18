# INTERNAL_DOCS — PromptPostPromote / Astrobatching

*Last updated: March 2026*

---

## 1. Directory Map

### Root
```
rebuild/                       — All application code lives here
RepoDepot/                     — Project documentation and reference materials
  assets/                      — Images, diagrams, and other reference files
  CONTEXT.md                   — High-level project context and status
  INTERNAL_DOCS.md             — This file (developer reference)
  HOW_TO_USE.md                — Full user-facing how-to guide
publer_service.py              — Publer API wrapper class (used by rebuild/routes/publer.py)
replit.md                      — Architecture reference and full API endpoint index
```

### rebuild/ (the app)
```
app.py                         — Entry point. Flask app setup, DB config, blueprint registration.

database/
  models.py                    — SQLAlchemy models:
                                   UserProfile (email, birth data, role, is_admin)
                                   CalendarData (generated calendar JSON per user_id)
                                   Client (agency clients with birth data and calendar status)
                                   Settings (brand settings)
                                   SubscriptionToken (ICS feed auth tokens, permanent)
                                   ManualCalendarEntry (admin/editor-entered calendar classifications)
  manager.py                   — Database manager: get/save CalendarData, get/create SubscriptionTokens,
                                   get/save manual calendar entries

routes/
  auth.py                      — Login/logout, email-based auth, role detection (admin/editor/client/user),
                                   profile save/get, admin team management (/api/admin/set-role, /api/admin/editors)
  pages.py                     — Page routes: landing, dashboards, calendar feeds, power days, client portal
  clients.py                   — Client CRUD API + calendar generation/retrieval (admin-only)
                                   Includes /api/clients/{id}/ics-feeds, /api/clients/{id}/microtransits
  power_days.py                — Power Days API: classified days, bird batch on background, Yogi Point,
                                   Part of Fortune, ICS feed URL generation (/api/calendar-feeds)
  publer.py                    — Publer integration: test connection, list accounts, push microbird/generic
  ics_feeds.py                 — All ICS calendar subscription feeds (10+ types, background-filtered variants)
  api.py                       — Profile and calendar generation APIs
  manual_calendar.py           — Manual calendar entry API (POST/GET /api/manual-calendar)
  microtransits.py             — Raw microtransit calculation endpoints
  calendars.py                 — Calendar generation and retrieval
  downloads.py                 — CSV/JSON download endpoints

helpers/
  dashboard.py                 — Core dashboard generation (runs all 5 engines via generate_dashboard_core())
  utils.py                     — get_effective_user_id(), JSON serialization, normalization, date range utilities

core/
  combined_calendar.py         — Combined calendar analyzer (merges engine results, applies OMNI/Double GO/Good)
  magi_collective.py           — PTI/Magi astrology engine
  vedic_collective.py          — Vedic astrology engine
  personal_transit.py          — Personal transit calculator
  panch_pakshi/                — Panch Pakshi (Bird Batch / Five Birds) calculation package

filters/
  bird_batch_filter.py         — Bird batch timing filter (uses PanchPakshiCalculator)
  astro_batch_detector.py      — AstroBatch detector

microtransits/
  yp.py                        — Yogi Point transit calculator (process_transits())
  wb1.py                       — Part of Fortune transit calculator
  wb2.py, wb3.py               — Western bridge calculators
  vb1.py, vb2.py               — Vedic bridge calculators

templates/                     — Jinja2 HTML templates (pastel UI — DM Sans, #FFF8F0 bg, #2D2B3D text)
  landing_page.html            — Public landing page
  login.html                   — Sign in / sign up (tabbed, email-only)
  account_dashboard.html       — Regular user + admin dashboard (shows generate card if no data)
  client_dashboard.html        — Client portal dashboard (read-only)
  power_days.html              — Power Days view (golden windows, bird batch, microtransits, Micro Bird)
  calendar_feeds.html          — ICS subscription feed links (dynamically loads authenticated URLs)
  clients.html                 — Admin client management page
  client_results.html          — Admin view of a client's full pipeline results
  profile_setup.html           — Birth data entry form
  manual_calendar.html         — Editor/admin manual calendar input
  calendar_view.html           — Full calendar view (My Calendars)
  interactive_calendar.html    — Interactive calendar display
  multi_calendar_view.html     — Multi-calendar comparison view
  calendar_form.html           — Calendar generation form

static/
  icon.png                     — Favicon (four overlapping pastel circles)
```

### Entry Points
- **Application start:** `rebuild/app.py`
- **All page routes:** `rebuild/routes/pages.py`
- **Auth flow:** `rebuild/routes/auth.py`

### Configuration
- **App config:** `rebuild/app.py` (DB URL, secret key, debug mode)
- **Environment variables:** Set in Replit Secrets, referenced via `os.environ`

---

## 2. Role System

| Role | How Detected | Access |
|------|-------------|--------|
| `admin` | `UserProfile.is_admin=True` OR email == `ADMIN_EMAIL` env var | Full access — all pages, client management, team management |
| `editor` | `UserProfile.role='editor'` | Calendar Input page only + own Power Days/feeds |
| `client` | Login email matches a `Client.email` record | Client portal (`/client-dashboard`) — read-only |
| `user` | Default (no special flags) | Dashboard, Power Days, Calendar Feeds, Profile |

**Role detection happens at login** in `auth.py`. Session stores `role`, `client_id` (for clients), and `is_admin`.

**`get_effective_user_id()`** in `helpers/utils.py` is the single source of truth for resolving a user's data key:
- Clients → `client_{client_id}` (matches CalendarData saved during admin generation)
- All others → email address

---

## 3. Database Models

### UserProfile
Stores birth data and role for regular users and editors.
```
email (unique, PK-like), is_admin (bool), role (varchar 'user'/'editor'),
birth_date, birth_time, birth_latitude, birth_longitude, birth_timezone,
birth_location_name, current_latitude, current_longitude, current_location_name,
calendar_range_days
```
**Note:** The `role` column was added via ALTER TABLE in March 2026. If setting up fresh, `db.create_all()` handles it. If migrating an old DB, run:
```sql
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';
```

### CalendarData
Stores generated calendar JSON, keyed by `user_email` (which is `client_{id}` for agency clients).
```
user_email, calendar_type, data (JSON), date_range_start, date_range_end
```

### Client
Agency clients managed by admin.
```
owner_email, name, email, birth_date, birth_time, birth_latitude, birth_longitude,
birth_timezone, birth_location_name, current_latitude, current_longitude,
current_location_name, calendar_range_days, last_generated_at, calendar_status
```

### SubscriptionToken
ICS feed authentication. One row per (user_email, calendar_type). Created once, never rotated.
```
user_email, calendar_type, token (32-char hex)
```
Use `SubscriptionToken.get_or_create(user_id, calendar_type)` — always returns the same token for a given user+type.

### ManualCalendarEntry
Admin/editor-entered calendar data that overrides engine calculations.
```
date, calendar_type ('magi'/'vedic'), category, classification, notes
```

---

## 4. Dependencies & Integrations

### External Services
| Service | Purpose | How Connected |
|---|---|---|
| **PostgreSQL (Neon)** | All persistent data | `DATABASE_URL` env var, SQLAlchemy ORM |
| **Publer API** | Push Micro Bird events as social media drafts | `PUBLER_API_KEY` + `PUBLER_WORKSPACE_ID`, REST API via `publer_service.py` |
| **Swiss Ephemeris** | Planetary position calculations | `pyswisseph` library, no API key needed |

### Environment Variables
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `ADMIN_EMAIL` | Email address that gets admin role at login |
| `PUBLER_API_KEY` | Publer API authentication |
| `PUBLER_WORKSPACE_ID` | Publer workspace target |
| `SESSION_SECRET` | Flask session cookie signing |

### Not Used (Legacy References)
- **OpenAI API** — Was in original concept, not in current codebase
- **Flask-Dance / Flask-Login** — Not used; auth is raw Flask sessions with email only

---

## 5. Secrets & Sensitive Data

### Where Credentials Are Referenced
- `rebuild/app.py` — `DATABASE_URL`, `SESSION_SECRET`
- `rebuild/routes/auth.py` — `ADMIN_EMAIL`
- `publer_service.py` — `PUBLER_API_KEY`, `PUBLER_WORKSPACE_ID`

### Never Share Publicly
- Any environment variable values
- Database connection string (contains credentials)
- Publer API key / Session secret
- Data from `user_profiles` or `clients` tables (birth data is PII)

### Safe for Team Members
- All source code and templates
- Classification rules and pipeline logic
- ICS feed structure and endpoint documentation

---

## 6. ICS Feed System

### How Tokens Work
Each user+calendar_type pair gets one permanent token via `SubscriptionToken.get_or_create()`. Tokens are never rotated. ICS subscription URLs include `?user_id=...&token=...` and are safe to share publicly (they only serve calendar data for that specific user/type).

### Main vs Background-Filtered Feeds
| Feed Type | Filters to Background Days? |
|---|---|
| `/calendar/bird_batch.ics` | No — shows all bird periods every day |
| `/calendar/yogi_point.ics` | No — shows all YP transits |
| `/calendar/bg_bird_batch.ics` | Yes — OMNI/Double GO/Good days only |
| `/calendar/bg_yogi_point.ics` | Yes — background days only |
| `/calendar/bg_pof.ics` | Yes — background days only |
| `/calendar/microbird.ics` | Yes — Micro Bird precision windows |
| `/calendar/nogo.ics` | No filter (Rahu Kalam every day) |

### Calendar Feeds Page
`/calendar-feeds` loads authenticated URLs for the 6 dynamically-served feeds (Bird, MicroBird, Enhanced PoF, Yogi Point, NO GO, All Microtransits) via `GET /api/calendar-feeds` on page load. The server-rendered feeds (PTI, Vedic, Personal Nakshatra) are injected at render time via Jinja2.

---

## 7. Common Tasks

### Run Locally
```bash
cd rebuild && python app.py
```
Server starts on port 5000. Requires `DATABASE_URL` set.

### Deploy / Update
- Hosted on Replit — deploy via Replit's Deploy button
- Production uses `gunicorn` as WSGI server
- Schema changes: `db.create_all()` runs on startup (additive only — doesn't drop columns). For new columns on existing tables, run ALTER TABLE manually via psycopg2 or psql.

### Add a New Page
1. Add route in `rebuild/routes/pages.py`
2. Create template in `rebuild/templates/`
3. Design system: DM Sans, `#FFF8F0` background, `#2D2B3D` text, `border-radius: 12–20px`, soft pastel accents
4. Add `<link rel="icon" type="image/png" href="/static/icon.png">` in `<head>`
5. Add role guard at top: check `session.get('authenticated')`, redirect to `/login` if not

### Add a New API Endpoint
1. Add to appropriate blueprint in `rebuild/routes/`
2. Use `get_effective_user_id()` from `helpers/utils.py` for data isolation
3. Check `session.get('authenticated')` for auth
4. For admin-only: check `session.get('user_info', {}).get('is_admin')`
5. For client-blocking: check `session.get('user_info', {}).get('role') != 'client'`

### Add a New ICS Feed
1. Add route in `rebuild/routes/ics_feeds.py`
2. Use `_verify_subscription(calendar_type)` to authenticate (requires `user_id` + `token` params)
3. Read saved data via `_get_saved_calendar_section(user_id, section_key)`
4. Build events list and return `create_ics_response(name, events)`
5. Add the `calendar_type` to `db_manager.get_user_subscriptions()` in `manager.py` if it should appear in the feeds list

### Add a New Database Column
1. Add to the model in `rebuild/database/models.py`
2. `db.create_all()` only creates new tables — it won't add columns to existing tables
3. Run manually: `ALTER TABLE tablename ADD COLUMN IF NOT EXISTS colname type DEFAULT val;`

---

## 8. Known Issues & Tech Debt

### Current Known Issues
- **Microtransits not cached** — Yogi Point and Part of Fortune are recalculated from scratch on every Power Days page load (~1-2 min each time). Results are not stored in the database. Should be cached in CalendarData on first calculation.
- **No post-merge setup script** — The `.replit` file has no post-merge script configured; task agent merges will show a warning. Add a `post_merge_setup.sh` via the post_merge_setup skill if task agents are used.

### Tech Debt
- **Duplicate date-parsing helpers** — `_extract_date_part()` is copy-pasted across `power_days.py` and `publer.py`; should live in `helpers/utils.py`
- **`publer_service.py` location** — Sits in root directory; should be moved into `rebuild/`
- **No structured logging** — Everything uses `print()` and `traceback.print_exc()`; should use Python `logging` module
- **No test suite** — Zero automated tests; classification logic, role detection, and data isolation are the highest priority test targets
- **Static event counts on Calendar Feeds page** — The stats text ("360 events per two months") is hardcoded, not calculated from actual data

### Planned Features (Not Yet Built)
- **Brand Kit** — Upload and store client brand assets (logo, colors, hashtags) — placeholder card exists on client dashboard
- **Calendar auto-refresh** — Automatically regenerate stale calendars instead of requiring manual trigger
- **Client onboarding email** — Notify client by email when admin generates their calendar for the first time
- **Standalone API docs** — Formal API documentation beyond the endpoint index in `replit.md`

---

## 9. Classification Rules Reference

| Term | Logic |
|------|-------|
| **OMNI** | PTI Best/Go AND Vedic GO/Mild GO/Build AND Personal power/supportive |
| **Double GO** | PTI Best/Go AND Vedic GO/Mild GO/Build (Personal irrelevant) |
| **Good** | 2 of 3 systems positive — PTI Worst never qualifies |
| **PTI Worst** | Hard exclusion — removes day from ALL background calculations |
| **Mild GO** | Counts as GO for classification (treated same as GO) |
| **Background day** | Any day classified OMNI, Double GO, or Good |
| **Micro Bird** | Time window where a microtransit (YP or PoF) overlaps a Bird Batch period on a background day |

---

## 10. Error Handling Patterns

### DB Transaction Errors
If you see `InFailedSqlTransaction` cascades (from long-running async operations leaving the session in a bad state):
- Add `db.session.rollback()` in exception handlers — already done in `database/manager.py`
- The login handler does NOT rollback proactively (removed as unnecessary once the `role` column issue was resolved)

### ICS Feed Auth Errors
If an ICS URL returns 400 "user_id query parameter required" — the URL is missing auth params. Always use the URLs from `db_manager.get_user_subscriptions()` or `SubscriptionToken.get_or_create()` — never construct ICS URLs manually without tokens.
