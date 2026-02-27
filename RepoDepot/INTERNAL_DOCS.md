# INTERNAL_DOCS — PromptPostPromote / Astrobatching

## 1. Directory Map

### Root
```
rebuild/                       — All application code lives here
RepoDepot/                     — Project documentation and reference materials
  assets/                      — Images, diagrams, and other reference files
publer_service.py              — Publer API wrapper class (used by rebuild/routes/publer.py)
replit.md                      — Project documentation and architecture reference
```

### rebuild/ (the app)
```
app.py                         — Entry point. Flask app setup, DB config, blueprint registration.

database/
  models.py                    — SQLAlchemy models: UserProfile, CalendarData, Client, Settings, SubscriptionToken
  manager.py                   — Database manager class for calendar data CRUD and subscription tokens

routes/
  auth.py                      — Login/logout, email-based auth, role detection (admin/client/user), profile setup
  pages.py                     — Page routes: landing, dashboards, calendar feeds, power days, client portal
  clients.py                   — Client CRUD API + calendar generation/retrieval (admin-only)
  power_days.py                — Power Days API: classified days, bird batch, Yogi Point, Part of Fortune, Micro Bird
  publer.py                    — Publer integration: test connection, list accounts, push microbird/generic events
  ics_feeds.py                 — ICS calendar subscription feeds (all types + background-filtered)
  api.py                       — Profile and calendar generation APIs
  microtransits.py             — Raw microtransit calculation endpoints
  calendars.py                 — Calendar generation and retrieval
  downloads.py                 — CSV/JSON download endpoints

helpers/
  dashboard.py                 — Core dashboard generation logic (runs all 5 engines)
  utils.py                     — get_effective_user_id(), JSON serialization, normalization, date range utilities

core/
  combined_calendar.py         — Combined calendar analyzer (merges all engine results, applies classification)
  magi_collective.py           — PTI/Magi astrology engine
  vedic_collective.py          — Vedic astrology engine
  personal_transit.py          — Personal transit calculator
  panch_pakshi/                — Panch Pakshi (Bird Batch) calculation package

filters/
  bird_batch_filter.py         — Bird batch timing filter
  astro_batch_detector.py      — AstroBatch detector

microtransits/
  yp.py                        — Yogi Point transit calculator
  wb1.py                       — Part of Fortune transit calculator
  wb2.py, wb3.py               — Western bridge calculators
  vb1.py, vb2.py               — Vedic bridge calculators

templates/                     — Jinja2 HTML templates (pastel UI)
  landing_page.html            — Public landing page
  login.html                   — Sign in / sign up (tabbed)
  account_dashboard.html       — Regular user + admin dashboard
  client_dashboard.html        — Client portal dashboard
  power_days.html              — Power Days view (golden windows, microtransits)
  calendar_feeds.html          — ICS subscription feed links
  clients.html                 — Admin client management page
  client_results.html          — Admin view of a client's results
  profile_setup.html           — Birth data entry form
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

## 2. Dependencies & Integrations

### External Services
| Service | Purpose | How Connected |
|---|---|---|
| **PostgreSQL (Neon)** | All persistent data | `DATABASE_URL` env var, SQLAlchemy ORM |
| **Publer API** | Push Micro Bird events as social media drafts | `PUBLER_API_KEY` + `PUBLER_WORKSPACE_ID`, REST API via `publer_service.py` |
| **Swiss Ephemeris** | Planetary position calculations | `pyswisseph` library, no API key needed |

### Environment Variables Needed
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `ADMIN_EMAIL` | Email address that gets admin role |
| `PUBLER_API_KEY` | Publer API authentication |
| `PUBLER_WORKSPACE_ID` | Publer workspace target |
| `SESSION_SECRET` | Flask session cookie signing |

### Not Used (Legacy References)
- **OpenAI API** — Was in original concept, not used in current codebase
- **Flask-Dance** — Not used; auth is email-based without OAuth
- **Flask-Login** — Not used; auth uses raw Flask sessions

---

## 3. Secrets & Sensitive Data

### Where Credentials Are Referenced
- `rebuild/app.py` — `DATABASE_URL`, `SESSION_SECRET`
- `rebuild/routes/auth.py` — `ADMIN_EMAIL`
- `publer_service.py` — `PUBLER_API_KEY`, `PUBLER_WORKSPACE_ID`

### Never Share Publicly
- Any environment variable values
- Database connection string (contains credentials)
- Publer API key
- Session secret
- Any data from the `user_profiles` or `clients` tables (birth data is PII)

### Safe for Team Members to See
- All source code
- Template files
- The classification rules and pipeline logic
- ICS feed structure
- API endpoint documentation in `replit.md`

---

## 4. Common Tasks

### Run Locally
```bash
cd rebuild && python app.py
```
Server starts on port 5000. Requires `DATABASE_URL` to be set.

### Deploy / Update
- Hosted on Replit — deploy via Replit's "Deploy" button
- Production uses `gunicorn` as the WSGI server
- Database migrations are automatic (`db.create_all()` in `app.py`)

### Where Logs / Errors Show Up
- **Development:** Flask debug console (workflow logs in Replit)
- **Production:** Replit deployment logs
- **Browser:** JS console for frontend errors
- No structured logging — errors print to stdout/stderr via `traceback.print_exc()`

### How to Add a New Feature

**New page:**
1. Add route in `rebuild/routes/pages.py`
2. Create template in `rebuild/templates/`
3. Follow pastel design system (DM Sans, #FFF8F0 background, #2D2B3D text)
4. Add favicon link: `<link rel="icon" type="image/png" href="/static/icon.png">`

**New API endpoint:**
1. Add to the appropriate blueprint in `rebuild/routes/`
2. Use `get_effective_user_id()` from `helpers/utils.py` for user identification
3. Check `session.get('authenticated')` for auth
4. For admin-only routes, check `session.get('user_info', {}).get('is_admin')`

**New astrology engine:**
1. Add calculator module in `rebuild/core/`
2. Wire it into `helpers/dashboard.py` `generate_dashboard_core()`
3. Add ICS feed endpoint in `routes/ics_feeds.py` if needed

**New database model:**
1. Define in `rebuild/database/models.py`
2. `db.create_all()` runs on startup — no manual migrations needed

---

## 5. Help Needed

### Tasks That Could Be Delegated Now
- **Mobile responsiveness testing** — Go through each template on phone-size screens, note layout issues
- **Brand Kit UI** — Build the upload form and storage for client brand assets (placeholder card exists in client dashboard)
- **Calendar auto-refresh** — Add logic to regenerate expired calendars automatically instead of showing stale data
- **Client onboarding email** — Send an email when admin generates a client's calendars to tell them they can log in

### Areas That Need Cleanup
- **Duplicate date-parsing helpers** — `_extract_date_part()` is copy-pasted across `power_days.py` and `publer.py`; should be in `helpers/utils.py`
- **Publer service location** — `publer_service.py` sits in the root directory; should move into `rebuild/`
- **No structured logging** — Everything uses `print()` and `traceback.print_exc()`; should use Python `logging` module
- **No test suite** — Zero automated tests; critical paths (classification logic, role detection, data isolation) should have tests

### Documentation Gaps
- No standalone API documentation beyond what is in `replit.md`
- Classification rules (OMNI/Double GO/Good) are encoded in `power_days.py` logic but not documented as a standalone reference
- No onboarding guide for new clients (how to log in, what they will see)
- No runbook for common issues (stale calendars, Publer connection failures)
