# Feature Specification: Notification Synchronization Endpoint

**Feature Branch**: `001-notification-sync`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Endpoint de sincronização de notificações do backend para o frontend que filtra notificações já conhecidas pelo cliente"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Client Syncs with Known Notifications (Priority: P1)

Mobile client maintains a local list of notification IDs it has already received. To prevent re-delivering duplicates and minimize payload size, the client sends this list to the backend; the backend returns only new notifications not in this list.

**Why this priority**: This is the primary use case for real-time sync scenarios where clients reconnect after brief interruptions or disconnect. Filtering duplicates ensures efficient bandwidth usage and prevents notification fatigue.

**Independent Test**: Can be fully tested by calling `/notifications/sync` with a populated `known_notification_ids` list and verifying: (1) returned notifications exclude all IDs in the list, (2) newly created notifications for the user appear in the response, (3) payload is minimal.

**Acceptance Scenarios**:

1. **Given** a user with 5 existing notifications and a client knowing 3 of them, **When** the client calls `/notifications/sync` with those 3 IDs, **Then** the endpoint returns exactly 2 new notifications (the unknown ones).
2. **Given** fresh notifications created after the client's last sync, **When** the client sends the previous sync list, **Then** the new notifications appear in the response immediately.
3. **Given** a client submitting invalid/non-existent UUIDs in the known list, **When** the endpoint processes the request, **Then** those IDs are safely ignored and the response includes all valid new notifications.

---

### User Story 2 - Client Syncs Without Prior Knowledge (Priority: P2)

When a new client first connects or after a full reset, it has no prior notification list. The endpoint must return all unread and recent notifications for the authenticated user to bootstrap the client state.

**Why this priority**: Essential for initial connect and data recovery. Ensures new clients and reinstalled apps can immediately populate their notification history without special-casing logic.

**Independent Test**: Can be fully tested by calling `/notifications/sync` with an empty or absent `known_notification_ids` list and verifying: (1) all user notifications are returned, (2) response ordering is consistent (e.g., most recent first), (3) no authentication bypass is possible.

**Acceptance Scenarios**:

1. **Given** a user with 10 existing notifications and no `known_notification_ids` provided, **When** the client calls `/notifications/sync`, **Then** all 10 notifications are returned.
2. **Given** a mobile app fresh install, **When** the authenticated user calls `/notifications/sync` without a list, **Then** the full notification history populates the client in a single call.
3. **Given** notifications with different delivery times, **When** they are returned, **Then** ordering is deterministic (by `deliver_at` or ID, consistently applied).

---

### User Story 3 - Error Handling and Security (Priority: P3)

The endpoint must handle edge cases: unauthenticated requests, invalid payload structures, and database errors. Security must ensure users see only their own notifications.

**Why this priority**: Protects against malicious or malformed requests and prevents information leakage across users. Important for production stability.

**Independent Test**: Can be fully tested by: (1) calling `/notifications/sync` without authentication and verifying a 401/403 error, (2) sending malformed `known_notification_ids` (non-UUID formats, oversized lists) and verifying graceful rejection, (3) two different users calling the endpoint and verifying each sees only their own notifications.

**Acceptance Scenarios**:

1. **Given** an unauthenticated request, **When** calling `/notifications/sync`, **Then** the endpoint returns 401 Unauthorized.
2. **Given** a request with `known_notification_ids` containing malformed UUIDs, **When** the endpoint processes it, **Then** a 400 Bad Request is returned with a clear error message.
3. **Given** two authenticated users, **When** User A calls the endpoint, **Then** User A sees only their notifications, never User B's.

---

### Edge Cases

- What happens when the `known_notification_ids` list contains notifications that do not belong to the user?
- How does the system handle extremely large lists (e.g., 10,000 IDs) to avoid timeout or memory issues?
- What if a notification is deleted between the client's last sync and the current request?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Endpoint MUST accept a POST request at `/notifications/sync` with a JSON payload containing optional `known_notification_ids` (list of UUIDs).
- **FR-002**: Endpoint MUST require authentication and return only notifications belonging to the authenticated user.
- **FR-003**: Endpoint MUST filter and return notifications excluding any IDs in the `known_notification_ids` list.
- **FR-004**: Endpoint MUST return all user notifications when `known_notification_ids` is empty, null, or omitted.
- **FR-005**: Response MUST include notification ID, title, message, read status, delivery time, type, and any extra fields.
- **FR-006**: Response data MUST include notification relation details (project/client/task reference if applicable).
- **FR-007**: Endpoint MUST validate that `known_notification_ids` contains only valid UUIDs; malformed UUIDs trigger a 400 Bad Request.
- **FR-008**: Endpoint MUST validate that the list size does not exceed a reasonable limit (e.g., 10,000 IDs) to prevent abuse.
- **FR-009**: Endpoint MUST return results ordered consistently (e.g., most recent `deliver_at` first, then by ID for tiebreaker).
- **FR-010**: Endpoint MUST handle database errors gracefully and return a 500 Internal Server Error with a generic message (no SQL details exposed).

### Key Entities

- **Notification**: Represents a message event (title, message, read flag, delivery time, type). Linked to a single user.
- **NotificationRelation**: Optional association of a notification to a domain entity (Project, Client, or Task) with a relation type indicator.
- **SyncRequest Payload**: Contains the list of known notification IDs from the client.
- **SyncResponse Payload**: List of new notification records with embedded relation details.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Endpoint responds to a sync request in under 500ms (P95) for a user with up to 1,000 notifications.
- **SC-002**: Filtering logic correctly excludes 100% of known notification IDs; no known IDs appear in the response.
- **SC-003**: All new notifications (created after the client's last known ID set) appear in the response; no notification loss.
- **SC-004**: Response payload size is minimized: when filtering 100 known IDs from 120 total, response contains exactly 20 new notifications.
- **SC-005**: Both unit tests (service methods isolated) and end-to-end API tests (full route with auth) achieve 100% code coverage for sync logic.
- **SC-006**: Security: unauthenticated requests are rejected; users can only see their own notifications (verified by cross-user test).

## Assumptions

- **Authentication**: Assumes existing Django authentication system is in place; the sync endpoint will use Django's built-in user context (e.g., `request.user`).
- **Notification Storage**: All notifications are persisted in the existing database; no external notification service is required for this feature.
- **Response Format**: Assumes client expects JSON format; response will follow the project's standard API response structure as defined by Django Ninja.
- **Date Ordering**: Notifications are naturally ordered by `deliver_at`; if no explicit order is specified, most recent first is a reasonable default.
- **Relation Details**: Not all notifications have a NotificationRelation; the response includes relation data only if it exists (optional field in the schema).
- **Scope Boundary**: This endpoint handles synchronization only; actual notification creation, marking as read, or deletion are out of scope and handled by separate endpoints.
- **List Limit**: A reasonable upper limit of 10,000 known notification IDs is assumed to prevent memory/timeout issues without hindering normal use.
