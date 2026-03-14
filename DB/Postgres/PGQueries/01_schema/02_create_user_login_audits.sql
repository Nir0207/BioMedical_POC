CREATE TABLE IF NOT EXISTS user_login_audits (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    login_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_user_login_audits_user_id ON user_login_audits (user_id);
