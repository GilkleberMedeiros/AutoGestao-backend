---
description: "Implementation tasks for Notification Synchronization Endpoint (001)"
---

# Tasks: Notification Synchronization Endpoint

**Input**: Design documents from `/specs/001-notification-sync/`

**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

**Tests**: Included. Required by specification success criteria (SC-005) and constitution principle III.

**Organization**: Tasks organized by user story to enable independent implementation and testing of each feature increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

**Single Django app structure**:
- `apps/notifications/` — existing app directory
- `test/` — test root directory
- Paths shown below follow this convention

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create file structure and project setup

- [ ] T001 Create NotificationService class file at `apps/notifications/services/notification.py`
- [ ] T002 Create sync route handler file at `apps/notifications/routes/sync.py`
- [ ] T003 Initialize `__init__.py` files: `apps/notifications/services/__init__.py`, `apps/notifications/routes/__init__.py`

---

## Phase 2: Foundational (Schemas & Base Service)

**Purpose**: Define contracts and base service structure; MUST complete before any user story can begin

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create schema definitions in `apps/notifications/schemas.py`: `SyncRequestSchema`, `SyncResponseSchema`, `RelationDTO` with full field validation per [contracts/notification-sync-contract.md](contracts/notification-sync-contract.md)
- [ ] T005 [P] Create NotificationService class stub in `apps/notifications/services/notification.py` with method signature `sync(user: User, known_ids: list[UUID]) → list[dict]`
- [ ] T006 [P] Create test structure: `test/notifications/__init__.py` and `test/api/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Client Syncs with Known Notifications (Priority: P1) 🎯 MVP

**Goal**: Implement core filtering logic and route handler that excludes known notification IDs

**Independent Test**: Can be fully tested by calling `/notifications/sync` with a populated `known_notification_ids` list and verifying: (1) returned notifications exclude all known IDs, (2) ordering is deterministic, (3) response schema matches contract

### Implementation for User Story 1

- [ ] T007 [US1] Implement NotificationService.sync() filtering logic in `apps/notifications/services/notification.py`: accept `user` and `known_ids` (list of UUIDs), return queryset filtered with `exclude(id__in=known_ids).order_by('-deliver_at', 'id').select_related('notificationrelation')`
- [ ] T008 [US1] Implement `apps/notifications/routes/sync.py` route handler: POST `/notifications/sync`, parse SyncRequestSchema, call NotificationService.sync(), serialize to SyncResponseSchema
- [ ] T009 [US1] Add authentication check to route handler: require `request.user` to be authenticated; return 401 Unauthorized if missing
- [ ] T010 [US1] Add UUID validation in schema/handler: validate each UUID in `known_notification_ids` against UUID v4 regex; return 400 Bad Request on invalid format with clear error message
- [ ] T011 [US1] Add list size validation: reject requests with `known_notification_ids` > 10,000; return 400 Bad Request with "maximum exceeded" error
- [ ] T012 [US1] Add user isolation in service: filter notifications by `user=request.user` to ensure no cross-user leakage
- [ ] T013 [US1] Add response serialization: convert Notification queryset to SyncResponseSchema with all fields (id, title, message, read, deliver_at, type, extra_fields, relation object if exists)
- [ ] T014 [US1] Handle NotificationRelation serialization: include nested `relation` object with relation_type and appropriate (project_id|client_id|task_id); null if no relation exists

### Tests for User Story 1

- [ ] T015 [P] [US1] Unit test: `test/notifications/test_services.py` — test NotificationService.sync() with 5 notifications: client knows 2, verify exactly 3 returned (not the known 2)
- [ ] T016 [P] [US1] Unit test: `test/notifications/test_services.py` — test ordering: verify notifications returned in descending order by deliver_at
- [ ] T017 [P] [US1] Unit test: `test/notifications/test_services.py` — test empty known_ids list: verify all notifications returned
- [ ] T018 [P] [US1] Unit test: `test/notifications/test_services.py` — test invalid UUIDs in known_ids: verify safely ignored (no exception, filtering still works)
- [ ] T019 [P] [US1] Unit test: `test/notifications/test_services.py` — test max size validation: verify request with 10,001 UUIDs triggers validation error
- [ ] T020 [P] [US1] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync with 3 known IDs from 5 total: verify 2 new notifications returned, known ones excluded
- [ ] T021 [P] [US1] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync verifies response schema matches contract: all required fields present, types correct
- [ ] T022 [P] [US1] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync with relation: verify nested relation object correctly populated with relation_type and appropriate entity IDs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently; filtering logic works correctly for known IDs

---

## Phase 4: User Story 2 - Client Syncs Without Prior Knowledge (Priority: P2)

**Goal**: Verify bootstrap sync (empty known_ids list) returns all notifications with consistent ordering

**Independent Test**: Can be tested by calling `/notifications/sync` with empty or absent `known_notification_ids` and verifying all user notifications returned in deterministic order

### Tests for User Story 2

- [ ] T023 [P] [US2] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync with empty known_notification_ids: verify all user notifications returned
- [ ] T024 [P] [US2] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync with omitted known_notification_ids field: verify empty list treated as default, all notifications returned
- [ ] T025 [P] [US2] E2E test: `test/api/test_notification_sync.py` — POST /notifications/sync: call twice in succession, verify same notifications returned in same order (deterministic)
- [ ] T026 [P] [US2] E2E test: `test/api/test_notification_sync.py` — bootstrap scenario: fresh user with no prior sync, call /notifications/sync, verify full notification history populated in response

**Checkpoint**: User Story 2 functionality verified; bootstrap sync returns complete and ordered notification set

---

## Phase 5: User Story 3 - Error Handling and Security (Priority: P3)

**Goal**: Comprehensive error handling, validation, and security isolation

**Independent Test**: Can be tested by: (1) calling without auth → 401, (2) sending malformed requests → 400, (3) cross-user access attempts → verified user isolation

### Tests for User Story 3

- [ ] T027 [P] [US3] E2E test: `test/api/test_notification_sync.py` — unauthenticated request (no token/session): POST /notifications/sync returns 401 Unauthorized with error message
- [ ] T028 [P] [US3] E2E test: `test/api/test_notification_sync.py` — invalid UUID format: POST /notifications/sync with known_notification_ids=["not-a-uuid"]: returns 400 Bad Request with validation error message
- [ ] T029 [P] [US3] E2E test: `test/api/test_notification_sync.py` — malformed UUID variants: UUID too short, UUID with typo, null UUID, UUID spelled wrong: all return 400 Bad Request
- [ ] T030 [P] [US3] E2E test: `test/api/test_notification_sync.py` — oversized list: POST /notifications/sync with 10,001 UUIDs: returns 400 Bad Request, message includes size limit
- [ ] T031 [P] [US3] E2E test: `test/api/test_notification_sync.py` — user isolation: User A with 3 notifications, User B with 3 notifications: User A auth calls endpoint, verify only User A's 3 returned, never User B's
- [ ] T032 [P] [US3] E2E test: `test/api/test_notification_sync.py` — cross-user known_ids: User A tries to hide User B's notification IDs in known_notification_ids: verified User A sees only their own notifications (User B's are ignored safely)
- [ ] T033 [P] [US3] E2E test: `test/api/test_notification_sync.py` — malformed JSON payload: send invalid JSON (trailing comma, unquoted keys): returns 400 Bad Request
- [ ] T034 [P] [US3] Unit test: `test/notifications/test_services.py` — database error handling: mock database exception, verify service method raises or handles gracefully; route handler returns 500 with generic error message (no SQL details exposed)
- [ ] T035 [P] [US3] E2E test: `test/api/test_notification_sync.py` — deleted notification scenario: notification exists, then deleted, next sync request: notification correctly absent from response (no error, no stale reference)

**Checkpoint**: All error paths covered; security isolation verified; user data not leaking across boundaries

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, optimization, and documentation

- [ ] T036 [P] Database index verification: confirm PostgreSQL indexes exist or are created on (user_id, deliver_at DESC) and (user_id, id) for query performance
- [ ] T037 Run full test suite: `uv run manage.py test test.api.test_notification_sync test.notifications.test_services` — verify 100% code coverage for sync logic
- [ ] T038 Performance validation: execute sync endpoint with 1,000 notifications and 500 known IDs; measure P95 response time; confirm < 500ms per specification SC-001
- [ ] T039 API documentation: add endpoint documentation to `docs/api_contract.md` or project API docs referencing [contracts/notification-sync-contract.md](contracts/notification-sync-contract.md)
- [ ] T040 Quickstart validation: run all 7 scenarios from [quickstart.md](quickstart.md) manually; verify endpoint behavior matches expected outcomes
- [ ] T041 Code review: peer review of NotificationService.sync(), route handler, and schemas for compliance with project constitution principles (Domain-Led Modular Services, Explicit Contracts, Test Discipline, Simple Code)

**Checkpoint**: Feature complete, tested, documented, and production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - core implementation
- **User Story 2 (Phase 4)**: Depends on US1 completion - additional test coverage
- **User Story 3 (Phase 5)**: Depends on US1 completion - error/security validation
- **Polish (Phase 6)**: Depends on all user stories complete

### Within Each User Story

- Implementation tasks (T007–T014) before tests (T015–T022)
- Tests should be written first (TDD), fail, then implementation makes them pass
- For US2 and US3: tests can start immediately after Phase 2 (Foundational)

### Parallel Opportunities

**Phase 1**:
- All T001–T003 can run in parallel (separate files, no dependencies)

**Phase 2**:
- T004, T005, T006 marked [P] can run in parallel (separate concerns: schemas, service stub, test structure)

**Phase 3 (US1)**:
- T007–T014 (implementation) are sequential; service method first, then route handler uses it
- T015–T022 (tests) marked [P] can run in parallel (unit tests independent of E2E tests, multiple E2E scenarios)

**Phase 4 (US2)** & **Phase 5 (US3)**:
- All tests marked [P] can run in parallel across both phases (E2E tests independent, separate scenarios)

**Phase 6**:
- T036, T037, T038, T039, T040, T041 should be sequential (validation → documentation → review)

### Parallel Example: Complete Phase 3 & 4 & 5 Tests in Parallel

Once Phase 2 (Foundational) and Phase 3 (US1 Implementation) complete, all test tasks can execute in parallel:
```
Task T015–T022 (US1 tests) in parallel
  + Task T023–T026 (US2 tests) in parallel
  + Task T027–T035 (US3 tests) in parallel
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

1. Complete Phase 1: Setup ✅
2. Complete Phase 2: Foundational ✅
3. Complete Phase 3: User Story 1 (core filtering, route, basic tests) ✅
4. **STOP and VALIDATE**: Test US1 independently; user can call `/notifications/sync` with known IDs and get filtered results

**MVP Deliverable**: Working endpoint that filters known notifications; meets US1 requirements and SC-002 (filtering accuracy)

### Post-MVP Phases

5. Complete Phase 4: User Story 2 (bootstrap sync tests)
6. Complete Phase 5: User Story 3 (error handling, security)
7. Complete Phase 6: Polish, documentation, full validation

### Suggested Task Assignment (if team available)

- **Developer 1**: Phase 1 + Phase 2 + Phase 3 Implementation (T001–T014)
- **Developer 2**: Phase 3 Tests (T015–T022) while Dev1 implements
- **Developer 3**: Phase 4 & 5 Tests (T023–T035) once Phase 2 complete
- **All**: Phase 6 (final validation, review)

---

## Success Criteria (from Specification)

All tasks complete when:

- [ ] SC-001: Endpoint responds in <500ms P95 for 1,000 notifications (T038)
- [ ] SC-002: Filtering excludes 100% of known IDs (T015, T020)
- [ ] SC-003: All new notifications appear in response (T017, T023)
- [ ] SC-004: Response payload minimized when filtering (T020)
- [ ] SC-005: 100% code coverage for unit + E2E tests (T037)
- [ ] SC-006: Security verified—no auth bypass, no cross-user leakage (T031, T032, T027)

---

## Constitutional Compliance (from `.specify/memory/constitution.md`)

Each task follows project principles:

- **Principle I — Domain-Led Modular Services**: Service encapsulates sync logic (T007); route delegates to service (T008); no fat controllers
- **Principle II — Explicit API and Data Contracts**: Schemas defined, versioned in contract (T004); no implicit formats
- **Principle III — Test Discipline**: Unit tests (T015–T019, T034) + E2E tests (T020–T035); 100% coverage required (T037)
- **Principle IV — Clear Change Management**: Additive feature; no schema migrations; configurable constants (list limit)
- **Principle V — Simplicity, Maintainability**: Idiomatic Django ORM (filter, exclude, select_related); no raw SQL; maintainable service method

---

## Rollback Plan (if task fails validation)

1. Review failed task against [contracts/notification-sync-contract.md](contracts/notification-sync-contract.md)
2. Check test output against [quickstart.md](quickstart.md) validation scenarios
3. Identify implementation gap (service logic, schema, or route handler)
4. Fix code and re-run specific task tests
5. Once task passes, continue to next task
6. If Phase fails, document blocker and escalate for review

---

**Ready for implementation**: All tasks are specific enough that an LLM can complete each one without additional context. Each task has clear deliverables, file paths, and acceptance criteria tied to specification and contract requirements.

**Next Steps**: 
1. Assign tasks to team members
2. Start Phase 1: Setup
3. Complete Phase 2: Foundational (prerequisite gate)
4. Proceed with Phases 3–6 in order or in parallel per "Parallel Opportunities" section above
