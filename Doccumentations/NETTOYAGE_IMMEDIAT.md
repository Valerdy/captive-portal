# 🚨 Nettoyage Immédiat des Entrées RADIUS Orphelines

## Problème Constaté

Vous avez des utilisateurs dans votre table `radcheck` qui n'existent PAS dans votre table `core_user`:
- **EUIN0130** (ID 28-29)
- **EUIN030** (ID 30-31)

Ces "fantômes" causent des problèmes lors de l'activation des promotions.

---

## 🎯 Solution Rapide (2 options)

### Option 1: Via SQL (RECOMMANDÉ - Plus rapide)

#### Étape 1: Connexion à la base de données

```bash
mysql -u root -p -h 10.242.52.100 radius
```

Mot de passe: `MotDePasseSecurise123!` (selon votre configuration)

#### Étape 2: Vérification des orphelins

Exécutez d'abord cette requête pour **VOIR** les utilisateurs orphelins sans rien supprimer:

```sql
-- Voir tous les usernames orphelins
SELECT DISTINCT rc.username
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL
ORDER BY rc.username;
```

Vous devriez voir au minimum:
- EUIN030
- EUIN0130

#### Étape 3: Comptage des entrées à supprimer

```sql
-- Compter combien d'entrées seront supprimées dans chaque table
SELECT
    'radcheck' as table_name,
    COUNT(*) as orphaned_count
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT 'radreply', COUNT(*)
FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL

UNION ALL

SELECT 'radusergroup', COUNT(*)
FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL;
```

#### Étape 4: Suppression (avec sécurité)

```sql
-- Démarrer une transaction (permet d'annuler si problème)
START TRANSACTION;

-- Supprimer de radcheck
DELETE rc FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL;

SELECT ROW_COUNT() as 'radcheck_supprimés';

-- Supprimer de radreply
DELETE rr FROM radreply rr
LEFT JOIN core_user cu ON rr.username = cu.username
WHERE cu.username IS NULL;

SELECT ROW_COUNT() as 'radreply_supprimés';

-- Supprimer de radusergroup
DELETE rug FROM radusergroup rug
LEFT JOIN core_user cu ON rug.username = cu.username
WHERE cu.username IS NULL;

SELECT ROW_COUNT() as 'radusergroup_supprimés';

-- Si tout est OK, valider:
COMMIT;

-- Si vous voulez annuler: ROLLBACK;
```

#### Étape 5: Vérification finale

```sql
-- Vérifier qu'il ne reste plus d'orphelins
SELECT COUNT(*) as 'Orphelins_restants_radcheck'
FROM radcheck rc
LEFT JOIN core_user cu ON rc.username = cu.username
WHERE cu.username IS NULL;
```

Résultat attendu: **0**

---

### Option 2: Via le script Python Django

Si vous préférez utiliser le script Python:

```bash
# Activez votre environnement virtuel Python (si vous en avez un)
# source /path/to/venv/bin/activate

cd /home/user/captive-portal/backend

# Mode test (ne supprime rien)
python manage.py cleanup_orphaned_radius_entries --dry-run

# Mode réel (supprime les orphelins)
python manage.py cleanup_orphaned_radius_entries
```

---

## 🔍 Diagnostic Avancé

### Vérifier si un utilisateur spécifique existe dans core_user

```sql
-- Chercher EUIN030 dans la table User
SELECT id, username, first_name, last_name, is_active
FROM core_user
WHERE username = 'EUIN030';

-- Si résultat vide = utilisateur n'existe PAS dans User
-- Si résultat présent = utilisateur existe (PAS orphelin)
```

### Voir toutes les entrées RADIUS pour EUIN030

```sql
-- Dans radcheck
SELECT * FROM radcheck WHERE username = 'EUIN030';

-- Dans radreply
SELECT * FROM radreply WHERE username = 'EUIN030';

-- Dans radusergroup
SELECT * FROM radusergroup WHERE username = 'EUIN030';
```

---

## ✅ Après le Nettoyage

1. **Redémarrez votre serveur Django** (si nécessaire)
2. **Testez l'activation d'une promotion** dans l'interface admin
3. **Vérifiez que seuls les vrais utilisateurs apparaissent**

---

## 🛡️ Prévention Future

Pour éviter ce problème à l'avenir:

1. **Ne supprimez JAMAIS des utilisateurs directement en SQL**
2. **Utilisez toujours l'interface admin Django** pour supprimer des utilisateurs
3. **Exécutez le script de nettoyage périodiquement** (ex: une fois par mois)

---

## 📁 Fichier SQL Complet

Un fichier SQL complet avec toutes ces requêtes est disponible dans:
```
/home/user/captive-portal/backend/cleanup_orphaned_radius.sql
```

Vous pouvez l'exécuter directement:

```bash
mysql -u root -p -h 10.242.52.100 radius < /home/user/captive-portal/backend/cleanup_orphaned_radius.sql
```

---

## ⚠️ Important

- Les requêtes SELECT (vérification) sont **sans risque** - exécutez-les autant que vous voulez
- Les requêtes DELETE sont **irréversibles** - vérifiez d'abord avec SELECT
- La transaction `START TRANSACTION` + `COMMIT` permet d'annuler avec `ROLLBACK` en cas de problème
- **Faites un backup** de votre base avant toute suppression importante (optionnel mais recommandé)

---

## 🆘 En Cas de Problème

Si vous supprimez par erreur des entrées RADIUS valides:

1. **ROLLBACK** immédiatement (si encore dans la transaction)
2. Réactivez les utilisateurs concernés via l'admin panel
3. Le système recréera automatiquement leurs entrées RADIUS

---

**Question**: Voulez-vous que je vous guide étape par étape dans l'exécution de ces commandes SQL?
