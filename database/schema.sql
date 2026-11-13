CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    password_hash VARCHAR(255) NOT NULL,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('STUDENT', 'ADMIN')),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE complaints (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    student_id BIGINT NOT NULL
        REFERENCES users(id),

    assigned_admin_id BIGINT
        REFERENCES users(id),

    title VARCHAR(200) NOT NULL,

    description TEXT NOT NULL,

    category VARCHAR(50),

    ai_suggested_category VARCHAR(50),

    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),

    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),

    ai_confidence NUMERIC(5,4)
        CHECK (ai_confidence IS NULL OR ai_confidence BETWEEN 0 AND 1),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_complaints_student_id
    ON complaints(student_id);

CREATE INDEX idx_complaints_assigned_admin_id
    ON complaints(assigned_admin_id);

CREATE INDEX idx_complaints_status
    ON complaints(status);


CREATE TABLE complaint_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(id),

    changed_by BIGINT NOT NULL
        REFERENCES users(id),

    old_status VARCHAR(20),

    new_status VARCHAR(20) NOT NULL
        CHECK (new_status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),

    remarks TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_complaint_history_complaint_id
    ON complaint_history(complaint_id);

CREATE INDEX idx_complaint_history_changed_by
    ON complaint_history(changed_by);
