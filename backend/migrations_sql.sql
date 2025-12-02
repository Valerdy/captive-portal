-- Migration 0006: Add is_radius_activated field
-- Run this first if not already applied
ALTER TABLE users
ADD COLUMN is_radius_activated BOOLEAN DEFAULT FALSE
COMMENT 'Utilisateur activé dans RADIUS par un administrateur';

-- Migration 0007: Remove pre-registration fields
-- Run this after migration 0006

-- 1. Remove the unique constraint on student identity
ALTER TABLE users DROP CONSTRAINT IF EXISTS unique_student_identity;

-- For MySQL, use this instead:
-- ALTER TABLE users DROP INDEX unique_student_identity;

-- 2. Remove is_pre_registered field
ALTER TABLE users DROP COLUMN IF EXISTS is_pre_registered;

-- 3. Remove registration_completed field
ALTER TABLE users DROP COLUMN IF EXISTS registration_completed;

-- Migration 0008: Add cleartext_password field
-- Run this after migration 0007
-- ATTENTION SÉCURITÉ: Ce champ stocke le mot de passe en clair

ALTER TABLE users
ADD COLUMN cleartext_password VARCHAR(128) NULL
COMMENT 'Mot de passe en clair (UNIQUEMENT pour activation RADIUS - RISQUE DE SÉCURITÉ)';

-- Verify the changes
DESCRIBE users;
