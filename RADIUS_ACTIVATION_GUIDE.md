# 📋 Guide du système d'activation RADIUS

## Vue d'ensemble

Ce système sépare l'**inscription utilisateur Django** de l'**activation RADIUS** pour offrir un contrôle administratif complet sur l'accès au réseau WiFi.

---

## 🔄 Workflow complet

### **Étape 1 : Inscription** (Utilisateur)

L'étudiant s'inscrit directement en fournissant ses informations et son mot de passe.

**Endpoint**: `POST /api/core/auth/register/`

```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "promotion": "ING3",
  "matricule": "2024001",
  "username": "jdupont",  // Optionnel (par défaut: matricule)
  "email": "jdupont@student.example.com",  // Optionnel (par défaut: matricule@student.ucac-icam.com)
  "password": "MonMotDePasse123!",
  "password2": "MonMotDePasse123!"
}
```

**Résultat**:
- ✅ Utilisateur créé et actif dans Django (`is_active = True`)
- ✅ Mot de passe Django hashé
- ✅ Tokens JWT générés (cookies HttpOnly)
- ✅ Username généré automatiquement depuis matricule si non fourni
- ✅ Email généré automatiquement si non fourni
- ❌ **PAS encore dans `radcheck`** (RADIUS)
- ⚠️ `is_radius_activated = False`

**Message utilisateur**:
> "Inscription réussie ! Votre compte doit être activé par un administrateur pour accéder au portail captif."

---

### **Étape 2 : Activation RADIUS** (Admin)

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
      "radius_password": "MonMotDePasse123!",  // ✅ MÊME mot de passe que Django
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
  "important_note": "Les utilisateurs peuvent désormais se connecter au WiFi avec le même mot de passe que pour l'interface web."
}
```

**Ce qui se passe en base de données**:

1. **`radcheck` table** (FreeRADIUS):
   ```sql
   -- Le mot de passe est copié depuis users.cleartext_password
   INSERT INTO radcheck (username, attribute, op, value)
   VALUES ('jdupont', 'Cleartext-Password', ':=', 'MonMotDePasse123!');
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

### **⚠️ IMPORTANT : Stockage du mot de passe**

Le système utilise **UN SEUL mot de passe** pour Django ET RADIUS, mais stocké de **DEUX façons différentes** :

| Stockage | Emplacement | Format | Utilisation |
|----------|-------------|--------|-------------|
| **Hash Argon2** | Table `users.password` | `argon2$argon2id$v=19$...` (irréversible) | Authentification Django (interface web) |
| **Texte clair** | Table `users.cleartext_password` | Mot de passe original | Copié dans `radcheck` lors de l'activation RADIUS |
| **Texte clair** | Table `radcheck.value` | Mot de passe original | Authentification FreeRADIUS (WiFi) |

### **🚨 RISQUE DE SÉCURITÉ**

- Le mot de passe est stocké **EN CLAIR** dans `users.cleartext_password`
- Si la base de données est compromise, **TOUS les mots de passe sont exposés**
- Cette approche viole les bonnes pratiques de sécurité
- Recommandation : protéger l'accès à la base de données avec des règles strictes

### **États d'un utilisateur**

| Champ | Valeur | Signification |
|-------|--------|---------------|
| `is_active` | `True` | Utilisateur inscrit et actif dans Django |
| `is_radius_activated` | `False` | Pas encore activé dans RADIUS |

➡️ **Après inscription**:
- `is_active = True`
- `is_radius_activated = False` ⚠️
- Accès à l'interface web uniquement

➡️ **Après activation par admin**:
- `is_radius_activated = True` ✅
- Présence dans `radcheck`, `radreply`, `radusergroup`
- Accès WiFi autorisé

---

## 🖥️ Intégration Frontend

### **Vue Admin: Liste des utilisateurs non activés**

```typescript
// Filtrer les utilisateurs en attente d'activation
const pendingActivation = users.value.filter(user =>
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
WHERE is_radius_activated = FALSE
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
  COUNT(*) FILTER (WHERE is_active = TRUE AND is_radius_activated = FALSE) AS pending_activation,
  COUNT(*) FILTER (WHERE is_radius_activated = TRUE) AS radius_active,
  COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive
FROM users;
```

---

## 🧪 Tests

### **1. Tester l'inscription**

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

### **2. Tester l'activation RADIUS**

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
┌──────────────────────────────────────────────────────────────────────────┐
│                  SYSTÈME D'ACTIVATION RADIUS                             │
│                    (Un seul mot de passe)                                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   UTILISATEUR    │
│ Tape son mot de  │
│ passe: "Abc123!" │
└────────┬─────────┘
         │
         │ 1. S'inscrit (POST /api/core/auth/register/)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Table: users                                                       │
│  ✅ password = "argon2$argon2id$v=19$..."  (hashé - pour Django)   │
│  ✅ cleartext_password = "Abc123!"  (EN CLAIR - pour RADIUS)       │
│  ✅ is_active = TRUE                                                │
│  ❌ is_radius_activated = FALSE                                     │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ 2. Admin active (POST /api/core/admin/users/activate/)
         │    → Copie cleartext_password dans radcheck
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Table: users                                                       │
│  ✅ is_radius_activated = TRUE                                      │
└─────────────────────────────────────────────────────────────────────┘
         │
         ├───────────────────┬──────────────────┬──────────────────┐
         ▼                   ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Table:       │   │ Table:       │   │ Table:       │   │ RÉSULTAT     │
│ radcheck     │   │ radreply     │   │ radusergroup │   │              │
│              │   │              │   │              │   │              │
│ value =      │   │ ✅ Timeout   │   │ ✅ Group     │   │ Utilisateur  │
│ "Abc123!"    │   │ ✅ Bandwidth │   │              │   │ se connecte  │
│ ✅ EN CLAIR  │   │              │   │              │   │ avec le MÊME │
│              │   │              │   │              │   │ mot de passe │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 🎓 Avantages de cette approche

1. ✅ **Contrôle administratif total** : L'admin décide qui peut accéder au WiFi
2. ✅ **Simplicité pour l'utilisateur** : Un seul mot de passe pour web ET WiFi
3. ✅ **Traçabilité** : Historique de qui a été activé et quand
4. ✅ **Pas de confusion** : L'utilisateur n'a pas à gérer plusieurs mots de passe
5. ✅ **Flexibilité** : Possibilité de désactiver l'accès WiFi sans bloquer l'accès web
6. ✅ **Conformité** : Respect des règles d'accès réseau de l'établissement

## ⚠️ Compromis de sécurité

1. ❌ **Stockage en clair** : Le mot de passe est stocké en clair dans `users.cleartext_password`
2. ❌ **Risque de fuite** : Si la base de données est compromise, tous les mots de passe sont exposés
3. ❌ **Pas de rotation** : L'utilisateur doit changer son mot de passe dans Django ET RADIUS en même temps

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
