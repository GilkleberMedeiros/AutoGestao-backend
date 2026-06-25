# Quickstart: Notification Service CRUD Validation

**Feature**: `002-notification-service-crud`  
**Created**: 2026-06-25

## Prerequisites

- Python virtualenv activated (`.venv`)
- Dependencies installed (`uv sync` or equivalent)
- Database migrated

## Setup

```bash
cd /home/gil/Projetos/AutoGestão-backend
uv run manage.py migrate
```

## Run Tests

### All notification service tests (sync + CRUD)

```bash
uv run manage.py test test.notifications.test_services -v 2
```

### Sync regression only

```bash
uv run manage.py test test.notifications.test_services.TestNotificationService__sync -v 2
```

### CRUD tests only (after implementation)

```bash
uv run manage.py test \
  test.notifications.test_services.TestNotificationService__create \
  test.notifications.test_services.TestNotificationService__get \
  test.notifications.test_services.TestNotificationService__list \
  test.notifications.test_services.TestNotificationService__partial_update \
  test.notifications.test_services.TestNotificationService__delete \
  -v 2
```

## Validation Scenarios

### Scenario 1: Create and Get

**Goal**: Verify create persists all fields and get returns them.

1. Run create test or Django shell:
   - Create user via `User.objects.create_user(...)`
   - Call `NotificationService.create(user, CreateNotificationReq(...))`
2. Call `NotificationService.get(user, str(notification.id))`
3. **Expected**: Same `title`, `type`, `deliver_at`; `read` is `false` by default

### Scenario 2: List Ordering

**Goal**: Verify list returns user-scoped results in `deliver_at DESC, id ASC` order.

1. Create 3 notifications with different `deliver_at` values for one user
2. Call `NotificationService.list(user)`
3. **Expected**: 3 results, newest first; empty for other users

### Scenario 3: Partial Update (Mark Read)

**Goal**: Verify only submitted fields change.

1. Create unread notification
2. `NotificationService.partial_update(user, id, PartialUpdateNotificationReq(read=True))`
3. **Expected**: `read=True`; `title` and `message` unchanged

### Scenario 4: Delete

**Goal**: Verify deletion removes notification from get/list.

1. Create notification
2. `NotificationService.delete(user, id)`
3. **Expected**: `get` raises `ResourceNotFoundError`; `list` count decreases by 1

### Scenario 5: User Isolation

**Goal**: User A cannot access User B's notifications.

1. Create notification for User B
2. User A calls `get`, `partial_update`, `delete` with User B's notification ID
3. **Expected**: `ResourceNotFoundError` on all operations

### Scenario 6: Sync Regression

**Goal**: Existing sync behavior unchanged (SC-006).

```bash
uv run manage.py test test.notifications.test_services test.api.test_notification_sync -v 2
```

**Expected**: All tests pass with zero failures.

## Manual Shell Smoke Test (Optional)

```bash
uv run manage.py shell
```

```python
from datetime import datetime
from apps.users.models import User
from apps.notifications.services import NotificationService
from apps.notifications.schemas import CreateNotificationReq, PartialUpdateNotificationReq

user = User.objects.first()
data = CreateNotificationReq(title="Test", deliver_at=datetime.now(), type="SIMPLE")
n = NotificationService.create(user, data)
assert NotificationService.get(user, str(n.id)).title == "Test"
NotificationService.partial_update(user, str(n.id), PartialUpdateNotificationReq(read=True))
NotificationService.delete(user, str(n.id))
```

## References

- Service contract: [contracts/notification-service-crud-contract.md](contracts/notification-service-crud-contract.md)
- Data model: [data-model.md](data-model.md)
- Sync feature: [../001-notification-sync/quickstart.md](../001-notification-sync/quickstart.md)

## Success Checklist

- [ ] All CRUD unit tests pass
- [ ] Sync unit tests pass (no regression)
- [ ] Sync API tests pass (`test/api/test_notification_sync.py`)
- [ ] User isolation verified in negative tests
- [ ] Partial update leaves untouched fields unchanged
