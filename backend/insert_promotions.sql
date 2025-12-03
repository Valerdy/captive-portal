-- Script SQL pour insérer les promotions par défaut dans la table promotions
-- Exécuter ce script après avoir effectué les migrations

-- Supprimer d'abord les promotions existantes pour éviter les doublons
TRUNCATE TABLE promotions;

-- Insérer les promotions pour le cycle Licence
INSERT INTO promotions (name, description, is_active, created_at, updated_at) VALUES
('L1', 'Licence 1ère année', true, NOW(), NOW()),
('L2', 'Licence 2ème année', true, NOW(), NOW()),
('L3', 'Licence 3ème année', true, NOW(), NOW());

-- Insérer les promotions pour le cycle Master
INSERT INTO promotions (name, description, is_active, created_at, updated_at) VALUES
('M1', 'Master 1ère année', true, NOW(), NOW()),
('M2', 'Master 2ème année', true, NOW(), NOW());

-- Insérer les promotions pour le cycle Ingénieur
INSERT INTO promotions (name, description, is_active, created_at, updated_at) VALUES
('ING1', 'Ingénieur 1ère année', true, NOW(), NOW()),
('ING2', 'Ingénieur 2ème année', true, NOW(), NOW()),
('ING3', 'Ingénieur 3ème année', true, NOW(), NOW()),
('ING4', 'Ingénieur 4ème année', true, NOW(), NOW()),
('ING5', 'Ingénieur 5ème année', true, NOW(), NOW());

-- Insérer les promotions pour les cycles préparatoires
INSERT INTO promotions (name, description, is_active, created_at, updated_at) VALUES
('PREPA1', 'Prépa 1ère année', true, NOW(), NOW()),
('PREPA2', 'Prépa 2ème année', true, NOW(), NOW());

-- Insérer les promotions pour les doctorants
INSERT INTO promotions (name, description, is_active, created_at, updated_at) VALUES
('DOCTORAT', 'Doctorat', true, NOW(), NOW());

-- Afficher le résultat
SELECT * FROM promotions ORDER BY name;
