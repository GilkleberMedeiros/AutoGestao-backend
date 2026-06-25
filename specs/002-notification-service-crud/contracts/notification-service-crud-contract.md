# Service Contract: Notification CRUD Operations

**Phase**: 1 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Version**: 1.0.0  
**Scope**: Internal service layer (`NotificationService`) — no HTTP endpoints in this feature

## Overview

This contract defines the method signatures, inputs, outputs, and error behavior for CRUD operations on notifications. Future HTTP routes MUST delegate to these methods without duplicating business logic.

**Implementation file**: `apps/notifications/services/notification.py`  
**Input schemas**: `apps/notifications/schemas.py`

---

## Methods

### `create(user, data: CreateNotificationReq) -> Notification`

Creates a notification for `user`. Optionally creates a `NotificationRelation` when `data.relation` is provided.

| Aspect | Detail |
|--------|--------|
| **Transaction** | Atomic when relation is created |
| **Success** | Returns persisted `Notification` with relation prefetched if created |
| **Validation error** | Raises `BusinessRuleError` or `ValueError` for invalid type/relation |
| **Ownership** | Related project/client/task must belong to `user` |

---

### `get(user, notification_id: str) -> Notification`

Retrieves a single notification by ID scoped to `user`.

| Aspect | Detail |
|--------|--------|
| **Success** | Returns `Notification` |
| **Not found** | Raises `ResourceNotFoundError("Notification not found.")` |
| **Cross-user** | Same as not found (no information leakage) |

---

### `list(user) -> QuerySet[Notification]`

Returns all notifications for `user`.

| Aspect | Detail |
|--------|--------|
| **Ordering** | `deliver_at DESC, id ASC` |
| **Prefetch** | `notificationrelation_set` |
| **Empty** | Empty queryset (not an error) |

---

### `partial_update(user, notification_id: str, data: PartialUpdateNotificationReq) -> Notification`

Updates only fields present in `data`.

| Aspect | Detail |
|--------|--------|
| **Transaction** | Atomic when relation is updated |
| **Empty payload** | Returns notification unchanged |
| **Not found** | Raises `ResourceNotFoundError` |
| **Validation error** | Raises on invalid type/relation |
| **Success** | Returns updated `Notification` |

---

### `delete(user, notification_id: str) -> dict`

Permanently deletes a notification and cascades relation removal.

| Aspect | Detail |
|--------|--------|
| **Success** | Returns `{"success": True}` (matches `MovGroupService.delete`) |
| **Not found** | Raises `ResourceNotFoundError` |

---

### `sync(user, known_ids: list[UUID]) -> QuerySet[Notification]` *(existing — unchanged)*

See `specs/001-notification-sync/contracts/notification-sync-contract.md`.

---

## Input Schemas

### CreateNotificationReq

```python
class RelationInput(Schema):
    relation_type: str          # PROJECT | CLIENT | TASK
    project_id: UUID | None = None
    client_id: UUID | None = None
    task_id: UUID | None = None

class CreateNotificationReq(Schema):
    title: str
    deliver_at: datetime
    type: str                   # SIMPLE | ASSOCIATED | DEADLINE | SPENT_LIMIT
    message: str | None = None
    read: bool = False
    extra_fields: dict | None = None
    relation: RelationInput | None = None
```

### PartialUpdateNotificationReq

```python
class PartialUpdateNotificationReq(Schema):
    title: str | None = None
    message: str | None = None
    read: bool | None = None
    deliver_at: datetime | None = None
    type: str | None = None
    extra_fields: dict | None = None
    relation: RelationInput | None = None
```

---

## Error Contract

| Condition | Exception | Message (example) |
|-----------|-----------|-------------------|
| Notification not found or wrong user | `ResourceNotFoundError` | `"Notification not found."` |
| Invalid notification type | `BusinessRuleError` | `"Invalid notification type."` |
| Relation target missing or wrong user | `ResourceNotFoundError` | `"Related project not found."` |
| Inconsistent relation_type and IDs | `BusinessRuleError` | `"relation_type PROJECT requires project_id."` |

---

## User Isolation Guarantee

Every method MUST apply `filter(user=user)` (or set `user` on create). Callers MUST NOT bypass this by passing raw queryset IDs without user context.

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-06-25 | Initial service CRUD contract |

---

## Compliance Checklist (Implementers)

- [x] Method signatures match this contract
- [x] `apps.users.models.User` used (not Django auth User)
- [x] `sync()` behavior unchanged
- [x] Unit tests cover all methods and error paths
- [x] Patterns match `MovGroupService` / `ProjectService` conventions
