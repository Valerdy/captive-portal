-- Script SQL pour supprimer toutes les entrées Simultaneous-Use de radcheck
-- Ces entrées sont ajoutées automatiquement par l'ancien code d'activation

-- ================================================================================
-- ÉTAPE 1: VÉRIFICATION - Voir combien d'entrées seront supprimées
-- ================================================================================

SELECT
    'AVANT SUPPRESSION' as etape,
    COUNT(*) as nombre_entrees_simultaneous_use
FROM radcheck
WHERE attribute = 'Simultaneous-Use';

-- Voir les détails des entrées qui seront supprimées
SELECT
    id,
    username,
    attribute,
    op,
    value,
    statut
FROM radcheck
WHERE attribute = 'Simultaneous-Use'
ORDER BY username
LIMIT 20;

-- ================================================================================
-- ÉTAPE 2: SUPPRESSION - Supprimer toutes les entrées Simultaneous-Use
-- ================================================================================

-- Commencer une transaction pour pouvoir annuler si nécessaire
START TRANSACTION;

-- Supprimer toutes les entrées Simultaneous-Use
DELETE FROM radcheck
WHERE attribute = 'Simultaneous-Use';

-- Afficher combien ont été supprimées
SELECT ROW_COUNT() as 'Entrées_Simultaneous-Use_supprimées';

-- Vérifier qu'il ne reste plus d'entrées Simultaneous-Use
SELECT
    'APRÈS SUPPRESSION' as etape,
    COUNT(*) as nombre_entrees_simultaneous_use
FROM radcheck
WHERE attribute = 'Simultaneous-Use';

-- Si tout est OK, valider la transaction
COMMIT;

-- Si vous voulez annuler: ROLLBACK;

-- ================================================================================
-- ÉTAPE 3: VÉRIFICATION FINALE
-- ================================================================================

-- Vérifier que chaque utilisateur n'a plus que Cleartext-Password (et éventuellement quota)
SELECT
    username,
    GROUP_CONCAT(attribute ORDER BY attribute SEPARATOR ', ') as attributes_restants
FROM radcheck
GROUP BY username
ORDER BY username
LIMIT 20;
