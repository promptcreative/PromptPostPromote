# User Guide - Painting Content Planner

**For:** Artists & Content Managers  
**Purpose:** AI-powered social media scheduling for artwork promotion

---

## Quick Start Checklist

### Before You Begin

**⚠️ SECURITY WARNING:** Default login is `admin/123` for demo purposes only. Change credentials via environment variables (`ADMIN_USERNAME` and `ADMIN_PASSWORD`) before production use.

**Platform Setup (One-Time):**
1. ✅ **Instagram:** Link your Instagram account to a Facebook Business account (required for automation)
2. ✅ **Pinterest:** Create an "Original Art" board in your Pinterest account (app auto-detects this board)
3. ✅ **Publer:** Connect Instagram, Pinterest, and Facebook accounts in Publer dashboard
4. ✅ **API Keys:** Add `OPENAI_API_KEY` and `PUBLER_API_KEY` to environment variables

---

## Settings Configuration

Navigate to **Settings** tab (⚙️ icon) to configure your brand:

- **Company Name:** Your business name (auto-mentioned in AI-generated content)
- **Branded Hashtag:** Your signature hashtag (auto-appended to posts)
- **Instagram Hashtags:** Set limit (3-15 hashtags)
- **Pinterest Hashtags:** Set limit (2-10 hashtags)
- **Content Tone:** Choose writing style
  - 🎨 **Poetic** - Artistic, emotional storytelling
  - ⚖️ **Balanced** - Mix of art & sales
  - 💰 **Direct Sales** - Product-focused, clear CTAs
- **Shop URL:** Your Etsy or website link

**💡 Tip:** Configure settings ONCE, all future AI content matches your brand voice!

---

## Main Workflow

### 1️⃣ Upload Artwork

**Content Tab → Upload Images**

1. Create a **Collection** first (e.g., "Part of Fortune Conjunct Natal Moon")
2. Upload images → Select collection from dropdown
3. **Display Name Logic:**
   - With collection: Uses collection name (e.g., "Part of Fortune Conjunct Natal Moon")
   - Without collection: Uses cleaned filename (e.g., "Sunset Landscape" from `sunset_landscape.jpg`)

---

### 2️⃣ Generate AI Content

**Content Tab → Select Image → Generate with Vision AI**

AI creates platform-specific content:
- 📸 **Instagram:** Caption + hashtags (separate from description)
- 📌 **Pinterest:** Description + hashtags (different from Instagram!)
- 🛍️ **Etsy:** SEO title, description, tags
- 🌐 **General:** Alt text, SEO fields

**Review & Edit:**
- Click "Edit & Review" to modify AI-generated content
- Approve when satisfied → Status changes to "Ready"

---

### 3️⃣ Import Astrology Calendars

**Calendars Tab → Upload .ics File**

**Supported Calendars:**
- 🔮 **Antibaion (AB)** - Strategic timing
- 🧘 **Yogi Point (YP)** - Spiritual alignment
- 💰 **Part of Fortune (POF)** - Prosperity windows

**How It Works:**
- App calculates **midpoint time** between event start/end
- This is the optimal posting time based on astrology
- Calendar badges show source (🔮 AB / 🧘 YP / 💰 POF)

**Example:**
- Event: 10:00 AM - 2:00 PM
- **Optimal Post Time:** 12:00 PM (midpoint)

---

### 4️⃣ Schedule Content

**Schedule Grid Tab**

**Manual Assignment:**
1. Click a calendar time slot
2. Select artwork from dropdown
3. Choose platforms: Instagram, Pinterest, Facebook (checkboxes)
4. Click "Assign to Slot"

**Batch Assignment:**
1. Click "Fill All Days" dropdown
2. **Strategy Options:**
   - **Astrology Only:** Uses AB/YP/POF events exclusively
   - **Fill All:** Uses astrology events + fills gaps with default times (10am, 2pm, etc.)

**Multi-Platform Support:**
- One artwork can be scheduled to 3 platforms simultaneously
- Each platform gets a separate post with correct hashtags

---

### 5️⃣ Push to Publer

**Schedule Grid Tab → Export dropdown → Push to Publer**

1. Select time slots (checkbox individual events or whole days)
2. Click "Push to Publer"
3. App saves **post IDs** for tracking
4. Posts appear in Publer dashboard ready to publish

**Platform Notes:**
- **Instagram:** Requires Facebook Business account link
- **Pinterest:** Posts to "Original Art" board automatically
- **Facebook:** Uses your connected Facebook Page

---

### 6️⃣ Mark as Sold (Auto-Delete)

**Content Tab → Collections → Update Status**

When artwork sells:
1. Find collection in list
2. Change status to **Pending** or **Shipped**
3. App **automatically deletes ALL Publer posts** for that artwork

**💡 Never promote sold artwork!** System prevents double-selling.

---

## Export Options

### Publer CSV Export
**Schedule Grid → Export → Publer CSV**
- Select time slots with checkboxes
- Downloads CSV for manual Publer import
- Includes media URLs (Publer auto-fetches images)

### FeedHive CSV Export
**Schedule Grid → Export → FeedHive CSV**
- Alternative platform support
- 7-column format with labels and notes

### Scheduled Content Export
**Scheduled Tab → Export to Publer**
- Exports ALL scheduled assignments at once
- No need to select individual slots

---

## Scheduled Content Tab

View all assigned posts in chronological order:

- **Display:** Collection name + platform emoji
- **Actions:**
  - **Replace:** Swap to different artwork (keeps schedule)
  - **Delete:** Remove from schedule

**Example Display:**
```
Monday, November 18, 2025
  🔮 Part of Fortune Conjunct Natal Moon
  14:30 - 📸 Instagram POF
```

---

## Astrology Batching (Advanced)

**Calendar Workflow:**
1. Upload 3 calendars (AB, YP, POF) from external astrology system
2. App parses events and calculates midpoint times
3. Use "Fill All Days" to auto-assign content to optimal times

**Batching Strategy:**
- **Astrology Only:** Posts ONLY on AB/YP/POF event days
- **Fill All:** Posts on astrology days + fills gaps with regular times

**Visual Indicators:**
- 🔮 AB badge = Antibaion event
- 🧘 YP badge = Yogi Point event
- 💰 POF badge = Part of Fortune event
- No badge = Regular/default time slot

---

## Common Questions

### **Q: Why separate Instagram and Pinterest hashtags?**
A: Instagram and Pinterest have different hashtag strategies. The app prevents accidental overwriting by storing them separately.

### **Q: Can I edit AI-generated content?**
A: Yes! Click "Edit & Review" to modify any field before scheduling.

### **Q: What happens if I delete a scheduled image?**
A: The app warns you with assignment details and offers to remove from schedule first.

### **Q: Can I schedule the same artwork to multiple platforms?**
A: Yes! Use checkboxes in the assignment modal to select Instagram, Pinterest, and Facebook simultaneously.

### **Q: How do I update my brand voice?**
A: Go to Settings tab and change the "Content Tone" dropdown. All future AI generations use the new tone.

### **Q: What if I don't have astrology calendars?**
A: Use the "Fill All" strategy with regular times. The system works without astrology calendars.

---

## Pending Features (Coming Soon)

**Not Yet Active:**
- ⏳ **Smart Scheduler Auto-Assignment:** UI exists but AI slot optimization pending
- ⏳ **Video Upload:** Currently images only
- ⏳ **Video Mockups:** Image mockups only
- ⏳ **Weekly Planner View:** Day-by-day view only
- ⏳ **Etsy Automation:** Awaiting Etsy API approval for auto-sold detection

**Current Workarounds:**
- Manual assignment works perfectly
- Batch "Fill All Days" works for bulk scheduling
- Mark collections as Pending/Shipped manually to trigger auto-delete

---

## Troubleshooting

### **Instagram posts not automating**
→ Verify Instagram is linked to Facebook Business account (external requirement)

### **Pinterest posts failing**
→ Check "Original Art" board exists in your Pinterest account

### **Can't see uploaded images in scheduled view**
→ Re-upload images (old records may have broken file paths)

### **Deletion error when removing image**
→ Click "Remove from schedule" first, then delete image

### **AI content not generating**
→ Verify `OPENAI_API_KEY` environment variable is set

---

## Support & Resources

- **Technical Documentation:** `docs/technical-overview.md`
- **Multi-Tenant Roadmap:** `docs/multi-tenant-roadmap.md`
- **Publer API Notes:** `docs/publer-api-integration.md`

**Need Help?** Contact your system administrator or refer to technical docs.
