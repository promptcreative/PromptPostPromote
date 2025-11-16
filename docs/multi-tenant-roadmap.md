# Multi-Tenant Agency Model - Implementation Roadmap

## Overview
Transform the Painting Content Planner into a white-label agency platform where multiple artists/clients can use the system independently with complete data isolation.

---

## Architecture Decision: Shared Database Multi-Tenancy

**Chosen Approach:** One application, one database, with `workspace_id` filtering on all queries.

**Why:**
- ✅ Centralized updates (push features to all clients instantly)
- ✅ Lower hosting costs (one Replit deployment)
- ✅ Easier client management dashboard
- ✅ Simpler billing/usage tracking

**Alternative (not chosen):** Separate Replit instances per client = harder to maintain, expensive to scale

---

## Phase 1: Simple Login Protection ✅ **COMPLETED**
**Goal:** Secure the app with basic authentication before showing Etsy

### What Was Built:
- ✅ Added Replit Auth blueprint (Python Flask version)
- ✅ Created PostgreSQL database (required by Replit Auth)
- ✅ Migrated existing SQLite data to PostgreSQL
- ✅ Added `@login_required` decorator to main route
- ✅ Integrated User and OAuth models for session management

**Result:** App now requires login with Google/GitHub/Email before access.

---

## Phase 2: User & Workspace Models (FOUNDATION)
**Goal:** Add database structure for multi-tenancy

### New Models:

```python
class User:
    id: str (primary key, from Replit Auth)
    email: str
    first_name: str
    last_name: str
    profile_image_url: str
    created_at: datetime
    # Already exists from Replit Auth blueprint ✓

class Workspace:
    id: int (primary key)
    name: str (e.g., "Prompt Creative", "Artist Jane Doe")
    created_at: datetime
    
    # Settings per workspace
    company_name: str
    branded_hashtag: str
    content_tone: str
    shop_url: str
    instagram_hashtag_count: int
    pinterest_hashtag_count: int
    
    # API credentials per workspace
    publer_api_key: str (encrypted)
    publer_workspace_id: str
    openai_api_key: str (encrypted)

class WorkspaceMember:
    id: int (primary key)
    workspace_id: int (foreign key)
    user_id: str (foreign key to User.id)
    role: str ('owner', 'admin', 'member')
    joined_at: datetime
```

### Database Changes:

**Add workspace_id to ALL existing tables:**
- Collection → workspace_id
- Image → workspace_id  
- Calendar → workspace_id
- CalendarEvent → workspace_id
- EventAssignment → workspace_id
- Settings → workspace_id (migrate to per-workspace)

### Tasks:
1. Create Workspace and WorkspaceMember models
2. Add workspace_id columns via migration (INT NOT NULL DEFAULT 1)
3. Create default workspace (ID=1) with existing Settings data
4. Assign all existing data to workspace_id = 1
5. Create workspace switching UI (dropdown in navbar)

**Estimated Time:** 2-3 hours  
**Outcome:** Database ready for multi-tenant queries

---

## Phase 3: Data Isolation (CRITICAL)
**Goal:** Ensure users only see their workspace's data

### Changes Required:

**Every query must filter by workspace:**
```python
# BEFORE:
images = Image.query.all()

# AFTER:
images = Image.query.filter_by(workspace_id=current_workspace_id).all()
```

### Routes to Update (41 total):
- `/images` (GET, POST)
- `/images/<id>` (GET, PUT, DELETE)
- `/collections` (GET, POST)
- `/collections/<id>` (GET, PUT, DELETE)
- `/calendars` (GET, POST, DELETE)
- `/schedule/*` (all 15 schedule endpoints)
- `/assign` (POST)
- All batch actions

### Helper Function:
```python
from flask_login import current_user

def get_current_workspace():
    """Get current user's active workspace from session"""
    workspace_id = session.get('active_workspace_id')
    if not workspace_id:
        # Get user's first workspace
        member = WorkspaceMember.query.filter_by(user_id=current_user.id).first()
        workspace_id = member.workspace_id if member else None
        session['active_workspace_id'] = workspace_id
    return workspace_id
```

### Tasks:
1. Create `get_current_workspace()` helper
2. Add workspace filter to ALL query routes (systematic review)
3. Update POST routes to auto-assign workspace_id
4. Add workspace validation on PUT/DELETE (prevent cross-workspace edits)
5. Test with 2+ test workspaces (create test users, verify isolation)

**Estimated Time:** 3-4 hours  
**Outcome:** Complete data isolation between workspaces

---

## Phase 4: Workspace Management UI
**Goal:** Let users create/switch workspaces

### New Pages:
1. **Workspace Dashboard** (`/workspaces`)
   - List all workspaces user belongs to
   - Create new workspace button
   - Switch active workspace
   
2. **Workspace Settings** (extend Settings tab)
   - Workspace name
   - Brand settings (moved from global Settings)
   - API keys (Publer, OpenAI)
   - Team members (invite/remove)

3. **Team Management** (`/workspace/team`)
   - Invite users by email
   - Assign roles (owner/admin/member)
   - Remove members

### Tasks:
1. Create workspace switcher dropdown (navbar)
2. Build workspace creation modal
3. Move Settings to be workspace-specific
4. Add team invitation system
5. Add role-based permissions

**Estimated Time:** 3-4 hours  
**Outcome:** Users can manage multiple workspaces

---

## Phase 5: File Storage Organization
**Goal:** Isolate uploaded artwork per workspace

### Current Structure:
```
static/uploads/artwork_abc123.png
```

### New Structure:
```
static/uploads/workspace_1/artwork_abc123.png
static/uploads/workspace_2/artwork_abc123.png
```

### Tasks:
1. Update upload handler to create workspace folders
2. Migrate existing files to workspace_1 folder
3. Update image URLs to include workspace path
4. Add cleanup job (delete workspace folder when workspace deleted)

**Estimated Time:** 1-2 hours  
**Outcome:** File isolation per workspace

---

## Phase 6: Migration & Testing
**Goal:** Safely transition existing data

### Migration Strategy:
1. Create "Prompt Creative" default workspace (ID=1)
2. Assign all existing data to workspace_id = 1
3. Create test workspace for validation
4. Upload test images, assign to test workspace
5. Verify no data leakage between workspaces

### Critical Tests:
- [ ] User A cannot see User B's images
- [ ] User A cannot edit User B's collections
- [ ] User A cannot assign User B's calendar events
- [ ] Switching workspaces updates all UI correctly
- [ ] File uploads go to correct workspace folder
- [ ] Publer API uses correct workspace credentials

**Estimated Time:** 2 hours  
**Outcome:** Confidence in data isolation

---

## Phase 7: Agency Features (OPTIONAL)
**Goal:** Add features for managing multiple clients

### Admin Dashboard:
- View all workspaces
- Usage statistics (images uploaded, AI generations, Publer posts)
- Billing metrics (if monetizing)

### White-Label Branding:
- Custom logo per workspace
- Custom color scheme
- Remove "Powered by Prompt Creative" footer

### Usage Limits:
- Max images per workspace
- Max AI generations per month
- Throttle API calls

**Estimated Time:** 4-6 hours  
**Outcome:** Full agency platform

---

## Total Estimated Time
- **Phase 1 (Immediate):** ✅ DONE (30-45 min)
- **Phase 2-6 (Core Multi-Tenant):** 11-15 hours
- **Phase 7 (Agency Features):** 4-6 hours

**Grand Total:** ~15-21 hours for complete multi-tenant system

---

## Risks & Mitigation

### Risk 1: Missing Workspace Filter
**Impact:** Data leakage between users  
**Mitigation:** Systematic code review, automated tests, QA with 2+ workspaces

### Risk 2: PostgreSQL Migration Issues
**Impact:** Data loss during SQLite → PostgreSQL switch  
**Mitigation:** Backup database first, test migration on copy, validate all data

### Risk 3: Complexity Creep
**Impact:** Endless features delay launch  
**Mitigation:** Ship Phase 1-6 first, add Phase 7 based on demand

---

## Launch Checklist
- [x] Phase 1: Login working
- [ ] Phase 2: Workspace models created
- [ ] Phase 3: All queries filtered by workspace
- [ ] Phase 4: Workspace UI built
- [ ] Phase 5: File storage isolated
- [ ] Phase 6: Migration complete, tests pass
- [ ] Security audit (ensure no data leaks)
- [ ] Performance testing (10+ workspaces)
- [ ] Deploy to Replit production
- [ ] Onboard first client!

---

## Future Enhancements
- Stripe integration for billing
- Workspace templates (clone settings to new client)
- Advanced analytics per workspace
- API access for headless usage
- Mobile app (React Native)

---

## Current Status (November 16, 2025)
✅ **Phase 1 Complete:** Login protection active, app secured with Replit Auth
📋 **Next Steps:** Implement Phase 2 (User & Workspace models) when ready for multi-tenancy
