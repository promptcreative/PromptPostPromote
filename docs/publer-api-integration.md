# Publer API Integration Documentation

**Last Updated:** November 11, 2025

## Current Status: CSV Export Method (Working)

We've successfully implemented a CSV export workflow that allows bulk scheduling to Publer without API complexity. This is the **recommended approach** going forward.

### What Works ✅
- **CSV Export from Schedule Grid**: Select specific time slots and export Publer-compatible CSV
- **Media URL Hosting**: Images are hosted on Replit and Publer pulls them automatically during CSV import
- **Bulk Scheduling**: Import entire schedule into Publer calendar in one action
- **12-Column Format**: Date, Text, Link, Media URLs, Title, Labels, Alt text, Comments, Pin Board, Subtype, CTA, Reminder
- **No API Complications**: No OAuth, no rate limits, no draft state issues

---

## API Attempts History

### What We Tried with Publer API

#### 1. Media Upload (✅ Working)
```python
POST https://api.publer.io/v1/media_upload
Headers:
  - Authorization: Bearer {PUBLER_API_KEY}
  - Content-Type: multipart/form-data
```

**Result:** Successfully uploads images and returns media IDs
- Tested with Free Dance collection artwork
- Media IDs returned correctly
- Files accessible in Publer media library

#### 2. Draft Creation (⚠️ Partially Working)
```python
POST https://api.publer.io/v1/posts
Body: {
  "text": "Post caption",
  "media_ids": ["media_id_from_upload"],
  "social_accounts": ["690d29b4f0c7ea9a5833a3bb"],  # Pinterest
  "draft_public": true  # or false
}
```

**Result:** Creates drafts but they appear in wrong location
- Drafts created successfully via API
- **Problem**: Drafts appear in "Draft Ideas" section instead of calendar
- Cannot schedule specific dates/times via API
- Tried both `draft_public: true` and `draft_public: false`

#### 3. Scheduled Post Creation (❌ Failed)
**Problem:** Publer API documentation doesn't clearly specify how to:
- Schedule posts to specific calendar dates/times programmatically
- Move drafts from "Draft Ideas" to calendar view
- Assign astrology time slots (AB/YP/POF events) to posts

**What We Found:**
- API creates posts in "Draft Ideas" by default
- No clear endpoint to schedule posts to calendar dates
- `draft` vs `draft_public` states unclear in documentation
- Calendar integration appears to be UI-only feature

---

## Current Working Solution: CSV Export

### Why CSV is Better
1. **Reliability**: Publer's CSV import is their core feature, well-documented and stable
2. **Review Before Publishing**: Can check entire schedule before importing
3. **Bulk Operations**: Import weeks/months of content at once
4. **No API Limits**: No rate limiting or quota concerns
5. **Media Hosting**: Our hosted images work perfectly via URLs
6. **Calendar Integration**: CSV import goes directly to Publer's calendar

### User Workflow
```
1. Upload artwork to Content tab
2. Assign to calendar time slots in Schedule Grid
3. Select specific slots with checkboxes
4. Click "Export Selected to CSV"
5. Import CSV to Publer → Content appears in calendar
```

---

## Future API Work (Awaiting Publer Support)

### What We Need from Publer
1. **Documentation** on scheduling posts to specific dates/times
2. **Clarification** on draft states and calendar integration
3. **Endpoint** for creating scheduled posts (not just drafts)
4. **Example code** showing full workflow: upload → schedule → publish

### When to Revisit API Integration
- If Publer provides clearer scheduling API documentation
- If we need real-time posting capabilities (not bulk scheduling)
- If CSV import becomes unreliable or limited
- If we want to pull analytics/metrics from Publer

### Potential Use Cases for API
- Real-time posting triggers
- Post performance analytics
- Automated content updates
- Integration with other platforms

---

## Technical Details

### Our Setup
- **Workspace ID**: `690d1b03a8e6a73f9973ffce`
- **Pinterest Account**: `690d29b4f0c7ea9a5833a3bb`
- **Instagram Account**: `690d1b4ebe32d2156db74a85`
- **API Key**: Stored in `PUBLER_API_KEY` environment variable

### Test Endpoints Implemented
- `/api/publer/test` - Test connection, list accounts, view drafts
- `/api/publer/push_days` - Attempted bulk scheduling (not used currently)

### Code Files
- `publer_service.py` - Publer API wrapper class
- `routes.py` - API test and push endpoints
- `static/js/main.js` - Test connection button handler

---

## Recommendations

1. **Keep using CSV export** - It works perfectly and is reliable
2. **Archive API code** - Keep `publer_service.py` for future reference
3. **Contact Publer support** - Ask about scheduling API capabilities
4. **Monitor CSV import** - Watch for any format changes or issues
5. **Consider API later** - Only if specific use case requires it

---

## Notes for Future Development

- The `/schedule/export_csv` endpoint is production-ready
- CSV format matches Publer's 12-column template exactly
- Media URLs use full paths (e.g., `https://your-app.replit.dev/static/uploads/artwork_xyz.png`)
- Placeholder content for empty slots helps maintain structure
- Events are sorted chronologically automatically

**Bottom Line:** CSV export gives us everything we need. API integration can wait until Publer provides better documentation or we have a specific real-time posting requirement.
