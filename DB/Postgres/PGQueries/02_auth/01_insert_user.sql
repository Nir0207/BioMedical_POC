INSERT INTO app_users (
    email,
    full_name,
    hashed_password,
    is_active
) VALUES (
    :email,
    :full_name,
    :hashed_password,
    TRUE
)
RETURNING id, email, full_name, is_active, created_at;
