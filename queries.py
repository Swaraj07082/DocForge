CREATE_REPO_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS repos (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    repo_url VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255) NOT NULL,
    report_url TEXT,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT_REPO_QUERY = """
INSERT INTO repos (repo_url, file_path, thread_id, report_url, approved, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
