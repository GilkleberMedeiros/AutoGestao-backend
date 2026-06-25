# Implementation Plan: Notification Service CRUD Operations

**Branch**: `002-notification-service-crud` | **Date**: 2026-06-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-notification-service-crud/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Extend `NotificationService` in the existing `notifications` Django app with CRUD operations (`create`, `get`, `list`, `partial_update`, `delete`) scoped per user, following the same service-layer patterns used by `MovGroupService`, `ProjectService`, and `ClientService`. Reuse existing `Notification` and `NotificationRelation` models without schema migrations. Add request schemas for typed create/partial-update inputs, unit tests under `test/notifications/`, and a documented service contract. The existing `sync()` method remains unchanged.

## Technical Context

**Language/Version**: Python 3.14 (project `requires-python >=3.14`)

**Primary Dependencies**: Django 6.x, Django ORM, Django Ninja schemas (for service input DTOs only — no new routes in this feature)

**Storage**: SQLite (dev) / PostgreSQL (production) — existing `notifications_notification` and `notifications_notificationrelation` tables

**Testing**: Django `TestCase` unit tests in `test/notifications/test_services.py`; existing sync tests must continue passing

**Target Platform**: Linux server (Django backend)

**Project Type**: Web service backend — service-layer feature (internal API for future routes and domain signals)

**Performance Goals**: Standard ORM CRUD latency; list ordering consistent with sync (`deliver_at DESC, id ASC`)

**Constraints**: User isolation on every operation; no new HTTP endpoints; no database migrations; `sync()` behavior unchanged

**Scale/Scope**: Single service class extension; 2 new schemas; ~5 service methods; unit tests only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Domain-Led Modular Services | ✅ PASS | Business logic in `NotificationService`; models unchanged; no route layer in this feature |
| II. Explicit API and Data Contracts | ⚠️ JUSTIFIED | No public HTTP endpoints (out of scope per spec). Service contract documented in `contracts/notification-service-crud-contract.md`; input DTOs via Ninja schemas |
| III. Test Discipline | ✅ PASS | Unit tests for all CRUD methods; regression coverage for existing `sync()` tests |
| IV. Clear Change Management | ✅ PASS | Additive only; no migrations; no breaking changes to sync |
| V. Simplicity | ✅ PASS | Django ORM idioms; mirrors `MovGroupService` patterns |
| VI. Established Conventions (Golden Rule) | ✅ PASS | Same file layout, naming (`TestNotificationService__*`), exceptions (`ResourceNotFoundError`), and service signatures as peer services |

**Pre-design gate**: ✅ PASSED (Principle II exception documented below)

## Constitution Check: Phase 1 Design Validation

*GATE: Re-check after Phase 1 design (FINAL VALIDATION)*

**Principle I** ✅ — Service methods delegate to ORM; relation side-effects encapsulated in service private helpers.

**Principle II** ✅ (justified) — Service contract + `CreateNotificationReq` / `PartialUpdateNotificationReq` schemas provide explicit interface documentation. HTTP routes deferred to follow-up feature.

**Principle III** ✅ — Unit test matrix defined in [quickstart.md](quickstart.md) covering create, get, list, partial_update, delete, user isolation, validation errors, and sync regression.

**Principle IV** ✅ — No schema changes; cascade delete on `NotificationRelation` handled by existing FK `on_delete=CASCADE`.

**Principle V** ✅ — No repository pattern; no raw SQL; validation helpers kept minimal.

**Principle VI** ✅ — Method signatures align with `MovGroupService` (`user` first param, `get` raises `ResourceNotFoundError`, `list` returns queryset, `partial_update` uses `model_dump(exclude_unset=True)`).

**Post-design gate**: ✅ PASSED

## Project Structure

### Documentation (this feature)

```text
specs/002-notification-service-crud/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── notification-service-crud-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
apps/notifications/
├── models.py                    # EXISTS — no changes
├── schemas.py                   # UPDATE — add CreateNotificationReq, PartialUpdateNotificationReq, RelationInputSchema
└── services/
    ├── __init__.py              # EXISTS
    └── notification.py          # UPDATE — add create, get, list, partial_update, delete (+ helpers)

test/notifications/
├── __init__.py                  # EXISTS
└── test_services.py             # UPDATE — add TestNotificationService__create/get/list/partial_update/delete
```

**Structure Decision**: All changes stay within the established `notifications` app and `test/notifications/` mirror used by the sync feature. No new directories, no route files, no API tests — consistent with spec scope and constitution Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle II: no HTTP contract | Spec explicitly limits scope to service layer; sync route already covers client-facing notification API | Adding routes now would expand scope beyond user request and duplicate future admin/client endpoints |
