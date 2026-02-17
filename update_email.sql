-- ===============================
-- DATABASE SELECTION
-- ===============================
USE crop_system;

-- ===============================
-- CHECK USERS
-- ===============================
SELECT id, email, is_admin, password_hash
FROM users;

-- ===============================
-- UPDATE EMAIL (BY ID – SAFEST)
-- ===============================
UPDATE users
SET email = 'kushwahasanyam38@gmail.com'
WHERE id = 1;

-- ===============================
-- VERIFY EMAIL UPDATE
-- ===============================
SELECT id, email
FROM users;

-- ===============================
-- MAKE USER ADMIN
-- ===============================
UPDATE users
SET is_admin = 1
WHERE id = 1;

-- ===============================
-- VERIFY ADMIN STATUS
-- ===============================
SELECT id, email, is_admin
FROM users;

-- ===============================
-- RESET PASSWORD (PLAIN TEXT FOR PROJECT)
-- ===============================
UPDATE users
SET password_hash = 'NITROGEN35'
WHERE id = 1;

-- ===============================
-- FINAL VERIFICATION
-- ===============================
SELECT id, email, is_admin, password_hash
FROM users;
