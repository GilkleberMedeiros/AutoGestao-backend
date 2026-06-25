# Feature Specification: Notification Service CRUD Operations

**Feature Branch**: `002-notification-service-crud`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Preciso que você implemente os métodos de CRUD no NotificationService. Implemente os seguintes métodos: create, get, list update (partial) e delete."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Notifications for a User (Priority: P1)

The system must be able to register new notifications on behalf of a user when domain events occur (deadlines, spending limits, project updates, or generic alerts). Each notification must capture title, message, delivery time, type, optional metadata, and optional association to a project, client, or task.

**Why this priority**: Without creation, no notification can enter the system. This is the foundation for sync, in-app display, and push delivery pipelines.

**Independent Test**: Can be fully tested by creating a notification for a known user and verifying it is persisted with all required attributes and is retrievable only for that user.

**Acceptance Scenarios**:

1. **Given** a valid user and notification payload with title and delivery time, **When** a notification is created, **Then** a new notification record exists linked to that user with default unread status.
2. **Given** a notification of type associated with a project, **When** it is created with relation details, **Then** the notification and its entity association are stored together.
3. **Given** a notification payload missing required fields (e.g., title or delivery time), **When** creation is attempted, **Then** the operation is rejected with a clear validation outcome.

---

### User Story 2 - Retrieve a Single Notification (Priority: P1)

Authorized callers must fetch one notification by identifier, scoped to the owning user, to display detail views or confirm state after an action (e.g., opening a push notification).

**Why this priority**: Single-record retrieval is required for detail screens, deep links, and integrity checks after create/update.

**Independent Test**: Can be fully tested by creating a notification, fetching it by ID for the owning user, and verifying all stored fields are returned.

**Acceptance Scenarios**:

1. **Given** an existing notification belonging to User A, **When** User A requests it by ID, **Then** the full notification is returned.
2. **Given** a notification ID that does not exist, **When** retrieval is attempted, **Then** a not-found outcome is returned.
3. **Given** a notification belonging to User B, **When** User A requests it by ID, **Then** a not-found outcome is returned (no cross-user access).

---

### User Story 3 - List Notifications for a User (Priority: P2)

Authorized callers must list all notifications for a user, ordered consistently (most recent delivery time first), to power notification centers and support operational inspection.

**Why this priority**: Listing complements single retrieval and supports bulk UI views and internal tooling without requiring repeated single fetches.

**Independent Test**: Can be fully tested by creating multiple notifications for one user and verifying the list returns only that user's records in deterministic order.

**Acceptance Scenarios**:

1. **Given** a user with several notifications, **When** their notifications are listed, **Then** all and only that user's notifications are returned.
2. **Given** a user with no notifications, **When** listing is requested, **Then** an empty result is returned without error.
3. **Given** notifications with different delivery times, **When** listed, **Then** results are ordered by delivery time descending, with a stable tiebreaker.

---

### User Story 4 - Partially Update a Notification (Priority: P2)

Authorized callers must update one or more fields of an existing notification (e.g., mark as read, change title or message, adjust delivery time or metadata) without requiring a full replacement of the record.

**Why this priority**: Partial updates support common client actions such as marking notifications as read and correcting content without resending the entire object.

**Independent Test**: Can be fully tested by creating a notification, applying a partial update to one field, and verifying only that field changed while others remain intact.

**Acceptance Scenarios**:

1. **Given** an unread notification, **When** it is partially updated with read status true, **Then** only the read status changes and other fields remain unchanged.
2. **Given** an associated notification, **When** relation details are partially updated, **Then** the association reflects the new values without affecting unrelated fields.
3. **Given** a notification ID that does not exist or belongs to another user, **When** partial update is attempted, **Then** a not-found outcome is returned.
4. **Given** a partial update with invalid field values (e.g., unknown notification type), **When** applied, **Then** the operation is rejected with a clear validation outcome.

---

### User Story 5 - Delete a Notification (Priority: P3)

Authorized callers must permanently remove a notification when it is no longer relevant (user dismissal, retraction, or data cleanup), including any linked entity association.

**Why this priority**: Deletion supports user control, GDPR-style cleanup, and prevents stale items from reappearing on the next sync.

**Independent Test**: Can be fully tested by creating a notification, deleting it, and verifying subsequent retrieval and listing no longer include it.

**Acceptance Scenarios**:

1. **Given** an existing notification for User A, **When** User A deletes it, **Then** it no longer appears in get or list operations for User A.
2. **Given** a notification with an entity association, **When** it is deleted, **Then** the association is removed along with the notification.
3. **Given** a notification ID that does not exist or belongs to another user, **When** deletion is attempted, **Then** a not-found outcome is returned.

---

### Edge Cases

- What happens when partial update receives an empty payload (no fields to change)?
- How does the system handle creation of associated notifications without required relation targets for the declared type?
- What happens when two users attempt to access the same notification ID simultaneously (read/update/delete)?
- How are notifications with null message or null extra metadata handled on create and partial update?
- Does deletion of a notification affect the existing sync behavior for clients that still hold the deleted ID in their known list?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The notification service MUST provide a **create** operation that persists a new notification for a specified user with title, delivery time, and notification type at minimum.
- **FR-002**: The notification service MUST support optional message text and optional structured metadata on create.
- **FR-003**: The notification service MUST support optional entity association (project, client, or task) on create when the notification type requires or allows association.
- **FR-004**: The notification service MUST provide a **get** operation that retrieves one notification by identifier, scoped to the owning user.
- **FR-005**: The notification service MUST provide a **list** operation that returns all notifications for a given user, ordered by delivery time descending with a deterministic tiebreaker.
- **FR-006**: The notification service MUST provide a **partial update** operation that modifies only the fields supplied in the request, leaving all other fields unchanged.
- **FR-007**: The notification service MUST provide a **delete** operation that permanently removes a notification and its association, scoped to the owning user.
- **FR-008**: All operations MUST enforce user isolation: a user MUST NOT read, update, or delete another user's notifications.
- **FR-009**: Operations on non-existent or inaccessible notification IDs MUST return a consistent not-found outcome.
- **FR-010**: Invalid input (missing required fields, invalid notification type, invalid relation combination) MUST be rejected before persistence with a clear validation outcome.
- **FR-011**: The existing notification synchronization capability MUST remain unaffected by these CRUD operations.

### Key Entities

- **Notification**: A user-facing alert with title, optional message, read status, delivery time, type (simple, associated, deadline, spending limit), and optional structured metadata.
- **Notification Association**: Optional link between a notification and a domain entity (project, client, or task), including the association type.
- **User**: Owner of notifications; all CRUD operations are scoped to a single user context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A notification can be created and retrieved in a single user flow with 100% field accuracy (all submitted attributes match stored values).
- **SC-002**: 100% of list and get results for a given user contain only that user's notifications (zero cross-user leakage in test scenarios).
- **SC-003**: Partial updates change only the submitted fields in 100% of tested cases; untouched fields retain their previous values.
- **SC-004**: Deleted notifications are absent from subsequent get and list operations in 100% of tested cases.
- **SC-005**: Invalid create or partial-update attempts are rejected before persistence in 100% of negative test scenarios.
- **SC-006**: Existing notification sync behavior continues to pass all current automated tests without regression.

## Assumptions

- Scope is limited to the **notification service layer** (create, get, list, partial update, delete). Public HTTP routes for these operations are out of scope for this feature unless added in a follow-up specification.
- Operations follow the same user-scoping and error-handling conventions used by other domain services in the project (e.g., not-found and validation errors).
- Notification types and association rules align with the existing notification data model already used by the sync feature.
- The existing `sync` operation remains in the same service class and is not modified except to ensure compatibility.
- List ordering matches the sync feature convention: delivery time descending, then identifier ascending for ties.
- Partial update is the only update mode required; full replacement update is not in scope.

## Dependencies

- Existing notification data model and notification sync feature (`001-notification-sync`).
- User ownership model for scoping all operations.
- Domain entities (project, client, task) for associated notification types.
