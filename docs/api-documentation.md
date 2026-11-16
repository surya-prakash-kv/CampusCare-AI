# CampusCare AI - API Documentation

## Overview

CampusCare AI exposes REST APIs through a FastAPI backend.

Base URL for local development: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

OpenAPI specification: `http://127.0.0.1:8000/openapi.json`

## Authentication

- Public endpoints do not require authentication.
- Protected endpoints require a valid JWT bearer access token.
- Send protected requests using the `Authorization: Bearer <access_token>` header.
- Inactive users and invalid or expired tokens are rejected.

## Authorization roles

| Role | Access |
|---|---|
| STUDENT | Student registration, profile, complaint submission, and access to their own complaints and history. |
| ADMIN | Administrative complaint operations, AI review, and AI operational metrics. |

## Common HTTP status codes

| Status | Meaning |
|---|---|
| 200 | Request completed successfully. |
| 201 | Resource created successfully. |
| 401 | Authentication is missing or invalid. |
| 403 | Authenticated user does not have the required role. |
| 404 | Requested resource was not found or is not accessible to the student. |
| 409 | Request conflicts with the current resource state. |
| 422 | Request validation failed. |
| 429 | Login rate limit exceeded. |
| 503 | Required service or database operation is unavailable. |

## 1. Health

### GET `/`

- Access: Public
- Purpose: Root endpoint.

### GET `/api/health/database`

- Access: Public
- Purpose: Checks PostgreSQL connectivity using `SELECT 1`.
- Success: `200 OK` when the database responds.
- Failure: `503 Service Unavailable` when the database check fails.
- Note: This endpoint checks database connectivity, not the health of the AI provider or the entire application.

## 2. Authentication

### POST `/api/auth/register`

- Access: Public
- Content-Type: `application/json`
- Purpose: Registers a student account.
- Success: `201 Created`.
- Conflict: `409 Conflict` when the email is already registered.
- Validation: Full name, email, and password are validated.

### POST `/api/auth/login`

- Access: Public
- Content-Type: `application/x-www-form-urlencoded`
- Request fields: `username` (email) and `password`.
- Purpose: Authenticates a student and returns a JWT access token.
- Success: `200 OK`.
- Invalid credentials: `401 Unauthorized`.
- Rate limit exceeded: `429 Too Many Requests`, with a `Retry-After` header.
- Rate-limit storage or client IP failure: may return `503 Service Unavailable`.

### GET `/api/auth/me`

- Access: STUDENT
- Purpose: Returns the authenticated student profile.
- Authentication: JWT bearer token required.

## 3. Complaint management

### POST `/api/complaints`

- Access: STUDENT
- Content-Type: `application/json`
- Purpose: Submits a new complaint.
- Success: `201 Created`.
- Processing: Complaint creation and initial history are persisted transactionally. AI classification is scheduled as a background task.

### GET `/api/complaints/my`

- Access: STUDENT
- Purpose: Lists complaints belonging to the authenticated student.

### GET `/api/complaints/{complaint_id}`

- Access: STUDENT or ADMIN
- Purpose: Retrieves complaint details.
- Ownership: Students can retrieve only their own complaints. Administrators can retrieve complaints across students.
- Not found or inaccessible: `404 Not Found`.

### GET `/api/complaints/admin/all`

- Access: ADMIN
- Purpose: Lists complaints for administrative management.

### PATCH `/api/complaints/admin/{complaint_id}/status`

- Access: ADMIN
- Content-Type: `application/json`
- Purpose: Updates a complaint status and records the status change in complaint history.
- Processing: Status update and history insertion are transactional.
- Invalid status transition: `409 Conflict`.
- Missing complaint: `404 Not Found`.

### GET `/api/complaints/{complaint_id}/history`

- Access: STUDENT or ADMIN
- Purpose: Retrieves complaint status history.
- Ownership: Students can access history only for their own complaints.
- Not found or inaccessible: `404 Not Found`.

## 4. Administrative AI review

### GET `/api/complaints/admin/ai-review/pending`

- Access: ADMIN
- Purpose: Lists completed AI classifications awaiting administrative review.

### GET `/api/complaints/admin/{complaint_id}/ai-review/history`

- Access: ADMIN
- Purpose: Retrieves the review audit history for a complaint.

### POST `/api/complaints/admin/{complaint_id}/ai-review`

- Access: ADMIN
- Content-Type: `application/json`
- Purpose: Records an administrative decision about an AI classification.
- Supported decisions: `ACCEPTED`, `REJECTED`, and `MODIFIED`.
- For `MODIFIED`, both final category and final priority are required.
- For `ACCEPTED` or `REJECTED`, final category and priority must not be supplied.
- Success: `201 Created`.
- Invalid review or resource state: `409 Conflict`.

## 5. AI operational metrics

### GET `/api/admin/ai-operations/metrics`

- Access: ADMIN
- Purpose: Returns AI classification workload and operational metrics.
- Metrics include total complaints, classification status counts, oldest pending age, and attempt distribution.
- Processing status values: `HEALTHY`, `PROCESSING`, `IDLE`, and `DEGRADED`.
- Note: Processing status describes classification workload state, not overall infrastructure health.

## Additional notes

- Complaint categories and priorities are validated by the API schemas.
- AI classification suggestions are subject to administrative review.
- The AI confidence value is a model-reported score and should not be treated as a statistically calibrated probability.
- Request and response schemas are available in the running application OpenAPI specification.
