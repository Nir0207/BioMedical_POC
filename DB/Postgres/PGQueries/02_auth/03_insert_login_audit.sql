INSERT INTO user_login_audits (
    user_id,
    success,
    ip_address
) VALUES (
    :user_id,
    :success,
    :ip_address
)
RETURNING id, user_id, login_at, success, ip_address;
