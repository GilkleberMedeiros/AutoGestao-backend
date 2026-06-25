# API Contract: Notification Synchronization Endpoint

**Phase**: 1 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Version**: 1.0.0 (API contract version; incremented on breaking changes)  
**Endpoint**: `POST /notifications/sync`  
**Authentication**: Required (Bearer token or session-based; project standard)

## Overview

This contract defines the exact request and response format for the notification synchronization endpoint. All clients and servers exchanging data via this endpoint MUST comply with this contract.

## Request Contract

### Endpoint Details

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | `/notifications/sync` |
| **Authentication** | Required (Bearer token or Django session) |
| **Content-Type** | `application/json` |

### Request Body Schema

#### Content-Type: `application/json`

```typescript
{
  "known_notification_ids": UUID[]  // Optional; defaults to []
}
```

#### Request Body Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `known_notification_ids` | `Array<UUID>` | No | `[]` | 0–10,000 items; each item must be valid UUID v4 | IDs of notifications already synced to client; backend excludes these from response |

#### UUID Format

Valid UUID: RFC 4122 format string (e.g., `"550e8400-e29b-41d4-a716-446655440000"`)

#### Example Requests

**Request 1: Sync with known IDs**
```json
{
  "known_notification_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Request 2: Sync without known IDs (full sync)**
```json
{
  "known_notification_ids": []
}
```

**Request 3: Omit known IDs entirely (equivalent to empty list)**
```json
{}
```

### Error Responses (Request Validation)

| HTTP Status | Error Condition | Response Body |
|-------------|-----------------|---------------|
| **400 Bad Request** | `known_notification_ids` contains invalid UUID format | `{"error": "Invalid UUID in known_notification_ids", "details": "[exact field path]"}` |
| **400 Bad Request** | `known_notification_ids` list size exceeds 10,000 | `{"error": "known_notification_ids size exceeds maximum (10000)", "details": "provided: N"}` |
| **400 Bad Request** | Request body is not valid JSON | `{"error": "Invalid JSON in request body"}` |
| **401 Unauthorized** | No authentication provided or token invalid | `{"error": "Authentication required"}` |
| **403 Forbidden** | Authenticated user lacks permission (edge case) | `{"error": "Access denied"}` |

---

## Response Contract

### Success Response (200 OK)

#### Content-Type: `application/json`

```typescript
{
  "notifications": [
    {
      "id": UUID,
      "title": string,
      "message": string | null,
      "read": boolean,
      "deliver_at": ISO8601DateTime,
      "type": "SIMPLE" | "ASSOCIATED" | "DEADLINE" | "SPENT_LIMIT",
      "extra_fields": object | null,
      "relation": {
        "relation_type": "PROJECT" | "CLIENT" | "TASK",
        "project_id": UUID | null,
        "client_id": UUID | null,
        "task_id": UUID | null
      } | null
    }
  ]
}
```

#### Response Body Fields

| Field | Type | Always Present | Description |
|-------|------|-----------------|-------------|
| `notifications` | `Array<Object>` | Yes | List of new notifications (those not in `known_notification_ids`); ordered by `deliver_at DESC, id ASC` |
| `notifications[*].id` | UUID | Yes | Unique notification ID; must be persisted by client for next sync |
| `notifications[*].title` | string | Yes | Notification title; max 255 characters |
| `notifications[*].message` | string or null | Yes | Notification detail text; null if not provided |
| `notifications[*].read` | boolean | Yes | Whether user has viewed the notification |
| `notifications[*].deliver_at` | ISO 8601 string | Yes | Delivery/creation timestamp in UTC (e.g., "2026-06-25T10:00:00Z") |
| `notifications[*].type` | string (enum) | Yes | Notification category: SIMPLE (generic), ASSOCIATED (linked to entity), DEADLINE (project deadline), SPENT_LIMIT (budget limit) |
| `notifications[*].extra_fields` | object or null | Yes | Type-specific metadata; structure depends on `type`; null if not applicable |
| `notifications[*].relation` | object or null | No | Domain entity association (project/client/task); null if notification not tied to entity |
| `notifications[*].relation.relation_type` | string (enum) | Yes (if relation present) | Type of related entity: PROJECT, CLIENT, or TASK |
| `notifications[*].relation.project_id` | UUID or null | Yes (if relation present) | Related project ID; null if `relation_type != "PROJECT"` |
| `notifications[*].relation.client_id` | UUID or null | Yes (if relation present) | Related client ID; null if `relation_type != "CLIENT"` |
| `notifications[*].relation.task_id` | UUID or null | Yes (if relation present) | Related task ID; null if `relation_type != "TASK"` |

#### Example Success Response

```json
{
  "notifications": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440099",
      "title": "Project Deadline Tomorrow",
      "message": "The project 'Website Redesign' is due tomorrow at 5 PM",
      "read": false,
      "deliver_at": "2026-06-25T14:30:00Z",
      "type": "DEADLINE",
      "extra_fields": {
        "deadline_hours": 24,
        "deadline_timestamp": "2026-06-26T17:00:00Z"
      },
      "relation": {
        "relation_type": "PROJECT",
        "project_id": "660f9511-f30c-42e5-b827-557766551000",
        "client_id": null,
        "task_id": null
      }
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440098",
      "title": "Budget Alert",
      "message": "You have exceeded your monthly spending limit",
      "read": false,
      "deliver_at": "2026-06-25T12:00:00Z",
      "type": "SPENT_LIMIT",
      "extra_fields": {
        "spent": 5000,
        "limit": 4500,
        "currency": "USD"
      },
      "relation": null
    }
  ]
}
```

#### Empty Sync Response

When no new notifications exist for the user:

```json
{
  "notifications": []
}
```

---

## Error Responses (Server-Side)

| HTTP Status | Error Condition | Response Body | Content-Type |
|-------------|-----------------|---------------|--------------|
| **500 Internal Server Error** | Unhandled database error | `{"error": "An error occurred processing your request"}` (no SQL/stack details) | `application/json` |
| **503 Service Unavailable** | Database unavailable (rare) | `{"error": "Service temporarily unavailable"}` | `application/json` |

---

## Compatibility & Versioning

### Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-06-25 | Initial contract; filters notifications by known IDs; includes relation details |

### Breaking Change Policy

**Major Version (X.Y.Z)**: Increment X when response structure changes in incompatible ways (e.g., removing a required field, changing existing field type).

**Minor Version (X.Y.Z)**: Increment Y when new optional response fields are added (e.g., new `extra_fields` subkeys, optional `relation` enhancements).

**Patch Version (X.Y.Z)**: Increment Z for bug fixes and non-behavioral clarifications.

### Backward Compatibility

- **Adding fields**: Always optional; clients ignore unknown fields.
- **Changing field order**: JSON object field order is not guaranteed; clients must access by name, not position.
- **Removing fields**: Constitutes a major version bump; requires deprecation period.

---

## Performance SLA

| Metric | Target |
|--------|--------|
| **Response Time (P95)** | <500ms |
| **Response Time (P99)** | <1000ms |
| **Availability** | 99.5% uptime |

## Security & Data Protection

### Authentication

- Endpoint requires valid authentication (Bearer token or session cookie).
- All requests without authentication return **401 Unauthorized**.

### Authorization

- Endpoint returns only notifications belonging to `request.user`.
- Attempting to access another user's notifications returns filtered results (user sees only their own).
- No error is returned if `known_notification_ids` contains IDs from other users; they are simply ignored.

### Data Sensitivity

- Notification payloads contain user-facing messages; treat as sensitive.
- Timestamps and relation IDs may be linked to user activity; do not log full responses.
- `extra_fields` may contain domain-specific data (e.g., budget amounts, task titles); ensure HTTPS transport.

### Input Validation

- All UUID inputs must be sanitized and validated before database queries.
- List size must be bounded to prevent DOS attacks.
- JSON schema validation must reject malformed requests early.

---

## Contract Compliance Checklist

**For Clients**:
- [ ] Parse `deliver_at` as ISO 8601 datetime and convert to local timezone for display.
- [ ] Persist all `id` values received; send them as `known_notification_ids` in next sync call.
- [ ] Handle null `relation` and null `extra_fields` gracefully (assume no relation/metadata if absent).
- [ ] Display notification types appropriately: DEADLINE types may warrant prominent styling; SPENT_LIMIT types may trigger financial alerts.
- [ ] Respect `read` status from initial sync; do not modify it locally without confirmation from backend.

**For Servers**:
- [ ] Validate authentication before processing any request.
- [ ] Validate `known_notification_ids` size (≤10,000) and UUID format before querying database.
- [ ] Filter results to `request.user` only; never leak other users' notifications.
- [ ] Order results by `deliver_at DESC, id ASC` for deterministic behavior.
- [ ] Prefetch `NotificationRelation` data to avoid N+1 queries.
- [ ] Return **200 OK** with empty `notifications` array if no new results exist.
- [ ] Return **400 Bad Request** for malformed input; **500 Internal Server Error** for unhandled exceptions (never expose SQL or stack traces).

---

## Summary

This contract guarantees:
1. **Deterministic** filtering: clients can reliably sync by sending known IDs.
2. **Complete** responses: notifications include all required metadata and optional relation details.
3. **Secure** isolation: users see only their own notifications.
4. **Versioned** evolution: future changes follow semantic versioning.
5. **Performance-bounded** operations: sub-500ms response time for typical use.
