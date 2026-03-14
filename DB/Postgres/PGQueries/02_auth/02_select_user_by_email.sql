SELECT
    id,
    email,
    full_name,
    hashed_password,
    is_active,
    created_at,
    updated_at
FROM app_users
WHERE email = :email;
