<!--
Sync Impact Report
Version change: none → 1.0.0
Added principles: Domain-Led Modular Services; Explicit API and Data Contracts; Test Discipline and End-to-End Validation; Clear Change Management; Simplicity, Maintainability, and Developer Productivity
Added sections: Additional Constraints; Development Workflow
Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned
  - .specify/templates/spec-template.md ✅ aligned
  - .specify/templates/tasks-template.md ✅ aligned
Follow-up TODOs: none
-->

# AutoGestão Constitution

## Core Principles

### I. Domain-Led Modular Services
The codebase MUST be organized by Django app and feature domain. Models retrieve persisted state, service classes execute business rules, and routes orchestrate request handling. This separation prevents fat controllers, keeps business logic reusable, and preserves the established project workflow.

### II. Explicit API and Data Contracts
Every public endpoint MUST define explicit request and response schemas using Django Ninja or documented serializers. API contracts MUST be versioned, documented, and stable for mobile and frontend consumers. This reduces integration risk and keeps the backend dependable for client-driven releases.

### III. Test Discipline and End-to-End Validation
Isolated unit tests MUST cover service classes and business logic. End-to-end API tests MUST validate public routes and user-facing behavior. This dual layer of verification protects contract integrity and ensures changes do not break the mobile/client experience.

### IV. Clear Change Management
Breaking changes MUST be documented, reviewed, and migrated consciously. Database schema changes MUST use Django migrations, and compatibility risk MUST be evaluated before deployment. This discipline preserves production stability and enables safe evolution for a nearly complete backend.

### V. Simplicity, Maintainability, and Developer Productivity
Code MUST favor readability, minimal complexity, and built-in Django/Django Ninja patterns over premature optimization. Duplicate persistence logic MUST be avoided, and service methods MUST be concise and explicit. This principle keeps the project maintainable as development completes.

## Additional Constraints
The backend MUST use Django and Django Ninja conventions for configuration, routing, and schema definitions. Environment-sensitive values MUST be sourced from environment configuration, not hardcoded. Use the Django ORM for persistence and avoid raw SQL unless necessary for performance-critical cases.

## Development Workflow
Feature work MUST follow the documented architecture: models for data access, services for business logic, and routes for request/response coordination. Every PR MUST include updated tests for the affected feature area and documentation updates when API contracts or behavior change. Developers MUST run `uv run manage.py test` before merging.

## Governance
The constitution is authoritative for project architecture and quality decisions. Amendments require an explicit edit to this document, rationale for the change, and a review pass that verifies the updated governance is reflected in the implementation artifacts.

- Versioning follows semantic versioning: MAJOR for incompatible governance or principle changes, MINOR for new principles or material guidance additions, PATCH for clarifications.
- Every PR MUST identify the applicable constitution principles and provide a brief compliance note in the description.
- Quality gates include passing unit tests, end-to-end route tests, and adherence to service-class separation.

**Version**: 1.0.0 | **Ratified**: 2026-06-25 | **Last Amended**: 2026-06-25
