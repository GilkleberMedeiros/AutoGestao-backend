# Data Model: Notification Service CRUD

**Phase**: 1 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Input**: Feature specification, research.md, existing models

## Overview

CRUD operations reuse the existing persistence model from feature `001-notification-sync`. No new tables or migrations are required. This document describes entities, service input shapes, validation rules, and state transitions relevant to CRUD.

## Persistent Entities (Existing)

### Notification

**Purpose**: User-owned alert record.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | auto | Primary key; immutable |
| `user` | FK → User | yes | Owner; cascade delete |
| `title` | string(255) | yes | |
| `message` | text | no | Nullable |
| `read` | boolean | yes | Default `false` |
| `deliver_at` | datetime | yes | Delivery/display time |
| `type` | enum string | yes | SIMPLE, ASSOCIATED, DEADLINE, SPENT_LIMIT |
| `extra_fields` | JSON | no | Type-specific metadata |

**Source**: `apps/notifications/models.py`

### NotificationRelation

**Purpose**: Optional link to project, client, or task.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | auto | Primary key |
| `notification` | FK → Notification | yes | Cascade on notification delete |
| `relation_type` | enum string | no | PROJECT, CLIENT, TASK |
| `project` | FK → Project | no | Required when `relation_type=PROJECT` |
| `client` | FK → Client | no | Required when `relation_type=CLIENT` |
| `task` | FK → Task | no | Required when `relation_type=TASK` |

**Source**: `apps/notifications/models.py`

## Service Input DTOs (New — schemas only)

### CreateNotificationReq

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | max 255 |
| `deliver_at` | datetime | yes | |
| `type` | string | yes | Must be valid notification type |
| `message` | string | no | |
| `read` | boolean | no | Default false |
| `extra_fields` | object | no | |
| `relation` | RelationInput | no | Nested relation payload |

### PartialUpdateNotificationReq

All fields optional; only provided fields are updated.

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | |
| `message` | string | |
| `read` | boolean | Common use: mark as read |
| `deliver_at` | datetime | |
| `type` | string | |
| `extra_fields` | object | |
| `relation` | RelationInput | Updates or creates relation when provided |

### RelationInput

| Field | Type | Required when |
|-------|------|---------------|
| `relation_type` | string | Always when relation block present |
| `project_id` | UUID | `relation_type=PROJECT` |
| `client_id` | UUID | `relation_type=CLIENT` |
| `task_id` | UUID | `relation_type=TASK` |

## Validation Rules

### Create

1. `title` and `deliver_at` MUST be present.
2. `type` MUST be one of `Notification.NOTIFICATION_TYPE_CHOICES`.
3. If `relation` is provided:
   - `relation_type` MUST be set.
   - Exactly one target FK MUST match `relation_type`.
   - Target entity MUST exist and belong to the same `user`.
4. For `type=ASSOCIATED` or `type=DEADLINE`, `relation` SHOULD be provided (service may reject if missing — business rule).

### Get / List / Delete

1. Query MUST filter `notification.user = user`.
2. Missing or cross-user ID → `ResourceNotFoundError`.

### Partial Update

1. Only keys present in request are modified.
2. Empty payload → no database writes; return current entity.
3. Relation update uses `update_or_create` on `notificationrelation_set`.
4. Invalid type or relation combination → validation error before save.

### Delete

1. Hard delete notification row.
2. `NotificationRelation` removed via FK cascade.

## State Transitions

```text
[none] --create--> Notification (read=false by default)
Notification --partial_update(read=true)--> Notification (read)
Notification --partial_update(fields)--> Notification (modified fields)
Notification --delete--> [removed]
```

No soft-delete or archive state in this feature.

## Relationships Diagram

```text
User 1──* Notification 1──* NotificationRelation
                              ├──0..1 Project (user-scoped)
                              ├──0..1 Client  (user-scoped)
                              └──0..1 Task    (via project, user-scoped)
```

## Compatibility with Sync

| CRUD Operation | Sync Impact |
|----------------|-------------|
| create | New notification appears on next sync (not in known_ids) |
| partial_update | Updated fields reflected on next sync |
| delete | Notification absent from sync response even if ID in known_ids |
| get / list | No direct sync impact |

Ordering for `list()` and `sync()` both use `deliver_at DESC, id ASC`.

## Migration Requirements

**None.** All fields and tables already exist.
