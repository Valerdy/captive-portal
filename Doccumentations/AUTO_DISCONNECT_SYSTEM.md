# 🔒 Système de Désactivation Automatique des Utilisateurs

## 📋 Vue d'ensemble

Ce système désactive automatiquement les utilisateurs qui atteignent leurs limites (quota de données, durée de session, etc.) et empêche leur reconnexion jusqu'à ce qu'un administrateur les réactive manuellement.

### Fonctionnement général

```
1. Utilisateur consomme ses ressources
   ⬇️
2. Cron vérifie les limites toutes les 15 minutes
   ⬇️
3. Si limite atteinte: statut=0 dans radcheck + log créé
   ⬇️
4. Utilisateur déconnecté + reconnexion bloquée
   ⬇️
5. Utilisateur voit la raison sur le portail
   ⬇️
6. Admin réactive → statut=1 + utilisateur peut se reconnecter
```

---

## 🎯 Limites surveillées

Le système surveille automatiquement :

| Limite | Description | Raison log |
|--------|-------------|------------|
| **Quota total** | Volume de données du profil | `quota_exceeded` |
| **Limite journalière** | Limite daily_limit du profil | `daily_limit` |
| **Limite hebdomadaire** | Limite weekly_limit du profil | `weekly_limit` |
| **Limite mensuelle** | Limite monthly_limit du profil | `monthly_limit` |
| **Durée de validité** | validity_duration du profil | `validity_expired` |
| **Session timeout** | Durée maximale de session | `session_expired` |
| **Idle timeout** | Délai d'inactivité | `idle_timeout` |

---

## 🗄️ Base de données

### Table: `user_disconnection_logs`

```sql
CREATE TABLE user_disconnection_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    reason VARCHAR(50) NOT NULL,
    description TEXT,
    disconnected_at DATETIME NOT NULL,
    reconnected_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    reconnected_by_id INTEGER,
    quota_used BIGINT,
    quota_limit BIGINT,
    session_duration INTEGER,
    FOREIGN KEY (user_id) REFERENCES core_user(id),
    FOREIGN KEY (reconnected_by_id) REFERENCES core_user(id)
);
```

### Modification de `radcheck`

Le champ `statut` dans `radcheck` contrôle l'accès :
- `statut=1` (True) : Utilisateur peut se connecter
- `statut=0` (False) : Utilisateur bloqué

```sql
-- Désactiver un utilisateur
UPDATE radcheck SET statut = 0 WHERE username = 'john_doe';

-- Réactiver un utilisateur
UPDATE radcheck SET statut = 1 WHERE username = 'john_doe';
```

---

## ⚙️ Installation et Configuration

### 1. Créer la migration Django

```bash
cd /home/user/captive-portal/backend
python manage.py makemigrations
python manage.py migrate
```

### 2. Configurer le cron job

Ajoutez cette ligne au crontab pour vérifier toutes les 15 minutes :

```bash
crontab -e
```

Ajoutez :
```
*/15 * * * * cd /home/user/captive-portal/backend && /path/to/python manage.py check_and_disconnect_users >> /var/log/auto_disconnect.log 2>&1
```

Ou toutes les 5 minutes pour un contrôle plus strict :
```
*/5 * * * * cd /home/user/captive-portal/backend && /path/to/python manage.py check_and_disconnect_users >> /var/log/auto_disconnect.log 2>&1
```

### 3. Tester le système

Mode test (sans désactiver réellement) :
```bash
python manage.py check_and_disconnect_users --dry-run
```

Mode verbeux (plus de détails) :
```bash
python manage.py check_and_disconnect_users --verbose
```

Mode réel :
```bash
python manage.py check_and_disconnect_users
```

---

## 📊 Commande: `check_and_disconnect_users`

### Usage

```bash
python manage.py check_and_disconnect_users [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Mode test : affiche ce qui serait fait sans le faire |
| `--verbose` | Affiche les détails de chaque utilisateur vérifié |

### Sortie exemple

```
======================================================================
VÉRIFICATION ET DÉSACTIVATION AUTOMATIQUE DES UTILISATEURS
======================================================================

⚠️  MODE RÉEL: Les utilisateurs seront désactivés

✓ 45 utilisateurs actifs trouvés

[1] Vérification: john_doe (John Doe)
  ✗ QUOTA DÉPASSÉ: Quota dépassé: 52.3 Go / 50 Go
  ✗ DÉSACTIVÉ: john_doe - Quota dépassé: 52.3 Go / 50 Go
     → 2 entrée(s) RadCheck mises à jour (statut=0)

[2] Vérification: jane_smith (Jane Smith)
  ✓ OK: Aucune limite atteinte

...

======================================================================
STATISTIQUES
======================================================================

📊 Utilisateurs vérifiés: 45
⊗ Déjà déconnectés: 3

🔴 Total désactivés: 5
   - Quota dépassé: 3
   - Limite journalière: 1
   - Limite mensuelle: 0
   - Validité expirée: 1

✅ Vérification terminée
```

---

## 🔌 API Endpoints

### 1. Liste des logs (Admin uniquement)

```http
GET /api/core/disconnection-logs/
```

**Query params:**
- `is_active` : `true` | `false` - Filtrer par statut actif
- `reason` : `quota_exceeded` | `daily_limit` | etc. - Filtrer par raison

**Réponse:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "user": 5,
      "user_username": "john_doe",
      "user_full_name": "John Doe",
      "reason": "quota_exceeded",
      "reason_display": "Quota de données dépassé",
      "description": "Quota dépassé: 52.3 Go / 50 Go",
      "disconnected_at": "2025-12-11T14:30:00Z",
      "reconnected_at": null,
      "is_active": true,
      "quota_used": 56106127360,
      "quota_limit": 53687091200,
      "quota_used_gb": 52.3,
      "quota_limit_gb": 50.0
    }
  ]
}
```

### 2. Statut actuel de l'utilisateur connecté

```http
GET /api/core/disconnection-logs/current/
```

**Réponse (si déconnecté):**
```json
{
  "id": 1,
  "user_username": "john_doe",
  "reason": "quota_exceeded",
  "reason_display": "Quota de données dépassé",
  "description": "Quota dépassé: 52.3 Go / 50 Go",
  "disconnected_at": "2025-12-11T14:30:00Z",
  "quota_used_gb": 52.3,
  "quota_limit_gb": 50.0
}
```

**Réponse (si OK):**
```json
{
  "is_disconnected": false,
  "message": "Aucune déconnexion active"
}
```

### 3. Réactiver un utilisateur (Admin uniquement)

```http
POST /api/core/disconnection-logs/{id}/reactivate/
```

**Réponse:**
```json
{
  "message": "Utilisateur john_doe réactivé avec succès",
  "radcheck_updated": 2,
  "reconnected_at": "2025-12-11T15:45:00Z",
  "reconnected_by": "admin"
}
```

---

## 🎨 Intégration Frontend

### 1. Vérifier le statut au chargement du dashboard

```typescript
// Dans le composant Dashboard.vue
import { ref, onMounted } from 'vue'
import axios from 'axios'

const disconnectionStatus = ref(null)
const isDisconnected = ref(false)

onMounted(async () => {
  try {
    const response = await axios.get('/api/core/disconnection-logs/current/')
    if (response.data.is_disconnected !== false) {
      isDisconnected.value = true
      disconnectionStatus.value = response.data
    }
  } catch (error) {
    console.error('Erreur vérification statut:', error)
  }
})
```

### 2. Afficher le message de blocage

```vue
<template>
  <div v-if="isDisconnected" class="disconnection-alert">
    <h2>🚫 Accès Internet Suspendu</h2>
    <p><strong>Raison:</strong> {{ disconnectionStatus.reason_display }}</p>
    <p>{{ disconnectionStatus.description }}</p>

    <div v-if="disconnectionStatus.reason === 'quota_exceeded'" class="quota-info">
      <p>Quota utilisé: <strong>{{ disconnectionStatus.quota_used_gb }} Go</strong></p>
      <p>Limite: <strong>{{ disconnectionStatus.quota_limit_gb }} Go</strong></p>
    </div>

    <p class="help-text">
      Veuillez contacter un administrateur pour réactiver votre accès.
    </p>

    <p class="disconnected-at">
      Déconnecté le: {{ formatDate(disconnectionStatus.disconnected_at) }}
    </p>
  </div>
</template>

<style scoped>
.disconnection-alert {
  background: #FEE2E2;
  border: 2px solid #DC2626;
  border-radius: 8px;
  padding: 2rem;
  margin: 2rem 0;
  text-align: center;
}

.quota-info {
  margin: 1rem 0;
  padding: 1rem;
  background: white;
  border-radius: 4px;
}

.help-text {
  margin-top: 1.5rem;
  font-size: 1.1rem;
  color: #374151;
}

.disconnected-at {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #6B7280;
}
</style>
```

### 3. Interface Admin pour réactiver

```vue
<template>
  <div class="disconnected-users-list">
    <h3>Utilisateurs déconnectés</h3>

    <table>
      <thead>
        <tr>
          <th>Utilisateur</th>
          <th>Raison</th>
          <th>Description</th>
          <th>Depuis</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in disconnectedLogs" :key="log.id">
          <td>{{ log.user_full_name }} ({{ log.user_username }})</td>
          <td>{{ log.reason_display }}</td>
          <td>{{ log.description }}</td>
          <td>{{ formatDate(log.disconnected_at) }}</td>
          <td>
            <button @click="reactivate(log.id)" class="btn-reactivate">
              Réactiver
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const disconnectedLogs = ref([])

onMounted(async () => {
  await loadDisconnectedUsers()
})

async function loadDisconnectedUsers() {
  try {
    const response = await axios.get('/api/core/disconnection-logs/?is_active=true')
    disconnectedLogs.value = response.data.results
  } catch (error) {
    console.error('Erreur chargement logs:', error)
  }
}

async function reactivate(logId: number) {
  if (!confirm('Voulez-vous vraiment réactiver cet utilisateur ?')) return

  try {
    await axios.post(`/api/core/disconnection-logs/${logId}/reactivate/`)
    alert('Utilisateur réactivé avec succès')
    await loadDisconnectedUsers()
  } catch (error) {
    console.error('Erreur réactivation:', error)
    alert('Erreur lors de la réactivation')
  }
}
</script>
```

---

## 🔍 Scénarios d'utilisation

### Scénario 1: Quota dépassé

1. **État initial:** John a un profil avec 50 Go de quota
2. **Action:** John consomme 52 Go
3. **Détection:** Le cron détecte le dépassement
4. **Résultat:**
   - `radcheck.statut = 0` pour John
   - Log créé avec reason=`quota_exceeded`
   - John est déconnecté et ne peut plus se reconnecter
5. **Notification:** John voit "Quota dépassé: 52 Go / 50 Go"
6. **Résolution:** Admin clique "Réactiver" → `statut=1` → John peut se reconnecter

### Scénario 2: Limite journalière

1. **État initial:** Jane a un profil avec daily_limit=5 Go
2. **Action:** Jane consomme 6 Go aujourd'hui
3. **Détection:** Le cron détecte le dépassement journalier
4. **Résultat:** Désactivation automatique
5. **Auto-résolution:** À minuit, les quotas journaliers se réinitialisent
6. **Option:** Admin peut réactiver manuellement avant minuit

### Scénario 3: Durée de validité expirée

1. **État initial:** Bob a un profil avec validity_duration=30 jours
2. **Action:** 31 jours se sont écoulés depuis l'activation
3. **Détection:** Le cron détecte l'expiration
4. **Résultat:** Désactivation avec reason=`validity_expired`
5. **Résolution:** Admin renouvelle le profil puis réactive

---

## 📝 Logs et Monitoring

### Fichier de log

Les logs du cron sont stockés dans :
```
/var/log/auto_disconnect.log
```

### Consulter les logs

```bash
# Dernières exécutions
tail -100 /var/log/auto_disconnect.log

# Rechercher les déconnexions
grep "DÉSACTIVÉ" /var/log/auto_disconnect.log

# Statistiques
grep "Total désactivés" /var/log/auto_disconnect.log
```

### Monitoring via Django Admin

Ajoutez dans `admin.py` :
```python
from django.contrib import admin
from .models import UserDisconnectionLog

@admin.register(UserDisconnectionLog)
class UserDisconnectionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'reason', 'disconnected_at', 'is_active']
    list_filter = ['reason', 'is_active', 'disconnected_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['disconnected_at', 'reconnected_at']

    def has_add_permission(self, request):
        return False  # Logs créés automatiquement
```

---

## 🛡️ Sécurité et Permissions

### Permissions API

| Endpoint | Permission | Description |
|----------|-----------|-------------|
| `GET /disconnection-logs/` | Admin | Liste tous les logs |
| `GET /disconnection-logs/current/` | Authentifié | Son propre statut |
| `POST /disconnection-logs/{id}/reactivate/` | Admin | Réactiver un user |

### Considérations

- ✅ Les utilisateurs ne voient que leurs propres logs
- ✅ Seuls les admins peuvent réactiver
- ✅ Les logs sont en lecture seule (pas de modification manuelle)
- ✅ Transactions atomiques pour la réactivation
- ✅ Historique complet de qui a réactivé quand

---

## 🧪 Tests

### Test 1: Vérifier le dry-run

```bash
python manage.py check_and_disconnect_users --dry-run --verbose
```

Vérifie que :
- Les utilisateurs sont analysés correctement
- Les limites sont détectées
- Aucune modification n'est faite

### Test 2: Désactiver manuellement un utilisateur

```python
from core.models import User, UserDisconnectionLog
from radius.models import RadCheck

# Créer un log de test
user = User.objects.get(username='test_user')
log = UserDisconnectionLog.objects.create(
    user=user,
    reason='manual',
    description='Test de désactivation manuelle',
    is_active=True
)

# Désactiver dans radcheck
RadCheck.objects.filter(username='test_user').update(statut=False)

# Vérifier
print(f"Statut radcheck: {RadCheck.objects.filter(username='test_user').first().statut}")
# Doit afficher: False
```

### Test 3: Tester la réactivation

```bash
curl -X POST \
  http://localhost:8000/api/core/disconnection-logs/1/reactivate/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Vérifie que :
- Log marqué comme `is_active=False`
- `reconnected_at` est rempli
- `radcheck.statut=1` est restauré

---

## 🔧 Troubleshooting

### Problème: Les utilisateurs ne sont pas désactivés

**Causes possibles:**
1. Le cron n'est pas configuré
2. Le cron ne s'exécute pas
3. Problème de permissions

**Solutions:**
```bash
# Vérifier le cron
crontab -l

# Tester manuellement
python manage.py check_and_disconnect_users --verbose

# Vérifier les logs
tail -50 /var/log/auto_disconnect.log
```

### Problème: Utilisateur ne peut pas se reconnecter après réactivation

**Causes possibles:**
1. Le statut n'a pas été mis à jour dans radcheck
2. Cache RADIUS

**Solutions:**
```bash
# Vérifier le statut dans la DB
mysql -u root -p radius -e "SELECT * FROM radcheck WHERE username='john_doe' AND attribute='Cleartext-Password';"

# Forcer la mise à jour
python manage.py shell
>>> from radius.models import RadCheck
>>> RadCheck.objects.filter(username='john_doe').update(statut=True)

# Redémarrer FreeRADIUS
systemctl restart freeradius
```

### Problème: Trop d'utilisateurs désactivés

**Cause:** Les limites sont peut-être trop strictes

**Solution:**
```bash
# Analyser les raisons
python manage.py shell
>>> from core.models import UserDisconnectionLog
>>> from collections import Counter
>>> reasons = UserDisconnectionLog.objects.filter(is_active=True).values_list('reason', flat=True)
>>> Counter(reasons)

# Ajuster les profils selon les besoins
```

---

## 📊 Métriques et Statistiques

### Requêtes SQL utiles

```sql
-- Nombre total de déconnexions actives
SELECT COUNT(*) FROM user_disconnection_logs WHERE is_active = 1;

-- Répartition par raison
SELECT reason, COUNT(*) as count
FROM user_disconnection_logs
WHERE is_active = 1
GROUP BY reason;

-- Utilisateurs déconnectés le plus souvent
SELECT user_id, COUNT(*) as disconnect_count
FROM user_disconnection_logs
GROUP BY user_id
ORDER BY disconnect_count DESC
LIMIT 10;

-- Temps moyen avant réactivation
SELECT AVG(TIMESTAMPDIFF(MINUTE, disconnected_at, reconnected_at)) as avg_minutes
FROM user_disconnection_logs
WHERE reconnected_at IS NOT NULL;
```

---

## ✅ Checklist de déploiement

- [ ] Migration Django créée et appliquée
- [ ] Cron job configuré
- [ ] Test en dry-run effectué
- [ ] Test de désactivation manuelle OK
- [ ] Test de réactivation OK
- [ ] Interface frontend ajoutée
- [ ] Logs monitoring configurés
- [ ] Documentation équipe mise à jour
- [ ] Test avec utilisateur réel
- [ ] Notifications admins configurées (optionnel)

---

## 🚀 Améliorations futures

1. **Notifications email/SMS**
   - Prévenir l'utilisateur avant la déconnexion (80%, 90%, 95%)
   - Email à l'admin quand utilisateur déconnecté

2. **Réactivation automatique**
   - Pour les limites périodiques (daily, weekly, monthly)
   - Script qui réactive à minuit/début de semaine/début de mois

3. **Dashboard metrics**
   - Graphiques des déconnexions par jour
   - Top utilisateurs déconnectés
   - Raisons les plus fréquentes

4. **API Webhooks**
   - Notifier un système externe lors d'une déconnexion
   - Intégration avec systèmes de ticketing

---

**Système développé pour une gestion automatique et transparente des limites d'accès Internet.**
