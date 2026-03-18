# Astrobatching / Prompt Post Promote — How To Use

## What This Platform Does

Astrobatching calculates your **best days and times to post content** using three astrological timing systems running simultaneously:

- **PTI (Magi/Collective)** — collective energy cycles affecting everyone
- **Vedic Collective** — traditional Vedic calendar (tithis, nakshatras)
- **Personal Transit** — your personalized chart transits based on birth data

These are layered to find **"golden windows"** — moments when all three systems agree it's a good time. Within those windows, **Bird Batch** and **Microtransit** filters narrow it down further to exact posting minutes.

---

## Roles

| Role | What They Can Do |
|------|-----------------|
| **Admin** | Full access — manage clients, generate calendars, all dashboards, team management, manual calendar input |
| **Editor** | Calendar Input page only (manual Magi/Vedic data entry), plus their own Power Days and calendar feeds |
| **Client** | Client portal — sees their Power Days, Calendar Feeds (read-only, no regeneration) |
| **User** | Regular dashboard, Power Days, Calendar Feeds, Profile |

The admin account is set via the `ADMIN_EMAIL` environment variable.

---

## Getting Started (New User / Regular User)

### 1. Sign In
Go to the login page and enter your email address. No password — just your email. If you're new, an account is created automatically.

### 2. Set Up Your Profile
You'll be redirected to **Profile Setup**. Fill in:
- **Birth date** — exact date
- **Birth time** — exact time (the more precise, the better)
- **Birth location** — the city/place you were born (sets the latitude/longitude)
- **Current location** — where you are now (affects Rahu Kalam / NO GO timing)

This data is used by the Personal Transit engine to personalize your calendar.

### 3. Generate Your Calendars
After saving your profile, you'll land on the **Account Dashboard**. You'll see a **"Generate my calendars"** button — click it. This runs all five engines:

1. PTI Collective
2. Vedic Collective
3. Personal Transit
4. Bird Batch Filter
5. Combined Calendar Analyzer

Generation takes **3–5 minutes** on first run. After that, results are saved in the database and load instantly on every return visit. You only need to regenerate if your birth data or location changes, or if you want fresh dates for the next period.

---

## The Power Days Pipeline

This is the core of the platform. Go to **Power Days** from the nav.

### Background Days (The Foundation)
Days are first classified into one of three categories that qualify as "background" (good for posting):

| Classification | What It Means |
|---------------|---------------|
| **OMNI** | All three systems aligned: PTI Best/Go + Vedic GO/Mild GO/Build + Personal power/supportive |
| **Double GO** | PTI Best/Go + Vedic GO/Mild GO/Build (Personal is ignored) |
| **Good** | At least 2 systems positive — never includes PTI Worst days |

**PTI Worst days are hard-excluded** — nothing on these days qualifies as a background day regardless of other factors.

These background days are your "green days" — only post on these.

### Bird Batch on Background Days
Within background days, **Bird Batch periods** give you specific time windows. Each period is classified by tier:

| Tier | Meaning |
|------|---------|
| **Double Boost** | Highest — both bird and sub-activity are in optimal phase |
| **Boost** | Strong — primary bird phase is favorable |
| **Build** | Moderate — good for planning/prep content |

Bird Batch is based on the Panch Pakshi (Five Birds) system — each day is divided into periods ruled by a specific bird (Vulture, Owl, Crow, Cock, Peacock) and each period has an activity state (Ruling, Eating, Walking, Sleeping, Dying). Double Boost = Ruling/Eating or Eating/Ruling combinations.

### Microtransit Layers
Two additional microtransit systems overlay the background days:

**Yogi Point (YP)** — Transits when the Moon aligns with your natal Yogi Point. Spiritually and materially auspicious moments tied to your birth chart.

**Part of Fortune (PoF)** — Combined transits from six calculation scripts (VB1, VB2, WB1, WB2, WB3 and YP). Fortune alignments based on your chart's Part of Fortune.

Both are calculated on-the-fly and filtered to background days only.

### Micro Bird — Precision Posting Times
**Micro Bird = where a microtransit window overlaps with a Bird Batch period on the same background day.**

This is the most actionable output. Each Micro Bird event gives you:
- Exact start and end time
- Which microtransit triggered it (YP or PoF)
- Which Bird Batch tier it falls within
- Duration of the overlap window

These are your **precision posting minutes** — the narrowest, highest-quality windows in the entire system.

---

## Calendar Feeds (ICS Subscriptions)

Go to **Calendar Feeds** from the nav. Here you can copy subscription URLs to paste into Google Calendar, Apple Calendar, or any ICS-compatible app.

### How Subscriptions Work
Each feed has a unique token tied to your account. The URL never changes — it's generated once and stored permanently. When you regenerate your calendars, the URL stays the same but the feed automatically serves new events. Calendar apps poll the URL periodically (Google: ~24 hours, Apple: ~5–30 minutes).

**You only need to share/subscribe once. It updates itself.**

### Available Feeds

**Monthly Calendars (pre-authenticated on the Calendars page):**
| Feed | What It Shows |
|------|--------------|
| PTI Calendar | Daily PTI classifications (Best, Go, Normal, Slow, Worst) |
| Personal Vedic Calendar | Daily Vedic energy ratings |
| Personal Nakshatra Calendar | Your Moon transit calendar with timed nakshatra events |

**Microtransit Calendars (load automatically with your token when logged in):**
| Feed | What It Shows |
|------|--------------|
| Bird Calendar | All Bird Batch periods — every tier, every day |
| MicroBird Calendar | Bird periods filtered to Ruling/Eating combinations only |
| Enhanced Part of Fortune | Combined PoF transits (VB1+VB2+WB3+YP deduplicated) |
| Yogi Point Only | Pure Yogi Point transits |
| NO GO (Rahu Kalam) | Daily inauspicious periods to avoid (based on your location) |
| All Microtransits | Every transit from all 6 scripts — no filtering |

**Background-filtered feeds (accessible from Power Days page):**
| Feed | What It Shows |
|------|--------------|
| Bird Batch (Background) | Bird periods filtered to background days only |
| Yogi Point (Background) | YP transits filtered to background days only |
| PoF (Background) | PoF transits filtered to background days only |
| Micro Bird | Precision posting windows (microtransit + bird overlap) |

### Subscribing in Google Calendar
1. Copy the URL from the Calendar Feeds page
2. Go to Google Calendar → Settings (gear) → Add Calendar → From URL
3. Paste the URL → Add Calendar
4. Events sync automatically going forward

### Subscribing in Apple Calendar
- **Mac:** File → New Calendar Subscription → Paste URL → Subscribe
- **iPhone/iPad:** Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar

---

## Publer Integration

From the **Power Days** page, you can push Micro Bird events directly to Publer as scheduled draft posts.

Setup requires `PUBLER_API_KEY` and `PUBLER_WORKSPACE_ID` in environment variables.

- **Push Micro Bird** — pushes all Micro Bird precision windows as drafts to your connected Publer workspace
- Each event becomes a scheduled draft post at the exact start time of the window

---

## Agency Workflow (Admin)

### Managing Clients
Go to **Clients** from the nav (admin only). Each client has:
- Name and email
- Birth data (date, time, birth location)
- Current location

### Generating Client Calendars
Select a client → click **Generate Calendars**. This runs all five engines for that client's birth data and saves results under their account. Status shows as: `pending → generating → ready`.

### Viewing Client Results
Once generated, click **View Results** on any client. The results page shows the full pipeline:
- Stats row (OMNI / Double GO / Good / Background day counts)
- Golden Windows (OMNI and Double GO cards by date)
- Micro Bird precision posting windows
- Bird Batch on background days
- Yogi Point and Part of Fortune layers
- ICS feed URLs for that client
- Full calendar table

### Client Portal
If a client logs in with their email (the same email stored on their Client record), they automatically land on the **Client Dashboard** — a read-only view of their Power Days and Calendar Feeds. They cannot regenerate, but they can subscribe to their feeds and see all their windows.

### Sharing ICS Feeds with Clients
On the client results page, there's a **Calendar Feeds (ICS)** section with copy buttons for all 10 feed types. These URLs include the client's unique token — just share these links with the client.

---

## Editor Role (Calendar Input)

Editors are team members who can enter manual Magi/PTI and Vedic calendar data. This overrides the calculated engines for specific months.

### Adding an Editor (Admin only)
Dashboard → Team section → Enter their email → Set role to Editor.

### Manual Calendar Input
Editors go to **Calendar Input** from the nav. Select:
- Calendar type: Magi/PTI or Vedic
- Month and year
- Category (e.g., SUCCESS_LOVE, MONEY, etc.)
- Enter day-by-day classifications

When manual data exists for a month/category, the dashboard pipeline uses it instead of running the calculation engine. This lets editors enter data from PTI Collective or Vedic Collective handbooks directly.

---

## Regenerating Calendars

- **Regular users:** Power Days page → "Regenerate Calendars" button (top right)
- **Admin (own calendars):** Same as regular users
- **Admin (client calendars):** Clients page → select client → Generate Calendars

Regeneration re-runs all five engines with the latest data and overwrites the saved results. Feed URLs stay the same and update automatically.

---

## Understanding the Classification Rules

| Rule | Logic |
|------|-------|
| OMNI | PTI Best/Go AND Vedic GO/Mild GO/Build AND Personal power/supportive |
| Double GO | PTI Best/Go AND Vedic GO/Mild GO/Build (Personal not required) |
| Good | 2 of 3 systems positive — PTI Worst never qualifies |
| PTI Worst | Hard exclusion — day is removed from all background calculations |
| Mild GO | Counts as GO for Double GO and OMNI classification purposes |

---

## Key URLs

| Page | URL | Who Can Access |
|------|-----|----------------|
| Dashboard | `/account-dashboard` | Admin, Editor, User |
| Client Portal | `/client-dashboard` | Client |
| Power Days | `/power-days` | All |
| Calendar Feeds | `/calendar-feeds` | All |
| Clients (Agency) | `/clients` | Admin only |
| Client Results | `/clients/{id}/results` | Admin only |
| Calendar Input | `/manual-calendar` | Admin, Editor |
| Profile Setup | `/profile-setup` | Admin, Editor, User |
| Login | `/login` | All |
