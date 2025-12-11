-- Script SQL pour nettoyer les entrées RADIUS orphelines
-- ATTENTION: Exécutez d'abord les requêtes SELECT pour voir ce qui sera supprimé

-- ================================================================================
-- ÉTAPE 1: VÉRIFICATION - Lister les utilisateurs orphelins
-- ================================================================================

-- 1.1 Utilisateurs dans radcheck qui n'existent PAS dans core_user
SELECT
    'radcheck' as table_name,
    rc.id,
    rc.username,
    rc.attribute,
    rc.value,
    'ORPHELIN - User inexistant' as status
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL
ORDER BY rc.username, rc.id;

-- 1.2 Utilisateurs dans radreply qui n'existent PAS dans core_user
SELECT
    'radreply' as table_name,
    rr.id,
    rr.username,
    rr.attribute,
    rr.value,
    'ORPHELIN - User inexistant' as status
FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL
ORDER BY rr.username, rr.id;

-- 1.3 Utilisateurs dans radusergroup qui n'existent PAS dans core_user
SELECT
    'radusergroup' as table_name,
    rug.id,
    rug.username,
    rug.groupname,
    'ORPHELIN - User inexistant' as status
FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL
ORDER BY rug.username, rug.id;

-- 1.4 Comptage des orphelins par table
SELECT
    'radcheck' as table_name,
    COUNT(*) as orphaned_count
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT
    'radreply' as table_name,
    COUNT(*) as orphaned_count
FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT
    'radusergroup' as table_name,
    COUNT(*) as orphaned_count
FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL;

-- 1.5 Liste unique des usernames orphelins
SELECT DISTINCT username
FROM (
    SELECT username FROM radcheck
    UNION
    SELECT username FROM radreply
    UNION
    SELECT username FROM radusergroup
) AS all_radius_users
WHERE username NOT IN (SELECT username FROM core_user)
ORDER BY username;


-- ================================================================================
-- ÉTAPE 2: SUPPRESSION - À exécuter APRÈS vérification
-- ================================================================================
-- DÉCOMMENTEZ les lignes ci-dessous SEULEMENT si vous êtes sûr de vouloir supprimer

/*
-- Commencer une transaction pour pouvoir annuler si nécessaire
START TRANSACTION;

-- 2.1 Supprimer les entrées orphelines de radcheck
DELETE rc FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL;

-- Afficher le nombre supprimé
SELECT ROW_COUNT() as 'radcheck_deleted';

-- 2.2 Supprimer les entrées orphelines de radreply
DELETE rr FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL;

-- Afficher le nombre supprimé
SELECT ROW_COUNT() as 'radreply_deleted';

-- 2.3 Supprimer les entrées orphelines de radusergroup
DELETE rug FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL;

-- Afficher le nombre supprimé
SELECT ROW_COUNT() as 'radusergroup_deleted';

-- Si tout est OK, valider la transaction
COMMIT;

-- Si vous voulez annuler: ROLLBACK;
*/


-- ================================================================================
-- ÉTAPE 3: VÉRIFICATION POST-NETTOYAGE
-- ================================================================================
-- À exécuter après la suppression pour vérifier qu'il ne reste plus d'orphelins

/*
SELECT
    'radcheck' as table_name,
    COUNT(*) as remaining_orphans
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT
    'radreply',
    COUNT(*)
FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT
    'radusergroup',
    COUNT(*)
FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL;
*/
