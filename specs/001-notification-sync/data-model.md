# Data Model: Notification Synchronization

**Phase**: 1 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Input**: Feature specification and research.md

## Overview

The notification sync feature uses existing data models (`Notification` and `NotificationRelation`). This document describes the entities, their relationships, and any new domain concepts introduced by the sync feature.

## Existing Entities

### Notification

**Purpose**: Represents a message event sent to a user for display and action.

**Key Attributes**:
- `id` (UUID): Unique notification identifier; primary key and sync reference
- `user` (ForeignKey → User): The recipient of the notification
- `title` (CharField, max_length=255): Short notification heading
- `message` (TextField, nullable): Detailed notification body
- `read` (BooleanField): Whether the user has viewed the notification
- `deliver_at` (DateTimeField): When the notification should be shown/when it was created
- `type` (CharField): Notification category (SIMPLE, ASSOCIATED, DEADLINE, SPENT_LIMIT)
- `extra_fields` (JSONField, nullable): Unstructured data for specific notification types

**Validation Rules**:
- `id` immutable after creation; UUID v4 randomly generated
- `user` cannot be null; deleting a user cascades deletion of their notifications
- `title` required; max 255 characters
- `message` optional; can be null or blank
- `deliver_at` required; typically set to creation timestamp or point-in-future for scheduled notifications
- `type` constrained to fixed set (SIMPLE, ASSOCIATED, DEADLINE, SPENT_LIMIT)
- `extra_fields` optional; structure varies by `type`

**Current Status**: Already implemented in `apps/notifications/models.py`

### NotificationRelation

**Purpose**: Optional association of a notification to domain entities (Project, Client, Task) for filtering and context linking.

**Key Attributes**:
- `id` (UUID): Primary key
- `notification` (ForeignKey → Notification): Which notification this relation belongs to
- `project` (ForeignKey → Project, nullable): Associated project (Project app)
- `client` (ForeignKey → Client, nullable): Associated client (projects_and_clients app)
- `task` (ForeignKey → Task, nullable): Associated task (projects_and_clients app)
- `relation_type` (CharField): What type of entity is associated (PROJECT, CLIENT, TASK)

**Validation Rules**:
- `notification` required; cannot be null; 1-to-1 or 1-to-many relationship (multiple relations per notification are possible; current schema allows this)
- At most ONE of `project`, `client`, or `task` should be populated based on `relation_type`
- `relation_type` constrained to (PROJECT, CLIENT, TASK)
- Deleting the related entity (project/client/task) cascades deletion of the relation

**Current Status**: Already implemented in `apps/notifications/models.py`

## New Domain Concepts

### SyncRequest (Request Payload)

**Purpose**: Client-to-server communication of known notification state.

**Structure**:
```python
class SyncRequest:
    known_notification_ids: list[UUID]  # IDs of notifications already on client
```

**Validation Rules**:
- `known_notification_ids` optional; defaults to empty list if omitted, null, or not provided
- Each UUID must be valid RFC 4122 format; malformed UUIDs trigger 400 Bad Request
- List size must not exceed 10,000; oversized lists trigger 400 Bad Request with error message
- No validation that IDs actually belong to the user (backend ignores non-user IDs safely)

### SyncResponse (Response Payload)

**Purpose**: Server-to-client communication of new notifications and their context.

**Structure**:
```python
class NotificationDTO:
    id: UUID
    title: str
    message: Optional[str]
    read: bool
    deliver_at: datetime
    type: str  # Literal["SIMPLE", "ASSOCIATED", "DEADLINE", "SPENT_LIMIT"]
    extra_fields: Optional[dict]
    relation: Optional[RelationDTO]

class RelationDTO:
    relation_type: str  # Literal["PROJECT", "CLIENT", "TASK"]
    project_id: Optional[UUID]
    client_id: Optional[UUID]
    task_id: Optional[UUID]

class SyncResponse:
    notifications: list[NotificationDTO]
```

**Validation Rules**:
- Response includes only notifications for the authenticated user
- Each notification in response has ID not in the original `known_notification_ids` list
- `relation` field is null if no `NotificationRelation` exists for that notification
- `deliver_at` formatted as ISO 8601 string (e.g., "2026-06-25T10:00:00Z")
- Response is ordered by `deliver_at DESC, id ASC` (newest first; stable sort)

### Sync Operation (Business Logic)

**Purpose**: Filter operation that produces new notifications for client synchronization.

**Algorithm**:
1. Fetch all notifications for the authenticated user
2. Exclude notifications with IDs in `known_notification_ids`
3. Prefetch related `NotificationRelation` data to avoid N+1 queries
4. Order by `deliver_at DESC, id ASC`
5. Serialize to `SyncResponse` format

**Example**:
- User has 5 notifications: A, B, C, D, E (created in that chronological order by `deliver_at`)
- Client sends `known_notification_ids = [A, C]`
- Backend returns `[E, D, B]` (C excluded, ordered newest first)

## Relationship Diagram

```
User (users.User)
  ├─ Notification (1-to-many)
  │   ├─ id: UUID (primary key)
  │   ├─ user_id: FK
  │   ├─ title, message, read, deliver_at, type, extra_fields
  │   └─ NotificationRelation (0-or-1)
  │       ├─ notification_id: FK
  │       ├─ project_id: FK (nullable, OR)
  │       ├─ client_id: FK (nullable, OR)
  │       └─ task_id: FK (nullable, OR)
  │
  Project (projects_and_clients.Project)
    └─ NotificationRelation (0-or-many) [reverse FK]
  Client (projects_and_clients.Client)
    └─ NotificationRelation (0-or-many) [reverse FK]
  Task (projects_and_clients.Task)
    └─ NotificationRelation (0-or-many) [reverse FK]
```

## State Transitions & Invariants

### Notification State

**Invariants**:
- Once created, `id`, `user_id`, `deliver_at`, and `type` are immutable
- `read` status is mutable but out-of-scope for the sync endpoint (handled separately)
- `message` and `extra_fields` are immutable after creation

**Transitions** (per-user sync):
1. New notification created → synced to client on next `/sync` call
2. Notification filtered out on `/sync` because ID is in `known_notification_ids` → stays hidden from client until removed from known list
3. Notification marked as read (separate endpoint) → still returned by `/sync` if ID not known (clients manage read state locally)

### Relation State

**Invariants**:
- `relation_type` determines which foreign key (`project_id`, `client_id`, `task_id`) is populated
- Exactly one FK should be non-null per `relation_type` rule
- Deleting the related entity cascades deletion of the relation (default Django behavior)

## No New Entities Required

The sync feature does not introduce new database entities or require schema migrations. It purely reuses and filters existing `Notification` and `NotificationRelation` tables through new service logic and serialization layers.

## Data Volume Estimates

**Typical scenarios**:
- New user: 0 notifications initially
- Active user (months): 50–500 notifications (varies by feature activity)
- Power user (1+ year): 500–5000 notifications
- Heavy notification system: up to 10,000+ per user (monitored)

**Sync payload size**:
- Per notification: ~1–2 KB (JSON-serialized, including relation data)
- 100 new notifications: ~100–200 KB payload
- Network latency: <100ms typical; payload transfer at modern client speeds: <50ms

**Database storage**:
- 1 million users × 1,000 notifications avg = 1 billion notification rows
- PostgreSQL storage: ~40–50 GB (depends on `extra_fields` size and indexing overhead)

## Design Summary

The sync feature leverages existing, well-structured models (`Notification` and `NotificationRelation`). The filtering and ordering logic is encapsulated in a new `NotificationService.sync()` method. New domain concepts (`SyncRequest`, `SyncResponse`, `RelationDTO`) are defined in schemas, not as database entities. This lightweight design minimizes schema migration complexity and keeps the codebase maintainable per the project's constitution principles.
