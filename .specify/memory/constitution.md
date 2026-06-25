<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified principles: none renamed
Added principles: VI. Established Project Conventions (Golden Rule)
Added sections: none
Removed sections: none
Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check remains dynamic)
  - .specify/templates/spec-template.md ✅ aligned
  - .specify/templates/tasks-template.md ✅ updated (convention note in Path Conventions)
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

### VI. Established Project Conventions (Golden Rule)
New and changed code MUST follow patterns already established in this repository, with special attention to code organization. File layout, naming, layering (models, services, routes, schemas, tests), import style, test structure, and error-handling conventions MUST match neighboring modules and existing features unless an amendment to this constitution explicitly approves a different approach. This golden rule reduces fragmentation, speeds up reviews, and keeps the codebase coherent as it grows.

## Additional Constraints
The backend MUST use Django and Django Ninja conventions for configuration, routing, and schema definitions. Environment-sensitive values MUST be sourced from environment configuration, not hardcoded. Use the Django ORM for persistence and avoid raw SQL unless necessary for performance-critical cases.

## Development Workflow
Feature work MUST follow the documented architecture: models for data access, services for business logic, and routes for request/response coordination. Before introducing new abstractions or directory layouts, developers MUST inspect comparable features in the repository and align with their organization. Every PR MUST include updated tests for the affected feature area and documentation updates when API contracts or behavior change. Developers MUST run `uv run manage.py test` before merging.

## Governance
The constitution is authoritative for project architecture and quality decisions. Amendments require an explicit edit to this document, rationale for the change, and a review pass that verifies the updated governance is reflected in the implementation artifacts.

- Versioning follows semantic versioning: MAJOR for incompatible governance or principle changes, MINOR for new principles or material guidance additions, PATCH for clarifications.
- Every PR MUST identify the applicable constitution principles and provide a brief compliance note in the description.
- Quality gates include passing unit tests, end-to-end route tests, adherence to service-class separation, and demonstrable alignment with established project conventions.

**Version**: 1.1.0 | **Ratified**: 2026-06-25 | **Last Amended**: 2026-06-25
