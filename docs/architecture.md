# CampusCare AI - System Architecture

## 1. System overview

CampusCare AI is a full-stack student service management platform for complaint submission, AI-assisted classification, and administrator review.

The application consists of a React frontend, a FastAPI backend, and a PostgreSQL database. AI classification is integrated through the OpenAI Python SDK when an API key is configured.

## 2. Technology architecture

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React and JavaScript | Student and administrator interfaces for complaint management and AI-assisted workflows. |
| Frontend build tool | Vite | Frontend development server and production build. |
| Frontend routing | React Router | Client-side navigation between application views. |
| Frontend API client | Axios | HTTP communication with the FastAPI backend. |
| Frontend icons | Lucide React | Interface icons. |
| API | FastAPI | HTTP endpoints, request validation, dependency injection, and API documentation. |
| Application services | Python | Authentication, complaint workflows, AI review, rate limiting, and recovery orchestration. |
| Data access | Psycopg | PostgreSQL connections and SQL operations. |
| Database | PostgreSQL | Users, complaints, history, AI reviews, migration records, and login rate limits. |
| Authentication | JWT and Argon2 | Access-token validation and password hashing. |
| AI integration | OpenAI Python SDK | Structured complaint category and priority suggestions. |
| Background processing | FastAPI BackgroundTasks and recovery scheduler | Initial classification scheduling and recovery of stale attempts. |

### Application request flow

The React frontend communicates with the FastAPI backend through HTTP requests using Axios. The frontend API base URL is configured through `VITE_API_BASE_URL`. The backend validates requests, applies authentication and authorization rules, and executes application workflows using PostgreSQL. Backend CORS settings are controlled through `CORS_ALLOWED_ORIGINS` so configured frontend origins can access the API.

## 3. Backend module responsibilities

| Module | Responsibility |
|---|---|
| `app/main.py` | FastAPI application creation and lifespan management. |
| `app/api/` | HTTP route definitions. |
| `app/core/` | Application configuration and authentication dependencies. |
| `app/db/` | Database connection management. |
| `app/repositories/` | SQL queries and persistence operations. |
| `app/schemas/` | Request and response validation models. |
| `app/services/` | Business workflows and application services. |
| `app/services/ai/` | AI classification, background execution, metrics, and recovery. |
| `app/maintenance/` | Operational maintenance commands. |
| `backend/tests/` | Automated backend tests. |

## 4. Database architecture

The PostgreSQL database stores application users, student complaints, complaint status history, AI review decisions, migration history, and login rate-limit records.

### Database tables

| Table | Responsibility |
|---|---|
| `users` | Student and administrator accounts, roles, password hashes, and account status. |
| `complaints` | Complaint details, ownership, status, priority, and AI classification state. |
| `complaint_history` | Audit trail of complaint status changes. |
| `complaint_ai_reviews` | Administrator decisions and final AI classification review values. |
| `schema_migrations` | Applied database migration versions and descriptions. |
| `login_rate_limits` | Hashed identifiers and failed-login rate-limit state. |

### Entity relationships

- A user can submit multiple complaints.
- Each complaint belongs to one student through `student_id`.
- A complaint can optionally be assigned to an administrator through `assigned_admin_id`.
- A complaint can have multiple status-history records.
- A complaint can have multiple AI review audit records.
- Complaint history and AI review records reference the users who performed the actions.

### Database integrity

- Primary keys identify records.
- Foreign keys maintain relationships between users, complaints, history, and AI reviews.
- Unique constraints protect user email addresses and login rate-limit scope/identifier pairs.
- Check constraints validate roles, complaint statuses, priorities, AI confidence values, and review decisions.
- Complaint submission, status changes, and AI review persistence use database transactions.

### Schema and migrations

- Base schema: `database/schema.sql`.
- Incremental migrations: `database/migrations/`.
- Migration history is stored in `schema_migrations`.
- The repository does not currently document a verified automated migration runner.

## 5. AI classification lifecycle

### Initial classification flow

1. A student submits a complaint through the complaint API.
2. The complaint and initial history are persisted in a database transaction.
3. The complaint is marked for AI classification.
4. FastAPI schedules the classification task using BackgroundTasks.
5. The AI service obtains a configured OpenAI client.
6. The classifier requests a structured category, priority, confidence score, and explanation.
7. The classification result is persisted only when the processing attempt still owns the complaint.
8. If AI classification is not configured, the complaint classification can be marked `SKIPPED`.

### Classification states

| State | Meaning |
|---|---|
| `NOT_STARTED` | Classification has not started. |
| `PENDING` | Classification is waiting or currently being processed. |
| `COMPLETED` | Classification result was stored successfully. |
| `FAILED` | Classification attempt failed and requires recovery or has exhausted retries. |
| `SKIPPED` | Classification was intentionally not performed, such as when the AI provider is not configured. |

### Recovery and retry protection

- A recovery scheduler periodically searches for stale classification attempts.
- Stale records are claimed using database locking and `SKIP LOCKED`.
- Each claimed attempt receives a new UUID attempt identifier.
- Classification attempts are limited to five.
- Processing occurs after the claim transaction releases its database connection.
- Result updates verify the complaint ID, pending state, and attempt identifier.
- This ownership check prevents an older worker from overwriting a newer attempt.

### AI provider behavior

- AI classification uses structured responses validated against application schemas.
- Provider calls use a configured timeout and retry policy.
- Provider or validation failures are handled by the classification failure workflow.
- The model-generated confidence score is not statistically calibrated.
- AI output is a recommendation and does not replace administrator judgment.

## 6. Authentication and authorization

### Authentication flow

1. A student registers using the registration endpoint.
2. Passwords are hashed using Argon2 before database storage.
3. A registered user logs in using email and password.
4. Successful authentication returns a signed JWT access token.
5. Protected endpoints validate the bearer token and retrieve the current active user.
6. Invalid, expired, or inactive-user tokens are rejected.

### Role-based access control

| Role | Access |
|---|---|
| `STUDENT` | Own profile, complaint submission, own complaints, complaint details, and complaint history. |
| `ADMIN` | Administrative complaint management, status updates, AI review workflows, and AI operational metrics. |

### Authorization safeguards

- Role dependencies protect administrative endpoints.
- Students cannot access another student's complaint details or history.
- Unauthorized complaint ownership checks return `404` to avoid disclosing another user's records.
- Inactive accounts cannot authenticate through protected endpoints.
- Login attempts are rate-limited using hashed email/IP and IP identifiers.
- JWT signing configuration and rate-limit hashing secrets are supplied through environment variables.

## 7. Transaction and reliability boundaries

- Complaint creation and its initial history record are committed atomically.
- Complaint status updates and their history records are committed atomically.
- AI review decisions and corresponding complaint updates are committed atomically.
- Complaint status changes use row-level locking to protect concurrent updates.
- AI classification updates are guarded by attempt identifiers.
- Database connections are opened per operation; connection pooling is not currently implemented.
- The AI recovery scheduler runs within the FastAPI application lifecycle.

## 8. Current implementation boundaries

- The backend API and PostgreSQL integration are implemented.
- The React frontend is implemented and communicates with the backend REST API.
- Production deployment and cloud infrastructure are not yet configured.
- No external durable message broker or queue is currently implemented.
- No automated database migration runner is documented in the repository.
- Login rate-limit cleanup is available as a maintenance command; scheduled execution is not configured.
- AI classification depends on a configured external OpenAI API key.

## 9. Architecture evolution

Future architecture decisions will be based on measured application requirements, reliability needs, security reviews, and deployment constraints.

Potential future areas include automated migration execution, deployment automation, production monitoring, and load testing. These are future improvements, not current implemented components.


## 10. Production deployment requirements

The following are deployment requirements and recommendations. They do not indicate that production infrastructure has already been deployed.

### Application configuration

- Set `APP_ENV=production`.
- Configure `LOG_LEVEL` according to the operational logging policy.
- Set exact frontend origins through `CORS_ALLOWED_ORIGINS`.
- Supply database credentials, JWT signing secret, and rate-limit hashing secret through a secure environment configuration mechanism.
- Use separate, strong secrets for JWT signing and rate-limit hashing.
- Never commit `.env` files, credentials, or API keys.
- Keep API documentation disabled in production unless an explicit access policy is established.

### Application process and AI recovery

- Begin with one application worker because the AI recovery scheduler currently starts inside each FastAPI application process.
- Multiple application workers would start multiple recovery scheduler loops.
- Database locking and attempt ownership checks protect classification processing, but they do not replace an explicit scheduler deployment strategy.
- Before scaling application workers, move recovery scheduling into a dedicated process or introduce a separately controlled scheduler.
- Ensure graceful application shutdown allows background tasks to stop.

### Database operations

- Use a managed or otherwise reliably operated PostgreSQL deployment.
- Restrict database network access to authorized application infrastructure.
- Configure connection timeouts and monitor database availability.
- Apply schema migrations as a separate, controlled deployment operation.
- Verify backups and restoration procedures before production use.
- Do not run unverified migrations automatically during application startup.

### Network and monitoring

- Terminate HTTPS at a trusted reverse proxy or managed load balancer.
- Configure trusted proxy handling only for known proxy infrastructure.
- Monitor application errors, database connectivity, AI provider failures, and recovery processing.
- Use `GET /api/health/database` for database connectivity checks. It does not verify AI provider availability or complete application readiness.
- Protect operational logs and avoid recording credentials, tokens, or sensitive student information.

### Deployment status

Production hosting, cloud infrastructure, TLS configuration, automated deployment pipelines, production monitoring, and backup automation remain unimplemented until separately configured and verified.
