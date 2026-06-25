---
description: "Implementation tasks for Notification Service CRUD Operations (002)"
---

# Tasks: Notification Service CRUD Operations

**Input**: Design documents from `/specs/002-notification-service-crud/`

**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

**Tests**: Included. Required by specification success criteria (SC-001–SC-006) and constitution principle III.

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Path Conventions

**AutoGestão backend** (per plan.md and constitution Principle VI):

- `apps/notifications/services/notification.py` — service layer
- `apps/notifications/schemas.py` — input DTOs
- `test/notifications/test_services.py` — unit tests (`TestNotificationService__*`)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Confirm existing structure; no new directories required

- [x] T001 Verify feature file targets exist per plan.md: `apps/notifications/services/notification.py`, `apps/notifications/schemas.py`, `test/notifications/test_services.py`

---

## Phase 2: Foundational (Schemas & Service Helpers)

**Purpose**: Input schemas and shared validation helpers; MUST complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Add `RelationInputSchema` and `CreateNotificationReq` in `apps/notifications/schemas.py` per [contracts/notification-service-crud-contract.md](contracts/notification-service-crud-contract.md)
- [x] T003 [P] Add `PartialUpdateNotificationReq` in `apps/notifications/schemas.py` per [contracts/notification-service-crud-contract.md](contracts/notification-service-crud-contract.md)
- [x] T004 Fix `User` import to `apps.users.models.User` in `apps/notifications/services/notification.py` (replace `django.contrib.auth.models.User`)
- [x] T005 Add private validation helpers in `apps/notifications/services/notification.py`: `_validate_notification_type`, `_validate_and_resolve_relation`, `_create_relation`, `_update_relation` per [data-model.md](data-model.md) validation rules

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 - Create Notifications (Priority: P1) 🎯 MVP

**Goal**: Persist new notifications for a user with optional relation and metadata

**Independent Test**: Create a notification for a known user; verify persisted fields and user ownership via subsequent `get`

### Implementation for User Story 1

- [x] T006 [US1] Implement `NotificationService.create(user, data: CreateNotificationReq)` in `apps/notifications/services/notification.py` with `@transaction.atomic`, optional `NotificationRelation` creation, and user-scoped relation ownership checks

### Tests for User Story 1

- [x] T007 [P] [US1] Add `TestNotificationService__create` in `test/notifications/test_services.py`: success with required fields, default `read=False`
- [x] T008 [P] [US1] Unit test in `test/notifications/test_services.py`: create with `ASSOCIATED` type and project relation persists `NotificationRelation`
- [x] T009 [P] [US1] Unit test in `test/notifications/test_services.py`: create rejects invalid type or missing relation target with validation error

**Checkpoint**: User Story 1 independently testable via `create` + direct ORM assertion

---

## Phase 4: User Story 2 - Retrieve Single Notification (Priority: P1)

**Goal**: Fetch one notification by ID scoped to owning user

**Independent Test**: Create notification, call `get` for owner → success; other user or missing ID → `ResourceNotFoundError`

### Implementation for User Story 2

- [x] T010 [US2] Implement `NotificationService.get(user, notification_id: str)` in `apps/notifications/services/notification.py` raising `ResourceNotFoundError` when missing or cross-user

### Tests for User Story 2

- [x] T011 [P] [US2] Add `TestNotificationService__get` in `test/notifications/test_services.py`: success returns all fields, not-found raises, user isolation raises

**Checkpoint**: User Stories 1 + 2 deliver create-and-read MVP

---

## Phase 5: User Story 3 - List Notifications (Priority: P2)

**Goal**: Return all user notifications ordered `deliver_at DESC, id ASC`

**Independent Test**: Create multiple notifications; `list(user)` returns correct count, order, and isolation

### Implementation for User Story 3

- [x] T012 [US3] Implement `NotificationService.list(user)` in `apps/notifications/services/notification.py` with `prefetch_related("notificationrelation_set").order_by("-deliver_at", "id")`

### Tests for User Story 3

- [x] T013 [P] [US3] Add `TestNotificationService__list` in `test/notifications/test_services.py`: ordering, empty list, user isolation

**Checkpoint**: User Story 3 independently testable

---

## Phase 6: User Story 4 - Partial Update (Priority: P2)

**Goal**: Update only supplied fields; support mark-as-read and relation updates

**Independent Test**: Partial update one field; verify others unchanged; empty payload is no-op

### Implementation for User Story 4

- [x] T014 [US4] Implement `NotificationService.partial_update(user, notification_id, data: PartialUpdateNotificationReq)` in `apps/notifications/services/notification.py` using `model_dump(exclude_unset=True)`, `@transaction.atomic` for relation changes

### Tests for User Story 4

- [x] T015 [P] [US4] Add `TestNotificationService__partial_update` in `test/notifications/test_services.py`: mark read only, relation update, empty payload no-op, not-found, invalid type

**Checkpoint**: User Story 4 independently testable

---

## Phase 7: User Story 5 - Delete Notification (Priority: P3)

**Goal**: Permanently remove notification and cascade relation

**Independent Test**: Delete notification; `get` raises; `list` count decreases; relation row removed

### Implementation for User Story 5

- [x] T016 [US5] Implement `NotificationService.delete(user, notification_id: str)` in `apps/notifications/services/notification.py` returning `{"success": True}` per contract (mirror `MovGroupService.delete`)

### Tests for User Story 5

- [x] T017 [P] [US5] Add `TestNotificationService__delete` in `test/notifications/test_services.py`: success, relation cascade, not-found, user isolation

**Checkpoint**: All CRUD operations complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Regression validation and contract compliance

- [x] T018 Run sync regression tests: `uv run manage.py test test.notifications.test_services.TestNotificationService__sync -v 2`
- [x] T019 Run full notification test suite per [quickstart.md](quickstart.md): `uv run manage.py test test.notifications.test_services test.api.test_notification_sync -v 2`
- [x] T020 [P] Verify method signatures and error behavior match [contracts/notification-service-crud-contract.md](contracts/notification-service-crud-contract.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user stories**
- **Phase 3 (US1 Create)**: Depends on Phase 2
- **Phase 4 (US2 Get)**: Depends on Phase 2; tests may use `create` or `setUp` fixtures
- **Phase 5 (US3 List)**: Depends on Phase 2; independent of US2 implementation
- **Phase 6 (US4 Partial Update)**: Depends on Phase 2; benefits from US1/US2 for test fixtures
- **Phase 7 (US5 Delete)**: Depends on Phase 2; benefits from US1/US2 for test fixtures
- **Phase 8 (Polish)**: Depends on all user story phases complete

### User Story Dependencies

```text
Phase 2 (Foundational)
    ├── US1 Create (P1) ──► MVP
    ├── US2 Get (P1)    ──► extends MVP
    ├── US3 List (P2)   ──► independent after Phase 2
    ├── US4 Partial Update (P2) ──► independent after Phase 2
    └── US5 Delete (P3) ──► independent after Phase 2
```

### Within Each User Story

- Implementation task before tests for that story (tests may be written to fail first if preferred)
- Service methods accumulate in the same file `apps/notifications/services/notification.py`

### Parallel Opportunities

- **Phase 2**: T002 and T003 (schemas) in parallel
- **Per story**: Implementation + test tasks marked [P] can run in parallel after implementation lands
- **Phase 8**: T020 can run in parallel with T018/T019

---

## Parallel Example: User Story 1

```bash
# After T006 completes, run in parallel:
Task T007: "Unit test create success in test/notifications/test_services.py"
Task T008: "Unit test create with relation in test/notifications/test_services.py"
Task T009: "Unit test create validation errors in test/notifications/test_services.py"
```

## Parallel Example: Foundational

```bash
# Run together:
Task T002: "Add CreateNotificationReq in apps/notifications/schemas.py"
Task T003: "Add PartialUpdateNotificationReq in apps/notifications/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1 + Phase 2
2. Implement US1 `create` + tests (T006–T009)
3. Implement US2 `get` + tests (T010–T011)
4. **STOP and VALIDATE**: create → get flow works with user isolation

### Incremental Delivery

1. US1 + US2 → create/read MVP
2. US3 → listing for notification centers
3. US4 → mark-as-read and content corrections
4. US5 → dismissal and cleanup
5. Phase 8 → sync regression (SC-006)

### Suggested MVP Scope

**User Story 1 (Create) + User Story 2 (Get)** — minimum viable service layer for notification lifecycle entry and retrieval.

---

## Task Summary

| Phase | Story | Tasks | Task IDs |
|-------|-------|-------|----------|
| Setup | — | 1 | T001 |
| Foundational | — | 4 | T002–T005 |
| US1 Create | P1 | 4 | T006–T009 |
| US2 Get | P1 | 2 | T010–T011 |
| US3 List | P2 | 2 | T012–T013 |
| US4 Partial Update | P2 | 2 | T014–T015 |
| US5 Delete | P3 | 2 | T016–T017 |
| Polish | — | 3 | T018–T020 |
| **Total** | | **20** | T001–T020 |

---

## Notes

- No HTTP routes in this feature — service layer only
- No database migrations — reuse existing models
- Do not modify `NotificationService.sync()` behavior except fixing `User` import
- Follow `MovGroupService` / `ProjectService` patterns for method signatures and exceptions
- Test class naming: `TestNotificationService__create`, `TestNotificationService__get`, etc.
