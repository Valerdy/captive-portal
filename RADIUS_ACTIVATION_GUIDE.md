# 📋 Guide du système d'activation RADIUS

## Vue d'ensemble

Ce système sépare l'**inscription utilisateur Django** de l'**activation RADIUS** pour offrir un contrôle administratif complet sur l'accès au réseau WiFi.

---

## 🔄 Workflow complet

### **Étape 1 : Pré-enregistrement** (Admin)

Un administrateur pré-enregistre un étudiant via l'interface admin.

**Endpoint**: `POST /api/core/admin/users/preregister/`

```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "promotion": "ING3",
  "matricule": "2024001",
  "username": "jdupont",  // Optionnel
  "email": "jdupont@student.example.com"  // Optionnel
}
```

**Résultat**:
- ✅ Utilisateur créé dans Django (`users` table)
- ✅ `is_pre_registered = True`
- ✅ `registration_completed = False`
- ❌ **PAS** dans `radcheck` (RADIUS)

---

### **Étape 2 : Inscription** (Utilisateur)

L'étudiant complète son inscription en fournissant ses informations et son mot de passe.

**Endpoint**: `POST /api/core/auth/register/`

```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "promotion": "ING3",
  "matricule": "2024001",
  "password": "MonMotDePasse123!",
  "password2": "MonMotDePasse123!"
}
```

**Résultat**:
- ✅ Utilisateur actif dans Django (`is_active = True`)
- ✅ `registration_completed = True`
- ✅ Mot de passe Django hashé
- ✅ Tokens JWT générés (cookies HttpOnly)
- ❌ **PAS encore dans `radcheck`** (RADIUS)
- ⚠️ `is_radius_activated = False`

**Message utilisateur**:
> "Inscription réussie ! Votre compte doit être activé par un administrateur pour accéder au portail captif."

---

### **Étape 3 : Activation RADIUS** (Admin)

Un administrateur active manuellement un ou plusieurs utilisateurs dans RADIUS.

**Endpoint**: `POST /api/core/admin/users/activate/`

```json
{
  "user_ids": [1, 2, 3, 5, 8]
}
```

**Résultat pour chaque utilisateur**:
```json
{
  "success": true,
  "message": "5 utilisateur(s) activé(s) dans RADIUS",
  "activated_users": [
    {
      "id": 1,
      "username": "jdupont",
      "email": "jdupont@student.example.com",
      "first_name": "Jean",
      "last_name": "Dupont",
      "promotion": "ING3",
      "matricule": "2024001",
      "radius_password": "kT@9pL#mXq$1RvZ",  // ⚠️ Mot de passe RADIUS
      "session_timeout": "1h",
      "bandwidth_limit": "10M/10M",
      "message": "Utilisateur activé dans RADIUS avec succès"
    },
    ...
  ],
  "failed_users": [],
  "summary": {
    "total_requested": 5,
    "activated": 5,
    "failed": 0
  },
  "important_note": "IMPORTANT: Communiquez les mots de passe RADIUS aux utilisateurs de manière sécurisée. Ces mots de passe ne seront plus affichés après cette réponse."
}
```

**Ce qui se passe en base de données**:

1. **`radcheck` table** (FreeRADIUS):
   ```sql
   INSERT INTO radcheck (username, attribute, op, value)
   VALUES ('jdupont', 'Cleartext-Password', ':=', 'kT@9pL#mXq$1RvZ');
   ```

2. **`radreply` table** (FreeRADIUS):
   ```sql
   INSERT INTO radreply (username, attribute, op, value)
   VALUES ('jdupont', 'Session-Timeout', '=', '3600');

   INSERT INTO radreply (username, attribute, op, value)
   VALUES ('jdupont', 'Mikrotik-Rate-Limit', '=', '10M/10M');
   ```

3. **`radusergroup` table** (FreeRADIUS):
   ```sql
   INSERT INTO radusergroup (username, groupname, priority)
   VALUES ('jdupont', 'user', 0);
   ```

4. **`users` table** (Django):
   ```sql
   UPDATE users
   SET is_radius_activated = TRUE
   WHERE id = 1;
   ```

---

## 🎯 Points clés

### **Deux mots de passe distincts**

| Type | Stockage | Utilisation | Format |
|------|----------|-------------|--------|
| **Mot de passe Django** | Table `users` (hashé Argon2) | Connexion à l'interface web/app | Défini par l'utilisateur lors de l'inscription |
| **Mot de passe RADIUS** | Table `radcheck` (clair) | Connexion au WiFi (FreeRADIUS) | Généré automatiquement lors de l'activation (16 caractères sécurisés) |

### **États d'un utilisateur**

| Champ | Valeur | Signification |
|-------|--------|---------------|
| `is_pre_registered` | `True` | Pré-enregistré par un admin |
| `registration_completed` | `False` | N'a pas encore complété son inscription |
| `is_radius_activated` | `False` | Pas encore activé dans RADIUS |

➡️ **Après inscription**:
- `registration_completed = True`
- `is_active = True`
- `is_radius_activated = False` ⚠️

➡️ **Après activation par admin**:
- `is_radius_activated = True` ✅
- Présence dans `radcheck`, `radreply`, `radusergroup`

---

## 🖥️ Intégration Frontend

### **Vue Admin: Liste des utilisateurs non activés**

```typescript
// Filtrer les utilisateurs en attente d'activation
const pendingActivation = users.value.filter(user =>
  user.registration_completed &&
  !user.is_radius_activated &&
  user.is_active
)
```

### **Action d'activation**

```typescript
async function activateUsers(userIds: number[]) {
  try {
    const response = await api.post('/api/core/admin/users/activate/', {
      user_ids: userIds
    })

    // Afficher les mots de passe RADIUS aux admins
    response.data.activated_users.forEach(user => {
      console.log(`${user.username}: ${user.radius_password}`)
      // ⚠️ IMPORTANT: Afficher dans une modal ou télécharger en CSV
      // Ces mots de passe ne seront plus accessibles après !
    })

    return response.data
  } catch (error) {
    console.error('Erreur activation:', error)
    throw error
  }
}
```

### **Affichage du statut**

```vue
<template>
  <div>
    <span v-if="!user.is_radius_activated" class="badge badge-warning">
      ⏳ En attente d'activation RADIUS
    </span>
    <span v-else class="badge badge-success">
      ✅ Activé RADIUS
    </span>
  </div>
</template>
```

---

## ⚠️ Sécurité et bonnes pratiques

### **Communication des mots de passe RADIUS**

1. ❌ **NE PAS** envoyer par email non chiffré
2. ❌ **NE PAS** stocker dans la base de données Django
3. ✅ **RECOMMANDÉ** :
   - Afficher dans une modal avec option de copie
   - Télécharger un CSV sécurisé
   - Envoyer par SMS si disponible
   - Utiliser un système de tickets sécurisé

### **Export CSV sécurisé**

```typescript
function exportActivatedUsers(users) {
  const csv = users.map(u =>
    `${u.username},${u.email},${u.radius_password}`
  ).join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `radius_passwords_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
```

### **Pourquoi le mot de passe en clair dans radcheck ?**

FreeRADIUS nécessite le mot de passe en clair (ou dans un format réversible) pour certains protocoles d'authentification comme:
- **CHAP** (Challenge Handshake Authentication Protocol)
- **MS-CHAP** (Microsoft CHAP)
- **EAP-MD5**

Alternative : Utiliser `Crypt-Password` ou `NT-Password` pour des protocoles plus sécurisés, mais cela limite les types d'authentification supportés.

---

## 🔍 Requêtes utiles

### **Lister les utilisateurs non activés**

```sql
SELECT id, username, email, first_name, last_name, promotion, matricule
FROM users
WHERE registration_completed = TRUE
  AND is_radius_activated = FALSE
  AND is_active = TRUE;
```

### **Vérifier l'activation RADIUS**

```sql
SELECT u.username, u.is_radius_activated, rc.value as radius_password
FROM users u
LEFT JOIN radcheck rc ON u.username = rc.username
WHERE u.id = 1;
```

### **Compter les utilisateurs par statut**

```sql
SELECT
  COUNT(*) FILTER (WHERE is_pre_registered = TRUE AND registration_completed = FALSE) AS pre_registered,
  COUNT(*) FILTER (WHERE registration_completed = TRUE AND is_radius_activated = FALSE) AS pending_activation,
  COUNT(*) FILTER (WHERE is_radius_activated = TRUE) AS radius_active
FROM users;
```

---

## 🧪 Tests

### **1. Tester le pré-enregistrement**

```bash
curl -X POST http://localhost:8000/api/core/admin/users/preregister/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "promotion": "ING3",
    "matricule": "TEST001"
  }'
```

### **2. Tester l'inscription**

```bash
curl -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "promotion": "ING3",
    "matricule": "TEST001",
    "password": "TestPassword123!",
    "password2": "TestPassword123!"
  }'
```

### **3. Tester l'activation RADIUS**

```bash
curl -X POST http://localhost:8000/api/core/admin/users/activate/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3]
  }'
```

---

## 📊 Schéma du workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTÈME D'ACTIVATION RADIUS                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│    ADMIN     │
└───────┬──────┘
        │
        │ 1. Pré-enregistre
        ▼
┌───────────────────┐
│  Table: users     │
│  ✅ is_pre_registered = TRUE
│  ❌ registration_completed = FALSE
│  ❌ is_radius_activated = FALSE
└───────────────────┘
        │
        │ 2. Utilisateur s'inscrit
        ▼
┌───────────────────┐
│  Table: users     │
│  ✅ is_pre_registered = TRUE
│  ✅ registration_completed = TRUE
│  ❌ is_radius_activated = FALSE
│  ✅ Mot de passe Django (hashé)
└───────────────────┘
        │
        │ 3. Admin active dans RADIUS
        ▼
┌───────────────────────────────────────────────┐
│  Table: users                                 │
│  ✅ is_radius_activated = TRUE                │
└───────────────────────────────────────────────┘
        │
        ├─────────────────────┬──────────────────┬──────────────────┐
        ▼                     ▼                  ▼                  ▼
┌───────────────┐   ┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│ Table:        │   │ Table:        │   │ Table:       │   │ Mot de passe │
│ radcheck      │   │ radreply      │   │ radusergroup │   │ RADIUS       │
│               │   │               │   │              │   │              │
│ ✅ Password   │   │ ✅ Timeout    │   │ ✅ Group     │   │ ✅ Généré    │
│ (clair)       │   │ ✅ Bandwidth  │   │              │   │ ✅ 16 chars  │
└───────────────┘   └───────────────┘   └──────────────┘   └──────────────┘
```

---

## 🎓 Avantages de cette approche

1. ✅ **Contrôle administratif total** : L'admin décide qui peut accéder au WiFi
2. ✅ **Séparation des accès** : Connexion web ≠ connexion WiFi
3. ✅ **Traçabilité** : Historique de qui a été activé et quand
4. ✅ **Sécurité renforcée** : Mots de passe différents pour chaque service
5. ✅ **Flexibilité** : Possibilité de désactiver l'accès WiFi sans bloquer l'accès web
6. ✅ **Conformité** : Respect des règles d'accès réseau de l'établissement

---

## 📝 Notes de migration

Si vous migrez depuis l'ancien système (activation automatique lors de l'inscription) :

1. Les utilisateurs existants peuvent avoir `is_radius_activated = NULL`
2. Exécuter une migration de données :
   ```sql
   UPDATE users
   SET is_radius_activated = TRUE
   WHERE username IN (SELECT DISTINCT username FROM radcheck);
   ```

3. Nettoyer les entrées `radcheck` orphelines :
   ```sql
   DELETE FROM radcheck
   WHERE username NOT IN (SELECT username FROM users);
   ```

---

## 🆘 Dépannage

### Utilisateur ne peut pas se connecter au WiFi

1. Vérifier `is_radius_activated = TRUE` dans la table `users`
2. Vérifier la présence dans `radcheck` :
   ```sql
   SELECT * FROM radcheck WHERE username = 'jdupont';
   ```
3. Vérifier que le mot de passe communiqué est correct
4. Vérifier les logs FreeRADIUS : `/var/log/freeradius/radius.log`

### Activation échoue

- Vérifier que l'utilisateur existe et `is_active = TRUE`
- Vérifier qu'il n'est pas déjà activé
- Vérifier les permissions admin de l'utilisateur qui fait la requête
- Consulter les logs Django pour l'erreur exacte

---

## 📚 Références

- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [Django Custom User Model](https://docs.djangoproject.com/en/5.0/topics/auth/customizing/)
- [Django REST Framework](https://www.django-rest-framework.org/)
