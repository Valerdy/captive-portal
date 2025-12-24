# 🔧 Résolution du Problème de Connexion Admin

## 🎯 Votre Situation

Vous avez créé un superuser **valerdy** avec le mot de passe **Azerty1234@#**, mais vous rencontrez:
- ❌ Erreurs 401 Unauthorized lors de la connexion
- ❌ Impossible de supprimer l'utilisateur (contrainte de clé étrangère sur les tokens JWT)

---

## 🔍 Diagnostic Rapide

### Étape 1: Vérifier l'Utilisateur

**Double-cliquez sur:** `check_users.bat`

Ou manuellement:
```bash
cd backend
venv\Scripts\activate
python check_users.py
```

Ce script va afficher:
- ✅ Tous les utilisateurs
- ✅ Leurs permissions (is_superuser, is_staff, is_active)
- ✅ Leur accès aux interfaces admin
- ✅ Le nombre de tokens JWT

**Vérifiez que valerdy a:**
- `is_superuser = True`
- `is_staff = True`
- `is_active = True`

---

## ✅ Solution 1: Corriger les Permissions

Si les permissions ne sont pas correctes:

**Double-cliquez sur:** `fix_admin.bat`

Ou manuellement:
```bash
cd backend
venv\Scripts\activate
python fix_admin_user.py valerdy
```

Ce script va automatiquement:
- ✅ Définir `is_superuser = True`
- ✅ Définir `is_staff = True`
- ✅ Définir `is_active = True`

**Résultat:** L'utilisateur valerdy aura tous les droits admin !

---

## 🔑 Connexion aux Interfaces

### 1. Admin Django (Backend)

**URL:** http://localhost:8000/admin

**Credentials:**
- Username: `valerdy`
- Password: `Azerty1234@#`

✅ Cette interface permet de gérer la base de données directement.

---

### 2. Admin Frontend (Portail Captif)

**URL:** http://localhost:5173

**Étapes:**
1. Cliquez sur l'icône **"Admin"** en haut à droite (icône engrenage)
2. Entrez les credentials:
   - Username: `valerdy`
   - Password: `Azerty1234@#`
3. Vous serez redirigé vers le dashboard admin

✅ Cette interface permet de gérer les utilisateurs, sessions, monitoring, etc.

---

## 🐛 Causes Possibles des Erreurs 401

### Problème 1: Permissions Incorrectes

**Symptôme:** L'utilisateur existe mais n'a pas `is_staff` ou `is_superuser`

**Solution:** Exécutez `fix_admin.bat`

---

### Problème 2: Compte Inactif

**Symptôme:** `is_active = False`

**Solution:** Exécutez `fix_admin.bat` (active automatiquement)

---

### Problème 3: Mot de Passe Incorrect

**Symptôme:** Le mot de passe ne fonctionne pas

**Solution:** Réinitialisez le mot de passe:

```bash
cd backend
venv\Scripts\activate
python manage.py changepassword valerdy
```

Ou créez un nouveau superuser:
```bash
python manage.py createsuperuser
```

---

### Problème 4: Tokens JWT Corrompus

**Symptôme:** Des erreurs de token après plusieurs tentatives

**Solution:** Nettoyez les tokens JWT:

```bash
cd backend
venv\Scripts\activate
python clean_tokens.py valerdy
```

---

## 🗑️ Supprimer un Utilisateur (Si Nécessaire)

### Problème de Contrainte de Clé Étrangère

**Erreur:**
```
ERREUR: UPDATE ou DELETE sur la table « users » viole la contrainte de clé étrangère
« token_blacklist_outstandingtoken_user_id_83bc629a_fk_users_id »
```

**Cause:** L'utilisateur a des tokens JWT dans la table `token_blacklist_outstandingtoken`

### Solution: Nettoyer d'Abord les Tokens

**Étape 1:** Nettoyer les tokens JWT

```bash
cd backend
venv\Scripts\activate
python clean_tokens.py valerdy
```

Le script va:
- ✅ Lister tous les tokens de l'utilisateur
- ✅ Demander confirmation
- ✅ Supprimer tous les tokens

**Étape 2:** Supprimer l'utilisateur

**Option A: Via Django Shell**
```bash
python manage.py shell
```

Puis dans le shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.get(username='valerdy').delete()
print("Utilisateur supprimé")
exit()
```

**Option B: Via pgAdmin**

1. Ouvrez pgAdmin
2. Naviguez vers: `captive_portal_db` → Schemas → public → Tables → `core_user`
3. Clic droit → **View/Edit Data** → **All Rows**
4. Trouvez l'utilisateur `valerdy`
5. Clic droit sur la ligne → **Delete Row**
6. Confirmez

✅ L'utilisateur est maintenant supprimé !

---

## 🧪 Tester la Connexion

### Test 1: Backend Django Admin

```bash
# Ouvrez le navigateur
http://localhost:8000/admin

# Connectez-vous avec:
Username: valerdy
Password: Azerty1234@#
```

✅ Vous devriez voir l'interface d'administration Django

---

### Test 2: Frontend Admin

```bash
# Ouvrez le navigateur
http://localhost:5173

# Cliquez sur "Admin" en haut à droite
# Connectez-vous avec:
Username: valerdy
Password: Azerty1234@#
```

✅ Vous devriez être redirigé vers `/admin/dashboard`

---

### Test 3: API avec curl

```bash
curl -X POST http://localhost:8000/api/core/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "valerdy", "password": "Azerty1234@#"}'
```

**Résultat attendu (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "valerdy",
    "email": "...",
    "is_staff": true,
    "is_superuser": true
  },
  "access": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

**Si vous recevez 401:**
- Le mot de passe est incorrect
- L'utilisateur n'est pas actif
- Les permissions sont incorrectes

---

## 📋 Checklist de Résolution

### Diagnostic

- [ ] Exécutez `check_users.bat`
- [ ] Vérifiez que valerdy a `is_superuser = True`
- [ ] Vérifiez que valerdy a `is_staff = True`
- [ ] Vérifiez que valerdy a `is_active = True`

### Correction

- [ ] Si permissions incorrectes: Exécutez `fix_admin.bat`
- [ ] Si mot de passe oublié: `python manage.py changepassword valerdy`
- [ ] Si tokens corrompus: `python clean_tokens.py valerdy`

### Test

- [ ] Testez http://localhost:8000/admin
- [ ] Testez http://localhost:5173 (cliquez sur Admin)
- [ ] Testez avec curl

---

## 🎯 Scripts Disponibles

| Script | Description |
|--------|-------------|
| **`check_users.bat`** | Vérifie tous les utilisateurs et leurs permissions |
| **`fix_admin.bat`** | Corrige automatiquement les permissions de valerdy |
| **`clean_tokens.py`** | Nettoie les tokens JWT d'un utilisateur |
| **`backend/check_users.py`** | Version Python du diagnostic |
| **`backend/fix_admin_user.py`** | Version Python de la correction |

---

## 💡 Astuce: Créer un Nouvel Admin

Si vous voulez recommencer à zéro:

```bash
cd backend
venv\Scripts\activate

# Supprimer l'ancien (après avoir nettoyé les tokens)
python clean_tokens.py valerdy
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.get(username='valerdy').delete(); print('Supprimé')"

# Créer un nouveau
python manage.py createsuperuser
```

Ou utilisez le script automatique:
```bash
create_admin.bat
```
(Crée automatiquement un admin avec username: `admin`, password: `admin123`)

---

## 📞 Besoin d'Aide ?

Si le problème persiste après avoir suivi ce guide:

1. Exécutez `check_users.bat` et envoyez-moi la sortie
2. Vérifiez les logs du backend pour des erreurs spécifiques
3. Consultez `POSTGRESQL_CONFIG.md` pour vérifier la configuration de la base

---

## ✅ Résumé Rapide

**Pour corriger le problème:**

1. **Double-cliquez sur** `fix_admin.bat`
2. **Testez la connexion** sur http://localhost:5173
3. **Cliquez sur "Admin"** en haut à droite
4. **Connectez-vous** avec valerdy / Azerty1234@#

**Si ça ne fonctionne toujours pas:**

1. **Nettoyez les tokens:** `python clean_tokens.py valerdy`
2. **Réinitialisez le mot de passe:** `python manage.py changepassword valerdy`
3. **Retestez**

---

**Dernière mise à jour:** 2025-11-20
