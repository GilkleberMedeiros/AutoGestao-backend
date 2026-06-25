# Research: Notification Synchronization Endpoint

**Phase**: 0 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Input**: Specification requirements and technical context analysis

## Overview

Research phase validates technology choices, confirms best practices, and resolves any "NEEDS CLARIFICATION" markers from the specification. The specification contains no unresolved clarifications; all technical decisions are confirmed below.

## Technology Decisions

### Decision: Django ORM for Filtering

**Resolution**: Use Django ORM `exclude()` to filter out known notification IDs in a single query.

**Rationale**: Django ORM is the project standard for data access; using `Notification.objects.filter(user=user).exclude(id__in=known_ids).order_by('-deliver_at', 'id')` is idiomatic, maintainable, and avoids raw SQL complexity.

**Alternatives Considered**:
- **Raw SQL with NOT IN clause**: More verbose; SQL injection risk without proper parameterization; less testable
- **In-memory filtering (fetch all, filter in Python)**: Inefficient for large datasets; violates single responsibility principle (DB filtering vs. business logic)
- **Caching layer**: Premature optimization; adds complexity without proven performance need

**Decision**: Django ORM filtering ✅

### Decision: List Limit Validation

**Resolution**: Implement a configurable constant `SYNC_MAX_KNOWN_IDS = 10000` to reject requests with oversized lists.

**Rationale**: Prevents memory exhaustion and timeout attacks; 10,000 IDs is reasonable for typical mobile app sync patterns (device reconnection after hours/days of offline time).

**Alternatives Considered**:
- **No limit**: Vulnerable to abuse (attacker sends 1M IDs → OOM or timeout)
- **Lower limit (100)**: Too restrictive; excludes valid use cases (app unused for weeks)
- **Dynamic limit (based on user subscriptions)**: Over-engineered for current scope; revisit if scaling demands arise

**Decision**: Fixed 10,000 limit with validation error ✅

### Decision: Response Ordering

**Resolution**: Order results by `deliver_at DESC, id ASC` (newest notifications first; tie-breaker by UUID insertion order).

**Rationale**: Most recent notifications typically matter most to users; deterministic secondary sort ensures reproducible test results and consistent client behavior.

**Alternatives Considered**:
- **No explicit order**: Undefined behavior; database may return unpredictable order on repeated queries
- **Order by ID only**: Does not reflect notification intent (which is time-relative, not creation order)

**Decision**: `-deliver_at, id` ordering ✅

### Decision: Relation Data Inclusion

**Resolution**: Include `NotificationRelation` data in response via Django Ninja schema with nested serialization; use `select_related()` to minimize N+1 query problems.

**Rationale**: Clients need domain context (which project/client/task triggered the notification); `select_related()` fetches related records in a single join; minimal performance impact.

**Alternatives Considered**:
- **Omit relation data**: Clients lose actionable context (cannot link to project)
- **Separate endpoint for relations**: Requires 2 API calls; increases client complexity and latency
- **No prefetch optimization**: N+1 queries; performance degrades linearly with notification count

**Decision**: Nested schema with `select_related()` ✅

### Decision: Authentication & User Isolation

**Resolution**: Use Django's built-in `request.user` and authentication middleware; filter `Notification.objects.filter(user=request.user)` to enforce per-user isolation.

**Rationale**: Project already uses Django authentication; reusing it prevents custom security bugs and maintains consistency with existing endpoints.

**Alternatives Considered**:
- **Custom token-based auth**: Unnecessary; duplicates existing Django auth; higher maintenance burden
- **No explicit user check (rely on frontend)**: Major security risk; backend must enforce user boundaries

**Decision**: Django auth + explicit user filter ✅

## API Contract Best Practices

### Request Schema Design

**Decision**: Accept `known_notification_ids` as an optional array of UUIDs; default to empty list if omitted.

**Rationale**: Minimizes client-side logic; clients can call `/sync` on every reconnect without conditional handling.

**Format**:
```json
{
  "known_notification_ids": ["uuid1", "uuid2", ...] // optional; default []
}
```

### Response Schema Design

**Decision**: Return array of enhanced notification objects with embedded relation details.

**Rationale**: Single response payload; clients can immediately render notifications and resolve domain context without follow-up requests.

**Format**:
```json
{
  "notifications": [
    {
      "id": "uuid",
      "title": "...",
      "message": "...",
      "read": false,
      "deliver_at": "2026-06-25T10:00:00Z",
      "type": "SIMPLE|ASSOCIATED|DEADLINE|SPENT_LIMIT",
      "extra_fields": {...},
      "relation": {  // null if no relation
        "relation_type": "PROJECT|CLIENT|TASK",
        "project_id": "uuid" // null if relation_type != PROJECT
        "client_id": "uuid"  // null if relation_type != CLIENT
        "task_id": "uuid"    // null if relation_type != TASK
      }
    }
  ]
}
```

## Performance Considerations

### Database Query Performance

**Analysis for 1,000 notifications with 100 known IDs**:

1. **Filter + Exclude**: `Notification.objects.filter(user=user).exclude(id__in=[100 UUIDs]).select_related('notificationrelation')`
   - Single query with indexed lookups on `user_id` and `id`
   - PostgreSQL query planner uses indexe on both columns
   - Estimated execution: <10ms

2. **Ordering & Limit**: `order_by('-deliver_at', 'id')` returns most recent records first
   - Prevents unbounded full-table scans
   - Index on `deliver_at` recommended (created by Django migration)

3. **Memory**: Response payload ~2MB for 900 notifications (~2KB per notification with full details)
   - Well within typical server memory constraints
   - Client-side JSON parsing burden acceptable

**Conclusion**: <500ms P95 target is easily achievable with proper indexing ✅

### Index Recommendations

- Index on `(user_id, deliver_at DESC)` for common filter + order pattern
- Index on `(user_id, id)` for exclusion filters

These indexes should be created in a separate database migration during implementation phase.

## Testing Strategy

### Unit Test Scope (Service Layer)

- **Scenario 1**: Filter with known IDs → returned list excludes all known IDs
- **Scenario 2**: Filter with empty list → returns all notifications
- **Scenario 3**: Filter with invalid UUIDs → gracefully ignored (no exception)
- **Scenario 4**: Large list (10,000 IDs) → accepted and processed
- **Scenario 5**: List size > 10,000 → rejected with 400 error
- **Scenario 6**: Ordering is deterministic → multiple calls return same order

### E2E Test Scope (Route Layer)

- **Scenario 1**: Unauthenticated request → 401 Unauthorized
- **Scenario 2**: Valid request with known IDs → returns filtered notifications
- **Scenario 3**: Valid request without known IDs → returns all notifications
- **Scenario 4**: User A request → sees only User A's notifications (never User B's)
- **Scenario 5**: Malformed request (invalid schema) → 400 Bad Request
- **Scenario 6**: Database error simulation → 500 Internal Server Error (no SQL details exposed)

## Compliance with Constitution

### Principle I: Domain-Led Modular Services ✅

Service method `NotificationService.sync(user: User, known_ids: list[UUID]) → list[Notification]` encapsulates filtering logic; route handler remains thin (parse → service call → respond).

### Principle II: Explicit API and Data Contracts ✅

Request and response schemas defined explicitly using Django Ninja; versioning approach documented.

### Principle III: Test Discipline & End-to-End Validation ✅

Both unit (service) and E2E (route) tests required; dual-layer verification prevents regressions.

### Principle IV: Clear Change Management ✅

No breaking changes; additive feature; no schema migrations; configurable constants (list limit) support future adjustments.

### Principle V: Simplicity & Maintainability ✅

Single query with Django ORM idioms; no raw SQL; filtering logic in one method; minimal code complexity.

## Summary: All Clarifications Resolved ✅

**No NEEDS CLARIFICATION markers remain from specification.**

All technology decisions are validated:
- ✅ Django ORM confirmed as filtering approach
- ✅ List limit (10,000) established and justified
- ✅ Response ordering and schema design finalized
- ✅ Authentication strategy aligned with project standards
- ✅ Performance targets are achievable
- ✅ Testing strategy covers required scenarios

**Phase 0 Complete**: Ready to proceed to Phase 1 (Design & Contracts).
