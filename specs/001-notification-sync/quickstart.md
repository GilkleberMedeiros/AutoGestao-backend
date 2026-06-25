# Quickstart: Validate Notification Synchronization

**Phase**: 1 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Purpose**: Runnable validation scenarios proving the feature works end-to-end

## Prerequisites

1. Backend running locally: `uv run manage.py runserver` (on `http://localhost:8000`)
2. Authenticated user account (or create one via signup endpoint)
3. Authorization token or session (for API requests)
4. Database with test notifications pre-created or generated in test setup

## Setup: Create Test Data

### Option A: Create Notifications via Django Admin (Manual)

1. Run migrations: `uv run manage.py migrate`
2. Create a superuser: `uv run manage.py createsuperuser`
3. Navigate to Admin: `http://localhost:8000/admin`
4. Login with superuser credentials
5. Create 5 Notification records:
   - 1: Title="Notification A", deliver_at=now, type=SIMPLE
   - 2: Title="Notification B", deliver_at=now+1h, type=ASSOCIATED
   - 3: Title="Notification C", deliver_at=now+2h, type=DEADLINE
   - etc.

### Option B: Create Notifications via Test Fixture (Automated)

```bash
# Create fixture in test/fixtures/notifications.json
# Then load:
uv run manage.py loaddata test/fixtures/notifications.json
```

### Option C: Create Notifications in Test Code (CI/CD)

See "Test Scenarios" section below for pytest/Django TestCase examples.

---

## Validation Scenario 1: Client Syncs with Known IDs

**Goal**: Verify endpoint filters out known notification IDs and returns only new ones.

### Setup

- User: `test_user@example.com` (password: `testpass123`)
- Existing notifications: 5 total (IDs: N1, N2, N3, N4, N5)
- Client already knows: N1, N3

### Request

```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "known_notification_ids": ["<N1-uuid>", "<N3-uuid>"]
  }'
```

### Expected Response

```json
{
  "notifications": [
    {
      "id": "<N5-uuid>",
      "title": "...",
      "deliver_at": "2026-06-25T14:50:00Z",
      ...
    },
    {
      "id": "<N4-uuid>",
      "title": "...",
      "deliver_at": "2026-06-25T14:40:00Z",
      ...
    },
    {
      "id": "<N2-uuid>",
      "title": "...",
      "deliver_at": "2026-06-25T14:30:00Z",
      ...
    }
  ]
}
```

### Validation Checks

- [ ] Response HTTP status is **200 OK**
- [ ] Response contains exactly **3 notifications** (N2, N4, N5; N1 and N3 excluded)
- [ ] Response order is **descending by `deliver_at`** (newest first: N5 → N4 → N2)
- [ ] No notification in response has ID in the request's `known_notification_ids`

---

## Validation Scenario 2: Client Syncs Without Known IDs (Bootstrap)

**Goal**: Verify endpoint returns all notifications when the client has no prior state.

### Setup

- User: `test_user@example.com`
- Existing notifications: 5 total

### Request

```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "known_notification_ids": []
  }'
```

### Expected Response

```json
{
  "notifications": [
    { "id": "<N5-uuid>", ... },
    { "id": "<N4-uuid>", ... },
    { "id": "<N3-uuid>", ... },
    { "id": "<N2-uuid>", ... },
    { "id": "<N1-uuid>", ... }
  ]
}
```

### Validation Checks

- [ ] Response HTTP status is **200 OK**
- [ ] Response contains **all 5 notifications**
- [ ] Response order is **descending by `deliver_at`**

---

## Validation Scenario 3: Notifications with Relations

**Goal**: Verify endpoint includes `NotificationRelation` data when applicable.

### Setup

- User: `test_user@example.com`
- Existing notifications: 3 total
  - N1: Linked to Project P1 (relation_type=PROJECT)
  - N2: Linked to Client C1 (relation_type=CLIENT)
  - N3: No relation
- Known IDs: (empty list)

### Request

```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "known_notification_ids": [] }'
```

### Expected Response

```json
{
  "notifications": [
    {
      "id": "<N3-uuid>",
      "title": "Generic Alert",
      "relation": null  // No relation
    },
    {
      "id": "<N2-uuid>",
      "title": "Client Update",
      "relation": {
        "relation_type": "CLIENT",
        "project_id": null,
        "client_id": "<C1-uuid>",
        "task_id": null
      }
    },
    {
      "id": "<N1-uuid>",
      "title": "Project Deadline",
      "relation": {
        "relation_type": "PROJECT",
        "project_id": "<P1-uuid>",
        "client_id": null,
        "task_id": null
      }
    }
  ]
}
```

### Validation Checks

- [ ] N1 includes `relation` object with `project_id` populated
- [ ] N2 includes `relation` object with `client_id` populated
- [ ] N3 includes `relation: null` (no relation present)

---

## Validation Scenario 4: Authentication Required

**Goal**: Verify endpoint rejects unauthenticated requests.

### Request (No Token)

```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Content-Type: application/json" \
  -d '{ "known_notification_ids": [] }'
```

### Expected Response

```json
{
  "error": "Authentication required"
}
```

### Validation Checks

- [ ] Response HTTP status is **401 Unauthorized**
- [ ] Response includes error message mentioning authentication

---

## Validation Scenario 5: User Isolation (Security)

**Goal**: Verify User A cannot see User B's notifications.

### Setup

- User A: `user_a@example.com` with 3 notifications (A1, A2, A3)
- User B: `user_b@example.com` with 3 notifications (B1, B2, B3)

### Request as User A

```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token_user_a>" \
  -H "Content-Type: application/json" \
  -d '{ "known_notification_ids": [] }'
```

### Expected Response

```json
{
  "notifications": [
    { "id": "<A3-uuid>", "title": "User A Notification" },
    { "id": "<A2-uuid>", "title": "User A Notification" },
    { "id": "<A1-uuid>", "title": "User A Notification" }
  ]
}
```

### Validation Checks

- [ ] Response contains only User A's notifications (never B1, B2, B3)
- [ ] Count == 3 (exactly User A's notifications)
- [ ] Repeat as User B; verify only B's notifications appear

---

## Validation Scenario 6: Malformed Request (Error Handling)

**Goal**: Verify endpoint rejects invalid input gracefully.

### Test Case A: Invalid UUID Format

**Request**:
```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "known_notification_ids": ["not-a-uuid"]
  }'
```

**Expected Response**:
```json
{
  "error": "Invalid UUID in known_notification_ids"
}
```

**Validation**:
- [ ] HTTP status is **400 Bad Request**

### Test Case B: List Too Large

**Request**:
```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "known_notification_ids": [
      "<uuid-1>", "<uuid-2>", ..., "<uuid-10001>"
    ]
  }'
```

**Expected Response**:
```json
{
  "error": "known_notification_ids size exceeds maximum (10000)"
}
```

**Validation**:
- [ ] HTTP status is **400 Bad Request**

### Test Case C: Invalid JSON

**Request**:
```bash
curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ invalid json }'
```

**Expected Response**:
```json
{
  "error": "Invalid JSON in request body"
}
```

**Validation**:
- [ ] HTTP status is **400 Bad Request**

---

## Validation Scenario 7: Payload Size & Performance

**Goal**: Verify endpoint returns performant response for typical workload.

### Setup

- User: `perf_test_user@example.com`
- Existing notifications: 1,000 total
- Known IDs: 500 UUIDs (first half)

### Request

```bash
time curl -X POST http://localhost:8000/api/notifications/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "known_notification_ids": [
      "<uuid-1>", "<uuid-2>", ..., "<uuid-500>"
    ]
  }'
```

### Expected Behavior

- [ ] Response HTTP status is **200 OK**
- [ ] Response `notifications` array contains exactly **500 items** (the unknown half)
- [ ] Response time is **<500ms** (observe `time` command output)
- [ ] Response payload size is **~1MB** (approx. 2KB per notification)

---

## Summary: Automated Test Template

Use this template for pytest or Django TestCase to automate all scenarios:

```python
# test/api/test_notification_sync.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.notifications.models import Notification, NotificationRelation
from apps.projects_and_clients.models import Project, Client
import json
import uuid
from datetime import datetime, timedelta

class NotificationSyncTests(TestCase):
    def setUp(self):
        """Create test user and notifications"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Create 5 test notifications
        self.notifications = []
        for i in range(5):
            notif = Notification.objects.create(
                user=self.user,
                title=f"Notification {i}",
                message=f"Message {i}",
                read=False,
                deliver_at=datetime.now() + timedelta(hours=i),
                type='SIMPLE'
            )
            self.notifications.append(notif)
    
    def test_sync_with_known_ids(self):
        """Scenario 1: Filter out known IDs"""
        known_ids = [str(self.notifications[0].id), str(self.notifications[2].id)]
        response = self.client.post(
            '/api/notifications/sync',
            json.dumps({'known_notification_ids': known_ids}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        # Should return 3 notifications (indices 1, 3, 4)
        self.assertEqual(len(data['notifications']), 3)
        returned_ids = [n['id'] for n in data['notifications']]
        self.assertNotIn(known_ids[0], returned_ids)
        self.assertNotIn(known_ids[1], returned_ids)
    
    def test_sync_without_known_ids(self):
        """Scenario 2: Return all notifications"""
        response = self.client.post(
            '/api/notifications/sync',
            json.dumps({'known_notification_ids': []}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(len(data['notifications']), 5)
    
    def test_unauthenticated_request(self):
        """Scenario 4: Reject unauthenticated"""
        self.client.logout()
        response = self.client.post(
            '/api/notifications/sync',
            json.dumps({'known_notification_ids': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_user_isolation(self):
        """Scenario 5: User A sees only own notifications"""
        user_b = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        Notification.objects.create(
            user=user_b,
            title="User B Notification",
            message="B",
            read=False,
            deliver_at=datetime.now(),
            type='SIMPLE'
        )
        response = self.client.post(
            '/api/notifications/sync',
            json.dumps({'known_notification_ids': []}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        # User A should see 5, not 6
        self.assertEqual(len(data['notifications']), 5)
        for notif in data['notifications']:
            # Verify none belong to user_b
            fetched = Notification.objects.get(id=notif['id'])
            self.assertEqual(fetched.user, self.user)
```

Run tests:
```bash
uv run manage.py test test.api.test_notification_sync
```

---

## Rollback Plan (if feature fails validation)

If any validation scenario fails:

1. Review the test failure against [contracts/notification-sync-contract.md](contracts/notification-sync-contract.md)
2. Check the data-model assumptions in [data-model.md](data-model.md)
3. Identify the implementation gap (service logic, schema, or route handler)
4. Fix and re-run the specific scenario
5. Once all scenarios pass, merge the feature branch

---

## Success Criteria

All scenarios passing = feature is production-ready:
- ✅ Scenario 1: Filtering works correctly
- ✅ Scenario 2: Bootstrap sync returns all notifications
- ✅ Scenario 3: Relations are included in response
- ✅ Scenario 4: Authentication is enforced
- ✅ Scenario 5: User isolation is maintained
- ✅ Scenario 6: Malformed requests are rejected gracefully
- ✅ Scenario 7: Performance meets SLA (<500ms P95)

---

**Next Step**: Follow [../../tasks.md](../../tasks.md) for implementation details and task assignments.
