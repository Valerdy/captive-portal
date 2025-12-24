# 🚀 Guide de déploiement du système de déconnexion automatique

Ce guide détaille toutes les étapes pour déployer le système de déconnexion automatique des utilisateurs.

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Étape 1: Appliquer les migrations](#étape-1-appliquer-les-migrations)
3. [Étape 2: Tester en mode dry-run](#étape-2-tester-en-mode-dry-run)
4. [Étape 3: Configurer le cron job](#étape-3-configurer-le-cron-job)
5. [Étape 4: Interface frontend utilisateur](#étape-4-interface-frontend-utilisateur)
6. [Étape 5: Interface frontend admin](#étape-5-interface-frontend-admin)
7. [Étape 6: Tests complets](#étape-6-tests-complets)
8. [Surveillance et maintenance](#surveillance-et-maintenance)

---

## Prérequis

✅ Backend Django configuré et fonctionnel
✅ Base de données PostgreSQL/MySQL accessible
✅ FreeRADIUS configuré avec les tables radcheck, radreply, radusergroup
✅ Migration `0015_add_user_disconnection_log.py` créée (déjà fait)

---

## Étape 1: Appliquer les migrations

### 1.1 Activer l'environnement virtuel

```bash
# Si vous utilisez un environnement virtuel
cd /home/user/captive-portal/backend
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows
```

### 1.2 Vérifier les migrations à appliquer

```bash
python manage.py showmigrations core
```

Vous devriez voir:
```
core
 [X] 0001_initial
 [X] 0002_convert_bandwidth_kbps_to_mbps
 ...
 [X] 0014_add_profile_usage_history_alerts
 [ ] 0015_add_user_disconnection_log
```

### 1.3 Appliquer la migration

```bash
python manage.py migrate core
```

### 1.4 Vérifier que la table a été créée

```bash
python manage.py dbshell
```

Puis dans le shell SQL:
```sql
-- PostgreSQL
\dt user_disconnection_logs

-- MySQL
SHOW TABLES LIKE 'user_disconnection_logs';

-- Voir la structure
-- PostgreSQL
\d user_disconnection_logs

-- MySQL
DESCRIBE user_disconnection_logs;
```

Vous devriez voir une table avec les colonnes:
- `id`
- `user_id`
- `reason`
- `description`
- `disconnected_at`
- `reconnected_at`
- `is_active`
- `reconnected_by_id`
- `quota_used`
- `quota_limit`
- `session_duration`

---

## Étape 2: Tester en mode dry-run

Le mode dry-run permet de tester le système **sans effectuer de modifications** dans la base de données.

### 2.1 Exécution basique

```bash
cd /home/user/captive-portal/backend
python manage.py check_and_disconnect_users --dry-run
```

**Sortie attendue:**
```
======================================================================
VÉRIFICATION ET DÉSACTIVATION AUTOMATIQUE DES UTILISATEURS
======================================================================

🔍 MODE DRY-RUN: Aucune modification ne sera effectuée

✓ 42 utilisateurs actifs trouvés

======================================================================
STATISTIQUES
======================================================================

📊 Utilisateurs vérifiés: 42
⊗ Déjà déconnectés: 3

🟡 Seraient désactivés: 5
   - Quota dépassé: 2
   - Limite journalière: 1
   - Limite hebdomadaire: 0
   - Limite mensuelle: 2
   - Validité expirée: 0
   - Session expirée: 0

✅ Vérification terminée
======================================================================

💡 Exécutez sans --dry-run pour effectuer les désactivations
```

### 2.2 Exécution en mode verbose

Pour voir plus de détails sur chaque utilisateur vérifié:

```bash
python manage.py check_and_disconnect_users --dry-run --verbose
```

**Sortie attendue:**
```
======================================================================
VÉRIFICATION ET DÉSACTIVATION AUTOMATIQUE DES UTILISATEURS
======================================================================

🔍 MODE DRY-RUN: Aucune modification ne sera effectuée

✓ 42 utilisateurs actifs trouvés

[1] Vérification: jdoe (John Doe)
  ✓ OK: Aucune limite atteinte

[2] Vérification: jsmith (Jane Smith)
  ✗ QUOTA DÉPASSÉ: Quota dépassé: 55.23 Go / 50 Go
  [DRY-RUN] Désactiverait: jsmith - Quota dépassé: 55.23 Go / 50 Go

[3] Vérification: bmartin (Bob Martin)
  ✗ LIMITE JOURNALIÈRE: Limite journalière atteinte: 5.12 Go / 5 Go
  [DRY-RUN] Désactiverait: bmartin - Limite journalière atteinte: 5.12 Go / 5 Go

...
```

### 2.3 Analyser les résultats

**Points à vérifier:**

✅ Le nombre d'utilisateurs vérifiés correspond au nombre d'utilisateurs actifs avec RADIUS activé
✅ Les utilisateurs déjà déconnectés sont correctement identifiés et ignorés
✅ Les quotas calculés sont corrects (comparer avec la base de données)
✅ Les raisons de déconnexion sont appropriées

**Si les résultats semblent corrects, passez à l'étape suivante.**

---

## Étape 3: Configurer le cron job

Le système doit vérifier périodiquement les quotas. Nous utilisons un cron job pour cela.

### 3.1 Créer un script wrapper

Créez `/home/user/captive-portal/backend/scripts/check_quotas.sh`:

```bash
#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_FILE="/var/log/captive-portal/quota_checks.log"
ERROR_LOG="/var/log/captive-portal/quota_errors.log"

# Créer le dossier de logs s'il n'existe pas
mkdir -p /var/log/captive-portal

# Activer l'environnement virtuel
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Timestamp
echo "========================================" >> "$LOG_FILE"
echo "Vérification des quotas - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Exécuter la commande
cd "$PROJECT_DIR"
python "$MANAGE_PY" check_and_disconnect_users >> "$LOG_FILE" 2>> "$ERROR_LOG"

# Code de sortie
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Vérification terminée avec succès" >> "$LOG_FILE"
else
    echo "❌ Erreur lors de la vérification (code: $EXIT_CODE)" >> "$LOG_FILE"
    # Optionnel: envoyer une alerte
    # mail -s "Erreur vérification quotas" admin@example.com < "$ERROR_LOG"
fi

echo "" >> "$LOG_FILE"
```

### 3.2 Rendre le script exécutable

```bash
chmod +x /home/user/captive-portal/backend/scripts/check_quotas.sh
```

### 3.3 Tester le script

```bash
/home/user/captive-portal/backend/scripts/check_quotas.sh
```

Vérifiez les logs:
```bash
tail -f /var/log/captive-portal/quota_checks.log
```

### 3.4 Configurer le cron job

Ouvrez le crontab:
```bash
crontab -e
```

Ajoutez l'une des configurations suivantes selon vos besoins:

#### Option 1: Vérification toutes les 5 minutes (recommandé pour production)
```cron
*/5 * * * * /home/user/captive-portal/backend/scripts/check_quotas.sh
```

#### Option 2: Vérification toutes les 10 minutes
```cron
*/10 * * * * /home/user/captive-portal/backend/scripts/check_quotas.sh
```

#### Option 3: Vérification toutes les heures
```cron
0 * * * * /home/user/captive-portal/backend/scripts/check_quotas.sh
```

#### Option 4: Vérification toutes les 30 minutes (équilibré)
```cron
*/30 * * * * /home/user/captive-portal/backend/scripts/check_quotas.sh
```

### 3.5 Vérifier que le cron fonctionne

Attendez le délai configuré, puis vérifiez les logs:

```bash
# Voir les dernières vérifications
tail -50 /var/log/captive-portal/quota_checks.log

# Voir les erreurs éventuelles
tail -20 /var/log/captive-portal/quota_errors.log

# Suivre en temps réel
tail -f /var/log/captive-portal/quota_checks.log
```

### 3.6 Script de rotation des logs (optionnel)

Créez `/etc/logrotate.d/captive-portal`:

```
/var/log/captive-portal/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
```

---

## Étape 4: Interface frontend utilisateur

Créez un composant pour afficher l'état de déconnexion aux utilisateurs.

### 4.1 Créer le composant DisconnectionAlert.vue

Fichier: `frontend/portail-captif/src/components/DisconnectionAlert.vue`

```vue
<template>
  <div v-if="disconnectionStatus.is_disconnected" class="disconnection-alert">
    <div class="alert-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
    </div>

    <div class="alert-content">
      <h3>Accès suspendu</h3>
      <p class="reason">{{ disconnectionStatus.reason_display }}</p>
      <p class="description">{{ disconnectionStatus.description }}</p>

      <div v-if="disconnectionStatus.quota_used_gb" class="quota-info">
        <div class="quota-bar">
          <div class="quota-used" :style="{ width: usagePercent + '%' }"></div>
        </div>
        <p class="quota-text">
          {{ disconnectionStatus.quota_used_gb }} Go utilisés / {{ disconnectionStatus.quota_limit_gb }} Go
        </p>
      </div>

      <div class="alert-footer">
        <p class="disconnected-time">
          Déconnecté le {{ formatDate(disconnectionStatus.disconnected_at) }}
        </p>
        <p class="contact-info">
          Pour réactiver votre accès, veuillez contacter l'administrateur réseau.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface DisconnectionStatus {
  is_disconnected: boolean
  reason: string
  reason_display: string
  description: string
  disconnected_at: string
  quota_used_gb: number | null
  quota_limit_gb: number | null
}

const disconnectionStatus = ref<DisconnectionStatus>({
  is_disconnected: false,
  reason: '',
  reason_display: '',
  description: '',
  disconnected_at: '',
  quota_used_gb: null,
  quota_limit_gb: null
})

const usagePercent = computed(() => {
  if (!disconnectionStatus.value.quota_used_gb || !disconnectionStatus.value.quota_limit_gb) {
    return 0
  }
  return Math.min(
    100,
    (disconnectionStatus.value.quota_used_gb / disconnectionStatus.value.quota_limit_gb) * 100
  )
})

const checkDisconnectionStatus = async () => {
  try {
    const response = await axios.get('/api/core/disconnection-logs/current/')
    if (response.data.is_disconnected !== false) {
      disconnectionStatus.value = {
        is_disconnected: true,
        ...response.data
      }
    }
  } catch (error) {
    console.error('Erreur lors de la vérification du statut:', error)
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  checkDisconnectionStatus()
})
</script>

<style scoped>
.disconnection-alert {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  margin: 2rem 0;
  box-shadow: 0 10px 40px rgba(255, 107, 107, 0.3);
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.alert-icon {
  flex-shrink: 0;
}

.alert-icon svg {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.2));
}

.alert-content {
  flex: 1;
}

.alert-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.reason {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0.5rem 0;
  opacity: 0.95;
}

.description {
  font-size: 0.95rem;
  margin: 0.5rem 0 1rem 0;
  opacity: 0.9;
  line-height: 1.5;
}

.quota-info {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.quota-bar {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  height: 20px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.quota-used {
  background: white;
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.quota-text {
  margin: 0;
  font-size: 0.9rem;
  text-align: center;
  font-weight: 600;
}

.alert-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.disconnected-time {
  font-size: 0.85rem;
  opacity: 0.8;
  margin: 0 0 0.5rem 0;
}

.contact-info {
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  border-left: 3px solid white;
}

@media (max-width: 768px) {
  .disconnection-alert {
    flex-direction: column;
    text-align: center;
  }

  .alert-icon {
    margin: 0 auto;
  }
}
</style>
```

### 4.2 Intégrer dans DashboardView.vue

```vue
<template>
  <div class="dashboard">
    <!-- Alerte de déconnexion en haut -->
    <DisconnectionAlert />

    <!-- Reste du dashboard -->
    <div class="dashboard-content">
      <!-- ... -->
    </div>
  </div>
</template>

<script setup lang="ts">
import DisconnectionAlert from '@/components/DisconnectionAlert.vue'
// ... autres imports
</script>
```

---

## Étape 5: Interface frontend admin

Créez une interface pour que les admins puissent voir et réactiver les utilisateurs.

### 5.1 Créer AdminDisconnectionsView.vue

Fichier: `frontend/portail-captif/src/views/AdminDisconnectionsView.vue`

```vue
<template>
  <div class="admin-disconnections">
    <div class="page-header">
      <h1>Déconnexions automatiques</h1>
      <p class="page-description">
        Gérer les utilisateurs déconnectés automatiquement pour dépassement de quota
      </p>
    </div>

    <!-- Filtres -->
    <div class="filters">
      <div class="filter-group">
        <label>Statut</label>
        <select v-model="filters.status">
          <option value="all">Tous</option>
          <option value="active">Déconnectés (actifs)</option>
          <option value="reconnected">Réactivés</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Raison</label>
        <select v-model="filters.reason">
          <option value="">Toutes</option>
          <option value="quota_exceeded">Quota dépassé</option>
          <option value="daily_limit">Limite journalière</option>
          <option value="weekly_limit">Limite hebdomadaire</option>
          <option value="monthly_limit">Limite mensuelle</option>
          <option value="validity_expired">Validité expirée</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Recherche</label>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Username, nom..."
          class="search-input"
        />
      </div>

      <button @click="refreshData" class="btn-refresh">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
        </svg>
        Actualiser
      </button>
    </div>

    <!-- Statistiques -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_active }}</div>
        <div class="stat-label">Déconnectés actuellement</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.today }}</div>
        <div class="stat-label">Aujourd'hui</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.week }}</div>
        <div class="stat-label">Cette semaine</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ stats.reconnected }}</div>
        <div class="stat-label">Réactivés</div>
      </div>
    </div>

    <!-- Liste des déconnexions -->
    <div class="disconnections-table">
      <table>
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th>Raison</th>
            <th>Détails</th>
            <th>Déconnecté le</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id" :class="{ inactive: !log.is_active }">
            <td>
              <div class="user-info">
                <div class="user-name">{{ log.user_full_name }}</div>
                <div class="user-username">{{ log.user_username }}</div>
              </div>
            </td>
            <td>
              <span class="reason-badge" :class="'reason-' + log.reason">
                {{ log.reason_display }}
              </span>
            </td>
            <td>
              <div class="details">
                {{ log.description }}
                <div v-if="log.quota_used_gb" class="quota-details">
                  {{ log.quota_used_gb }} Go / {{ log.quota_limit_gb }} Go
                </div>
              </div>
            </td>
            <td>
              <div class="date-info">
                {{ formatDate(log.disconnected_at) }}
              </div>
            </td>
            <td>
              <span v-if="log.is_active" class="status-badge active">
                🔴 Déconnecté
              </span>
              <span v-else class="status-badge reconnected">
                ✅ Réactivé
                <div class="reconnected-info">
                  {{ formatDate(log.reconnected_at) }}
                  <br>
                  par {{ log.reconnected_by_username || 'Système' }}
                </div>
              </span>
            </td>
            <td>
              <button
                v-if="log.is_active"
                @click="reactivateUser(log)"
                class="btn-reactivate"
                :disabled="loading"
              >
                Réactiver
              </button>
              <span v-else class="already-reconnected">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredLogs.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M12 6v6l4 2"></path>
        </svg>
        <p>Aucune déconnexion trouvée</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="pagination.total > pagination.pageSize" class="pagination">
      <button
        @click="changePage(pagination.currentPage - 1)"
        :disabled="pagination.currentPage === 1"
        class="btn-page"
      >
        Précédent
      </button>
      <span class="page-info">
        Page {{ pagination.currentPage }} / {{ pagination.totalPages }}
      </span>
      <button
        @click="changePage(pagination.currentPage + 1)"
        :disabled="pagination.currentPage === pagination.totalPages"
        class="btn-page"
      >
        Suivant
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface DisconnectionLog {
  id: number
  user_username: string
  user_full_name: string
  reason: string
  reason_display: string
  description: string
  disconnected_at: string
  reconnected_at: string | null
  is_active: boolean
  quota_used_gb: number | null
  quota_limit_gb: number | null
  reconnected_by_username: string | null
}

const logs = ref<DisconnectionLog[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filters = ref({
  status: 'active',
  reason: ''
})

const pagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0
})

const stats = ref({
  total_active: 0,
  today: 0,
  week: 0,
  reconnected: 0
})

const filteredLogs = computed(() => {
  let result = logs.value

  // Filtre par statut
  if (filters.value.status === 'active') {
    result = result.filter(log => log.is_active)
  } else if (filters.value.status === 'reconnected') {
    result = result.filter(log => !log.is_active)
  }

  // Filtre par raison
  if (filters.value.reason) {
    result = result.filter(log => log.reason === filters.value.reason)
  }

  // Recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(log =>
      log.user_username.toLowerCase().includes(query) ||
      log.user_full_name.toLowerCase().includes(query)
    )
  }

  return result
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/core/disconnection-logs/', {
      params: {
        page: pagination.value.currentPage,
        page_size: pagination.value.pageSize
      }
    })

    logs.value = response.data.results
    pagination.value.total = response.data.count
    pagination.value.totalPages = Math.ceil(response.data.count / pagination.value.pageSize)

    calculateStats()
  } catch (error) {
    console.error('Erreur lors du chargement des logs:', error)
    alert('Erreur lors du chargement des déconnexions')
  } finally {
    loading.value = false
  }
}

const calculateStats = () => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

  stats.value = {
    total_active: logs.value.filter(log => log.is_active).length,
    today: logs.value.filter(log => {
      const disconnectedAt = new Date(log.disconnected_at)
      return disconnectedAt >= today && log.is_active
    }).length,
    week: logs.value.filter(log => {
      const disconnectedAt = new Date(log.disconnected_at)
      return disconnectedAt >= weekAgo && log.is_active
    }).length,
    reconnected: logs.value.filter(log => !log.is_active).length
  }
}

const reactivateUser = async (log: DisconnectionLog) => {
  if (!confirm(`Voulez-vous réactiver l'utilisateur ${log.user_full_name} (${log.user_username}) ?`)) {
    return
  }

  loading.value = true
  try {
    const response = await axios.post(`/api/core/disconnection-logs/${log.id}/reactivate/`)

    alert(`✅ ${response.data.message}`)

    // Rafraîchir les données
    await fetchLogs()
  } catch (error: any) {
    console.error('Erreur lors de la réactivation:', error)
    const errorMsg = error.response?.data?.error || 'Erreur lors de la réactivation'
    alert(`❌ ${errorMsg}`)
  } finally {
    loading.value = false
  }
}

const changePage = (page: number) => {
  pagination.value.currentPage = page
  fetchLogs()
}

const refreshData = () => {
  fetchLogs()
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.admin-disconnections {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.page-description {
  color: #7f8c8d;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.filter-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c3e50;
}

.filter-group select,
.search-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  align-self: flex-end;
}

.btn-refresh:hover {
  background: #2980b9;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #e74c3c;
}

.stat-card.success {
  border-left-color: #27ae60;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 0.5rem;
}

.disconnections-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f9fa;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #dee2e6;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

tr.inactive {
  opacity: 0.6;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-name {
  font-weight: 600;
  color: #2c3e50;
}

.user-username {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.reason-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  background: #e74c3c;
  color: white;
}

.reason-quota_exceeded {
  background: #e74c3c;
}

.reason-daily_limit,
.reason-weekly_limit,
.reason-monthly_limit {
  background: #f39c12;
}

.reason-validity_expired {
  background: #95a5a6;
}

.details {
  font-size: 0.9rem;
  color: #555;
}

.quota-details {
  font-size: 0.8rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

.date-info {
  font-size: 0.9rem;
  color: #555;
}

.status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #ffe5e5;
  color: #e74c3c;
}

.status-badge.reconnected {
  background: #d4edda;
  color: #27ae60;
}

.reconnected-info {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  opacity: 0.8;
}

.btn-reactivate {
  padding: 0.5rem 1rem;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-reactivate:hover {
  background: #229954;
}

.btn-reactivate:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.already-reconnected {
  color: #bdc3c7;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: #95a5a6;
}

.empty-state svg {
  margin-bottom: 1rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-page {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-page:hover:not(:disabled) {
  background: #f8f9fa;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-weight: 500;
  color: #2c3e50;
}
</style>
```

### 5.2 Ajouter la route

Fichier: `frontend/portail-captif/src/router/index.ts`

```typescript
{
  path: '/admin/disconnections',
  name: 'AdminDisconnections',
  component: () => import('@/views/AdminDisconnectionsView.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

### 5.3 Ajouter au menu admin

Ajoutez un lien dans le menu de navigation admin:

```vue
<router-link to="/admin/disconnections" class="nav-link">
  <svg><!-- icon --></svg>
  Déconnexions
</router-link>
```

---

## Étape 6: Tests complets

### 6.1 Test 1: Déconnexion par quota

**Objectif:** Vérifier qu'un utilisateur est déconnecté quand il dépasse son quota

**Étapes:**
1. Créer un utilisateur de test avec un profil de 1 Go
2. Simuler une consommation de 1.1 Go dans `radacct`
3. Attendre que le cron s'exécute (ou lancer manuellement)
4. Vérifier que l'utilisateur a `statut=0` dans `radcheck`
5. Vérifier qu'un log est créé dans `user_disconnection_logs`

**Script de test:**
```sql
-- 1. Vérifier l'utilisateur
SELECT username, attribute, value, statut FROM radcheck WHERE username = 'testuser';

-- 2. Vérifier le log de déconnexion
SELECT * FROM user_disconnection_logs WHERE user_id = (SELECT id FROM core_user WHERE username = 'testuser');

-- 3. Vérifier que l'utilisateur ne peut plus se connecter (statut=0)
SELECT username, statut FROM radcheck WHERE username = 'testuser' AND attribute = 'Cleartext-Password';
```

### 6.2 Test 2: Réactivation admin

**Objectif:** Vérifier qu'un admin peut réactiver un utilisateur

**Étapes:**
1. Se connecter en tant qu'admin
2. Aller dans la page "Déconnexions"
3. Cliquer sur "Réactiver" pour l'utilisateur test
4. Vérifier que `statut=1` dans `radcheck`
5. Vérifier que `is_active=false` dans le log
6. Vérifier que l'utilisateur peut se reconnecter

### 6.3 Test 3: Affichage utilisateur

**Objectif:** Vérifier que l'utilisateur voit son statut de déconnexion

**Étapes:**
1. Se connecter avec un utilisateur déconnecté
2. Vérifier que l'alerte de déconnexion s'affiche
3. Vérifier que la raison est claire
4. Vérifier que le quota utilisé/limite est affiché

### 6.4 Test 4: Limites périodiques

**Objectif:** Vérifier les limites journalières, hebdomadaires, mensuelles

**Étapes:**
1. Créer un profil avec limite journalière de 500 Mo
2. Assigner à un utilisateur
3. Simuler 600 Mo de consommation aujourd'hui
4. Lancer le check
5. Vérifier la déconnexion avec raison "daily_limit"

### 6.5 Test 5: Validité expirée

**Objectif:** Vérifier qu'un utilisateur est déconnecté quand sa validité expire

**Étapes:**
1. Créer un profil avec `validity_duration = 7` jours
2. Assigner à un utilisateur et activer
3. Modifier `activation_date` à il y a 8 jours:
```sql
UPDATE user_profile_usage
SET activation_date = NOW() - INTERVAL 8 DAY
WHERE user_id = (SELECT id FROM core_user WHERE username = 'testuser');
```
4. Lancer le check
5. Vérifier la déconnexion avec raison "validity_expired"

---

## Surveillance et maintenance

### Script de monitoring

Créez `/home/user/captive-portal/backend/scripts/monitor_disconnections.sh`:

```bash
#!/bin/bash

echo "=== Rapport de déconnexions - $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

cd /home/user/captive-portal/backend

# Activer venv si nécessaire
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Statistiques rapides
python manage.py shell << 'EOF'
from core.models import UserDisconnectionLog
from django.utils import timezone
from datetime import timedelta

now = timezone.now()
today = now.replace(hour=0, minute=0, second=0, microsecond=0)
week_ago = now - timedelta(days=7)

total_active = UserDisconnectionLog.objects.filter(is_active=True).count()
today_count = UserDisconnectionLog.objects.filter(
    disconnected_at__gte=today,
    is_active=True
).count()
week_count = UserDisconnectionLog.objects.filter(
    disconnected_at__gte=week_ago,
    is_active=True
).count()

print(f"📊 Utilisateurs déconnectés actuellement: {total_active}")
print(f"📅 Déconnexions aujourd'hui: {today_count}")
print(f"📆 Déconnexions cette semaine: {week_count}")
print("")

# Top raisons
print("🔝 Top raisons de déconnexion:")
from django.db.models import Count
reasons = UserDisconnectionLog.objects.filter(is_active=True).values('reason').annotate(count=Count('id')).order_by('-count')
for r in reasons:
    print(f"   - {r['reason']}: {r['count']}")

EOF
```

Rendez-le exécutable:
```bash
chmod +x /home/user/captive-portal/backend/scripts/monitor_disconnections.sh
```

Ajoutez au crontab pour un rapport quotidien:
```cron
0 9 * * * /home/user/captive-portal/backend/scripts/monitor_disconnections.sh | mail -s "Rapport quotidien - Déconnexions" admin@example.com
```

### Alertes critiques

Si plus de 10 utilisateurs sont déconnectés en 1 heure:

```bash
#!/bin/bash

THRESHOLD=10
COUNT=$(python manage.py shell -c "
from core.models import UserDisconnectionLog
from django.utils import timezone
from datetime import timedelta

count = UserDisconnectionLog.objects.filter(
    disconnected_at__gte=timezone.now() - timedelta(hours=1),
    is_active=True
).count()
print(count)
" | tail -1)

if [ "$COUNT" -gt "$THRESHOLD" ]; then
    echo "⚠️ ALERTE: $COUNT utilisateurs déconnectés en 1 heure" | mail -s "ALERTE Déconnexions" admin@example.com
fi
```

---

## ✅ Checklist finale

- [ ] Migration 0015 appliquée avec succès
- [ ] Table `user_disconnection_logs` créée
- [ ] Commande `check_and_disconnect_users` testée en dry-run
- [ ] Cron job configuré et fonctionnel
- [ ] Script wrapper créé et testé
- [ ] Logs rotatifs configurés
- [ ] Composant `DisconnectionAlert.vue` créé
- [ ] Vue admin `AdminDisconnectionsView.vue` créée
- [ ] Route admin ajoutée
- [ ] Menu admin mis à jour
- [ ] Tests de déconnexion par quota réussis
- [ ] Tests de réactivation réussis
- [ ] Tests d'affichage utilisateur réussis
- [ ] Tests des limites périodiques réussis
- [ ] Tests de validité expirée réussis
- [ ] Script de monitoring créé
- [ ] Documentation à jour

---

## 🆘 Dépannage

### Le cron ne s'exécute pas

```bash
# Vérifier que cron est actif
systemctl status cron

# Vérifier les logs cron
grep CRON /var/log/syslog

# Tester le script manuellement
/home/user/captive-portal/backend/scripts/check_quotas.sh
```

### Les utilisateurs ne sont pas déconnectés

```bash
# Exécuter en mode verbose
python manage.py check_and_disconnect_users --verbose

# Vérifier les profils
python manage.py shell -c "
from core.models import User
for u in User.objects.filter(is_radius_activated=True):
    print(f'{u.username}: profile={u.get_effective_profile()}')
"
```

### Erreur lors de la réactivation

```sql
-- Vérifier l'état dans radcheck
SELECT * FROM radcheck WHERE username = 'USERNAME';

-- Réactiver manuellement si nécessaire
UPDATE radcheck SET statut = 1 WHERE username = 'USERNAME';
```

---

## 📚 Ressources

- Documentation Django: https://docs.djangoproject.com/
- Documentation FreeRADIUS: https://freeradius.org/documentation/
- Cron: `man crontab`
- Guide AUTO_DISCONNECT_SYSTEM.md pour plus de détails techniques

---

**🎉 Système de déconnexion automatique prêt à l'emploi !**
