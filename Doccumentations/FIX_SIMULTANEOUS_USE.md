# 🔧 Correction: Suppression de l'attribut Simultaneous-Use

## ✅ Problème résolu

Vous aviez raison! Votre code Django ajoutait automatiquement l'attribut `Simultaneous-Use := 1` dans la table `radcheck` lors de l'activation des utilisateurs.

## 🔍 Cause identifiée

L'attribut était ajouté à **deux endroits** dans votre fichier `backend/core/viewsets.py`:

1. **Fonction `activate_radius()`** (ligne ~392-398)
   - Utilisée pour l'activation **individuelle** d'un utilisateur
   - Ajoutait: `Simultaneous-Use := 1`

2. **Fonction `activate()` dans PromotionViewSet** (ligne ~839-848)
   - Utilisée pour l'activation **par promotion**
   - Ajoutait: `Simultaneous-Use := 1`

## ✅ Solution appliquée

Les deux blocs de code ont été **complètement supprimés**. Maintenant, lors de l'activation:

### Dans `radcheck` (authentification):
- ✅ `Cleartext-Password := <mot_de_passe>` - **CONSERVÉ**
- ✅ `ChilliSpot-Max-Total-Octets := <quota>` (si profil limité) - **CONSERVÉ**
- ❌ `Simultaneous-Use := 1` - **SUPPRIMÉ**

### Dans `radreply` (paramètres de session):
- ✅ `Session-Timeout = <temps>`
- ✅ `Idle-Timeout = <temps>`
- ✅ `Mikrotik-Rate-Limit = <bande_passante>`

### Dans `radusergroup` (groupes):
- ✅ Affectation au groupe (student/admin/etc.)

---

## 🧹 Nettoyage de la base de données

### Option 1: Script SQL automatique (RECOMMANDÉ)

Un script SQL a été créé pour nettoyer toutes les entrées `Simultaneous-Use` existantes:

```bash
mysql -u root -p -h 10.242.52.100 radius < /home/user/captive-portal/backend/remove_simultaneous_use.sql
```

Mot de passe: `MotDePasseSecurise123!`

### Option 2: Nettoyage manuel via MySQL

#### Étape 1: Connexion à la base

```bash
mysql -u root -p -h 10.242.52.100 radius
```

#### Étape 2: Vérifier combien d'entrées seront supprimées

```sql
SELECT COUNT(*) as total_simultaneous_use
FROM radcheck
WHERE attribute = 'Simultaneous-Use';
```

#### Étape 3: Voir les détails (optionnel)

```sql
SELECT id, username, attribute, op, value
FROM radcheck
WHERE attribute = 'Simultaneous-Use'
ORDER BY username
LIMIT 20;
```

Vous devriez voir vos utilisateurs comme EUIN030, EUIN0130, etc.

#### Étape 4: Suppression

```sql
START TRANSACTION;

-- Supprimer toutes les entrées Simultaneous-Use
DELETE FROM radcheck
WHERE attribute = 'Simultaneous-Use';

-- Afficher combien ont été supprimées
SELECT ROW_COUNT() as 'Supprimées';

-- Vérifier qu'il n'en reste plus
SELECT COUNT(*) FROM radcheck WHERE attribute = 'Simultaneous-Use';

-- Si résultat = 0, valider:
COMMIT;

-- Si problème, annuler: ROLLBACK;
```

#### Étape 5: Vérification finale

```sql
-- Voir ce qui reste pour chaque utilisateur
SELECT
    username,
    GROUP_CONCAT(attribute ORDER BY attribute SEPARATOR ', ') as attributes
FROM radcheck
GROUP BY username
ORDER BY username
LIMIT 20;
```

Vous devriez voir uniquement:
- `Cleartext-Password` (pour tous)
- `ChilliSpot-Max-Total-Octets` (pour certains, si quota limité)

---

## 🧪 Test après correction

1. **Redémarrez votre serveur Django**
   ```bash
   # Selon votre configuration, par exemple:
   systemctl restart django
   # ou
   supervisorctl restart django
   ```

2. **Nettoyez la base** (voir ci-dessus)

3. **Testez l'activation d'une promotion**:
   - Allez dans l'admin panel
   - Cliquez sur une promotion
   - Activez-la
   - Vérifiez dans la base de données:

   ```sql
   -- Vérifier qu'un utilisateur n'a QUE Cleartext-Password
   SELECT * FROM radcheck WHERE username = 'VOTRE_USERNAME';
   ```

   Résultat attendu: **Uniquement 1 ligne** avec `Cleartext-Password`

4. **Vérifiez que FreeRADIUS fonctionne**:
   - Les utilisateurs peuvent toujours se connecter
   - Les sessions se créent normalement
   - Les quotas fonctionnent (si configurés)

---

## 📊 Récapitulatif des modifications

### Fichiers modifiés:
1. ✅ `backend/core/viewsets.py`
   - Supprimé: Création de `Simultaneous-Use` dans `activate_radius()`
   - Supprimé: Création de `Simultaneous-Use` dans `PromotionViewSet.activate()`

### Fichiers créés:
2. ✅ `backend/remove_simultaneous_use.sql`
   - Script SQL pour nettoyer la base de données

---

## 🔍 Pourquoi cette correction?

### Avant (❌ Problématique):
```sql
-- Dans radcheck pour chaque utilisateur:
id  username    attribute              op   value
28  EUIN030     Cleartext-Password     :=   motdepasse123
29  EUIN030     Simultaneous-Use       :=   1              ← Non désiré
```

### Après (✅ Correct):
```sql
-- Dans radcheck pour chaque utilisateur:
id  username    attribute              op   value
28  EUIN030     Cleartext-Password     :=   motdepasse123  ← Seul attribut
```

---

## 🛡️ Impact sur FreeRADIUS

**Bonne nouvelle**: Cette modification n'affectera **pas** le fonctionnement de FreeRADIUS:

- ✅ Les utilisateurs peuvent toujours se connecter (Cleartext-Password présent)
- ✅ Les limites de session fonctionnent (dans radreply)
- ✅ Les quotas fonctionnent (ChilliSpot-Max-Total-Octets si configuré)
- ✅ La bande passante est limitée (Mikrotik-Rate-Limit dans radreply)

**Ce qui change**:
- ❌ FreeRADIUS ne vérifiera plus le nombre de connexions simultanées par utilisateur
- Si vous vouliez cette limitation, elle peut être configurée ailleurs (ex: groupcheck, radgroupreply)

---

## 📝 Notes importantes

1. **Simultaneous-Use n'est plus géré au niveau utilisateur**
   - Si vous voulez limiter les connexions simultanées, faites-le au niveau du **groupe**
   - Exemple: Ajouter dans `radgroupcheck`:
     ```sql
     INSERT INTO radgroupcheck (groupname, attribute, op, value)
     VALUES ('student', 'Simultaneous-Use', ':=', '1');
     ```

2. **Les anciens utilisateurs déjà activés**
   - Ont encore `Simultaneous-Use` dans leur radcheck
   - Exécutez le script SQL pour les nettoyer

3. **Les nouveaux utilisateurs activés**
   - N'auront **que** `Cleartext-Password` (+ quota si limité)
   - C'est le comportement désiré ✅

---

## ✅ Validation finale

Après avoir appliqué ces changements et nettoyé la base:

```bash
# Test rapide
mysql -u root -p -h 10.242.52.100 radius -e "
SELECT COUNT(*) as 'Entrées_Simultaneous-Use_restantes'
FROM radcheck
WHERE attribute = 'Simultaneous-Use';
"
```

**Résultat attendu**: `0`

Si vous obtenez `0`, félicitations! 🎉 Le problème est complètement résolu.

---

## 🆘 Support

Si après ces changements:
- ✅ Les utilisateurs peuvent toujours se connecter → **Tout va bien**
- ❌ Les utilisateurs ne peuvent plus se connecter → Vérifiez que `Cleartext-Password` existe dans radcheck
- ⚠️ Vous voulez vraiment `Simultaneous-Use` → Configurez-le au niveau du groupe, pas de l'utilisateur
