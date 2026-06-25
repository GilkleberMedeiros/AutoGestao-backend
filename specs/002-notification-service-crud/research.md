# Research: Notification Service CRUD Operations

**Phase**: 0 (from `/speckit.plan`)  
**Created**: 2026-06-25  
**Input**: Specification requirements and existing codebase patterns

## Overview

No unresolved `[NEEDS CLARIFICATION]` markers exist in the specification. Research confirms technology choices and aligns implementation with established project service patterns (`MovGroupService`, `ProjectService`, `ClientService`).

## Technology Decisions

### Decision: Extend Existing NotificationService Class

**Resolution**: Add CRUD methods to `apps/notifications/services/notification.py` alongside the existing `sync()` method.

**Rationale**: Constitution Principle VI requires matching existing organization. The sync feature already introduced `NotificationService` in this file; splitting into multiple service classes would fragment the domain.

**Alternatives considered**:
- **Separate `NotificationCrudService`**: Extra indirection; breaks single-responsibility-per-domain-entity convention used elsewhere
- **Generic base CRUD mixin**: Over-abstraction; no other app uses this pattern

**Decision**: Single `NotificationService` class ✅

### Decision: Service Input Schemas (Ninja/Pydantic)

**Resolution**: Define `CreateNotificationReq` and `PartialUpdateNotificationReq` in `apps/notifications/schemas.py`, mirroring `CreateMovGroupReq` / `PartialUpdateMovGroupReq`.

**Rationale**: Typed inputs enable field validation at the schema layer; `partial_update` uses `model_dump(exclude_unset=True)` like `MovGroupService` and `ProjectService`.

**Alternatives considered**:
- **Plain `dict` parameters (ClientService style)**: Works but less type-safe; notifications have more fields and optional relation payload
- **Django forms**: Not used elsewhere for services in this project

**Decision**: Ninja schemas for create/partial_update ✅

### Decision: Error Handling

**Resolution**: `get`, `partial_update`, and `delete` raise `ResourceNotFoundError` when the notification is missing or belongs to another user (via `filter(user=user)`). Validation failures raise `BusinessRuleError` or `ValueError` for invalid type/relation combinations.

**Rationale**: `ProjectService.get()` and `MovGroupService.get()` raise `ResourceNotFoundError`; `ClientService.get()` returns `None` but update/delete raise — the raise-on-get pattern is more common in newer services.

**Alternatives considered**:
- **Return `None` from get**: Callers must null-check; inconsistent with `ProjectService`

**Decision**: Raise `ResourceNotFoundError` ✅

### Decision: User Model Import

**Resolution**: Use `apps.users.models.User` (project custom user), not `django.contrib.auth.models.User`.

**Rationale**: `Notification.user` FK points to `users.User`; existing sync tests already use `apps.users.models.User`. The current service file incorrectly imports Django auth `User` and should be corrected during implementation.

**Decision**: `apps.users.models.User` ✅

### Decision: NotificationRelation Management

**Resolution**: On `create`, optionally create a `NotificationRelation` row when relation input is provided. On `partial_update`, update relation only when relation fields are present in the payload (`update_or_create` on the reverse FK). On `delete`, rely on `CASCADE` from `Notification` → `NotificationRelation`.

**Rationale**: Mirrors `ClientService` nested create/update for related entities; avoids orphan relations.

**Alternatives considered**:
- **Ignore relations in CRUD**: Breaks ASSOCIATED/DEADLINE notification types
- **Always require relation for ASSOCIATED type**: Stricter validation — adopted as business rule in service helper

**Decision**: Optional relation on create; partial relation update; cascade delete ✅

### Decision: List Ordering and Prefetch

**Resolution**: `list(user)` returns `Notification.objects.filter(user=user).prefetch_related("notificationrelation_set").order_by("-deliver_at", "id")`.

**Rationale**: Matches `sync()` ordering for deterministic behavior (FR-005, SC-006). Prefetch avoids N+1 when callers access relations.

**Decision**: Same ordering as sync + prefetch ✅

### Decision: Transaction Boundaries

**Resolution**: Wrap `create` and `partial_update` (when relation changes) with `@transaction.atomic`.

**Rationale**: Consistent with `ClientService.create()` and `ClientService.partial_update()` when multiple tables are touched.

**Decision**: `@transaction.atomic` on multi-table writes ✅

### Decision: No Full Update Method

**Resolution**: Implement only `partial_update`; no `update` (full replace) method.

**Rationale**: Spec assumption explicitly excludes full update; reduces API surface.

**Decision**: `partial_update` only ✅

### Decision: Testing Strategy

**Resolution**: Unit tests only in `test/notifications/test_services.py`, using `TestNotificationService__<method>` class naming (matching `TestNotificationService__sync` and `TestAuthService__Login`).

**Rationale**: No HTTP routes in scope — E2E API tests not required. Constitution Principle III satisfied via service unit tests + sync regression.

**Decision**: Service unit tests only ✅

## Validation Rules Research

| Rule | Enforcement |
|------|-------------|
| Required fields on create (`title`, `deliver_at`, `type`) | `CreateNotificationReq` schema + model constraints |
| `type` in enum | Schema validator or service check against `Notification.NOTIFICATION_TYPE_CHOICES` |
| Relation consistency | Service helper: if `relation_type=PROJECT`, `project_id` required and owned by user |
| Empty partial update | No-op: return existing notification unchanged |
| User isolation | All queries filter `user=user` |

## Dependencies Confirmed

- Existing models: `Notification`, `NotificationRelation` (no migration)
- Existing exceptions: `ResourceNotFoundError`, `BusinessRuleError` from `apps.core.exceptions`
- Related entities: `Project`, `Client`, `Task` in `projects_and_clients` for relation ownership validation
- Sync feature (`001-notification-sync`): must remain regression-free

## Open Items

None. All technical context resolved.
