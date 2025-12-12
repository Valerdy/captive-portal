-- Script SQL pour ajouter le champ quota à la table radcheck
-- Utilisez ce script si vous préférez ajouter le champ manuellement
-- ou si les migrations Django ne fonctionnent pas pour votre base

-- ==============================================================
-- AJOUTER LE CHAMP QUOTA À RADCHECK
-- ==============================================================

-- Pour MySQL/MariaDB:
ALTER TABLE radcheck
ADD COLUMN quota BIGINT NULL
COMMENT 'Quota de données en octets (ex: 53687091200 = 50 Go). NULL = illimité';

-- Pour PostgreSQL:
-- ALTER TABLE radcheck
-- ADD COLUMN quota BIGINT NULL;
-- COMMENT ON COLUMN radcheck.quota IS 'Quota de données en octets (ex: 53687091200 = 50 Go). NULL = illimité';

-- ==============================================================
-- VÉRIFIER QUE LE CHAMP A ÉTÉ AJOUTÉ
-- ==============================================================

-- MySQL/MariaDB:
DESCRIBE radcheck;

-- PostgreSQL:
-- \d radcheck

-- ==============================================================
-- EXEMPLES D'UTILISATION
-- ==============================================================

-- Définir un quota de 50 Go pour un utilisateur
UPDATE radcheck
SET quota = 53687091200  -- 50 Go en octets
WHERE username = 'john.doe' AND attribute = 'Cleartext-Password';

-- Définir un quota de 100 Go pour tous les utilisateurs d'une promotion
UPDATE radcheck r
INNER JOIN core_user u ON r.username = u.username
INNER JOIN core_promotion p ON u.promotion_id = p.id
SET r.quota = 107374182400  -- 100 Go
WHERE p.name = 'Promo2024' AND r.attribute = 'Cleartext-Password';

-- Définir un quota illimité (NULL)
UPDATE radcheck
SET quota = NULL
WHERE username = 'admin.user';

-- Vérifier les quotas définis
SELECT username, quota,
       ROUND(quota / 1073741824, 2) AS quota_go
FROM radcheck
WHERE attribute = 'Cleartext-Password'
  AND quota IS NOT NULL
ORDER BY quota DESC;

-- ==============================================================
-- CALCULER LA CONSOMMATION D'UN UTILISATEUR
-- ==============================================================

-- Consommation totale d'un utilisateur
SELECT
    username,
    SUM(acctinputoctets + acctoutputoctets) AS total_octets,
    ROUND(SUM(acctinputoctets + acctoutputoctets) / 1073741824, 2) AS total_go
FROM radacct
WHERE username = 'john.doe'
GROUP BY username;

-- Comparer consommation et quota
SELECT
    rc.username,
    rc.quota AS quota_octets,
    ROUND(rc.quota / 1073741824, 2) AS quota_go,
    COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) AS consomme_octets,
    ROUND(COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) / 1073741824, 2) AS consomme_go,
    CASE
        WHEN rc.quota IS NULL THEN 'ILLIMITÉ'
        WHEN COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) >= rc.quota THEN 'DÉPASSÉ'
        ELSE 'OK'
    END AS statut_quota,
    rc.statut AS actif
FROM radcheck rc
LEFT JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
GROUP BY rc.username, rc.quota, rc.statut
ORDER BY consomme_octets DESC;

-- ==============================================================
-- DÉSACTIVER MANUELLEMENT UN UTILISATEUR QUI A DÉPASSÉ
-- ==============================================================

-- Désactiver un utilisateur
UPDATE radcheck
SET statut = 0
WHERE username = 'john.doe';

-- Réactiver un utilisateur
UPDATE radcheck
SET statut = 1
WHERE username = 'john.doe';

-- ==============================================================
-- CONVERTIR DES Go EN OCTETS (POUR DÉFINIR LES QUOTAS)
-- ==============================================================

/*
1 Go = 1073741824 octets (1024^3)

Exemples de conversion:
- 1 Go   = 1073741824 octets
- 5 Go   = 5368709120 octets
- 10 Go  = 10737418240 octets
- 50 Go  = 53687091200 octets
- 100 Go = 107374182400 octets
- 500 Go = 536870912000 octets
- 1 To   = 1099511627776 octets
*/

-- Calculer en SQL (exemple pour 50 Go):
SELECT 50 * 1024 * 1024 * 1024 AS octets_50go;

-- ==============================================================
-- NETTOYER LES STATISTIQUES (REMETTRE À ZÉRO LA CONSOMMATION)
-- ==============================================================

-- ⚠️ ATTENTION: Ceci supprime l'historique de consommation
-- À utiliser avec précaution, par exemple pour un nouveau cycle de facturation

-- Supprimer toutes les données d'accounting pour un utilisateur
DELETE FROM radacct WHERE username = 'john.doe';

-- Supprimer les anciennes sessions (plus de 30 jours)
DELETE FROM radacct
WHERE acctstarttime < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- ==============================================================
-- REQUÊTES UTILES POUR LA SURVEILLANCE
-- ==============================================================

-- Top 10 des plus gros consommateurs
SELECT
    username,
    SUM(acctinputoctets + acctoutputoctets) AS total_octets,
    ROUND(SUM(acctinputoctets + acctoutputoctets) / 1073741824, 2) AS total_go
FROM radacct
GROUP BY username
ORDER BY total_octets DESC
LIMIT 10;

-- Utilisateurs qui ont dépassé leur quota
SELECT
    rc.username,
    rc.quota AS quota_octets,
    SUM(ra.acctinputoctets + ra.acctoutputoctets) AS consomme_octets,
    ROUND((SUM(ra.acctinputoctets + ra.acctoutputoctets) - rc.quota) / 1073741824, 2) AS depassement_go,
    rc.statut AS actif
FROM radcheck rc
INNER JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
  AND rc.quota IS NOT NULL
GROUP BY rc.username, rc.quota, rc.statut
HAVING SUM(ra.acctinputoctets + ra.acctoutputoctets) >= rc.quota
ORDER BY depassement_go DESC;

-- Utilisateurs proches du quota (>80%)
SELECT
    rc.username,
    ROUND(rc.quota / 1073741824, 2) AS quota_go,
    ROUND(SUM(ra.acctinputoctets + ra.acctoutputoctets) / 1073741824, 2) AS consomme_go,
    ROUND(SUM(ra.acctinputoctets + ra.acctoutputoctets) / rc.quota * 100, 1) AS pourcentage
FROM radcheck rc
INNER JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
  AND rc.quota IS NOT NULL
GROUP BY rc.username, rc.quota
HAVING SUM(ra.acctinputoctets + ra.acctoutputoctets) / rc.quota >= 0.8
   AND SUM(ra.acctinputoctets + ra.acctoutputoctets) < rc.quota
ORDER BY pourcentage DESC;
