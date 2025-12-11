# Intégration des Statistiques de Profils au Dashboard Admin

Ce document contient les modifications à apporter à `AdminDashboardView.vue` pour intégrer les statistiques de profils.

## 1. Imports et Stores (Lignes 1-20)

### Ajouter cet import :
```typescript
import { useProfileStore } from '@/stores/profile'
```

### Ajouter cette initialisation après line 17 :
```typescript
const profileStore = useProfileStore()
```

## 2. Chargement des données onMounted (Ligne 252-256)

### Modifier Promise.all pour inclure les statistiques de profils :
```typescript
await Promise.all([
  userStore.fetchUsers(),
  sessionStore.fetchSessions(),
  deviceStore.fetchDevices(),
  profileStore.fetchStatistics()  // AJOUT
])
```

## 3. Stats Computed - Ajouter après line 77

```typescript
// Stats de profils
const profileStats = computed(() => {
  if (!profileStore.statistics) return null
  return profileStore.statistics.summary
})

const topProfiles = computed(() => {
  if (!profileStore.statistics) return []
  return profileStore.statistics.top_profiles || []
})
```

## 4. Graphique Top 5 Profils - Ajouter après line 242

```typescript
// Graphique Top 5 profils les plus utilisés
const topProfilesChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#10B981'],
  plotOptions: {
    bar: {
      borderRadius: 8,
      columnWidth: '70%',
      distributed: false
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: topProfiles.value.map(p => p.profile_name),
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      rotate: -45,
      rotateAlways: true
    }
  },
  yaxis: {
    title: { text: 'Nombre d\'utilisateurs' },
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${Math.round(val)}`
    }
  },
  grid: { borderColor: '#E5E7EB' },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} utilisateurs` }
  }
}))

const topProfilesChartSeries = computed(() => {
  return [{
    name: 'Utilisateurs',
    data: topProfiles.value.map(p => p.total_users)
  }]
})

// Graphique de répartition des types de quotas
const quotaTypesPieChartOptions = computed(() => ({
  chart: {
    type: 'donut',
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#3B82F6', '#F59E0B'],
  labels: ['Quotas Limités', 'Quotas Illimités'],
  legend: {
    position: 'bottom',
    fontSize: '14px',
    fontWeight: 500
  },
  plotOptions: {
    pie: {
      donut: {
        size: '70%',
        labels: {
          show: true,
          total: {
            show: true,
            label: 'Total',
            fontSize: '16px',
            fontWeight: 600,
            color: '#1F2937'
          }
        }
      }
    }
  },
  dataLabels: { enabled: false },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} profils` }
  }
}))

const quotaTypesPieChartSeries = computed(() => {
  if (!profileStats.value) return [0, 0]
  return [
    profileStats.value.limited_profiles || 0,
    profileStats.value.unlimited_profiles || 0
  ]
})
```

## 5. Template - Nouvelles cartes de stats

### Ajouter ces 2 cartes dans la section `.stats-grid` (après line 327) :

```vue
          <div class="stat-card">
            <div class="stat-icon profiles">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ profileStats?.total_profiles || 0 }}</h3>
              <p>Profils créés</p>
              <span class="stat-badge success">{{ profileStats?.active_profiles || 0 }} actifs</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon quota">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ profileStats?.limited_profiles || 0 }}</h3>
              <p>Profils avec quota limité</p>
              <span class="stat-badge warning">{{ profileStats?.unlimited_profiles || 0 }} illimités</span>
            </div>
          </div>
```

## 6. Template - Nouveaux graphiques

### Ajouter dans la section `.charts-section` (après line 375, après le graphique sessions) :

```vue
          <div class="chart-card">
            <div class="chart-header">
              <h2>Top 5 Profils les Plus Utilisés</h2>
              <p class="chart-subtitle">Nombre d'utilisateurs par profil</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="topProfiles.length > 0"
                type="bar"
                height="350"
                :options="topProfilesChartOptions"
                :series="topProfilesChartSeries"
              />
              <div v-else class="no-data">
                <p>Aucune donnée disponible</p>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h2>Répartition des Types de Quotas</h2>
              <p class="chart-subtitle">Limités vs Illimités</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="profileStats"
                type="donut"
                height="350"
                :options="quotaTypesPieChartOptions"
                :series="quotaTypesPieChartSeries"
              />
              <div v-else class="no-data">
                <p>Aucune donnée disponible</p>
              </div>
            </div>
          </div>
```

## 7. Styles CSS - Ajouter à la fin de la section `<style scoped>`

```css
/* Nouvelles icônes de stats pour les profils */
.stat-icon.profiles {
  background: #EDE9FE;
  color: #8B5CF6;
}

.stat-icon.quota {
  background: #FBCFE8;
  color: #EC4899;
}

/* Style pour l'état vide */
.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 350px;
  color: #9CA3AF;
  font-size: 1rem;
}
```

## 8. Action rapide pour les profils

### Ajouter ce bouton dans la section `.quick-actions-grid` (après le bouton quotas, line 417) :

```vue
            <button @click="navigateTo('/admin/profiles')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Gérer les profils</h3>
              <p>Créer et configurer des profils</p>
            </button>
```

## Résumé des Modifications

1. ✅ Import `useProfileStore`
2. ✅ Initialisation `profileStore`
3. ✅ Ajout `profileStore.fetchStatistics()` au chargement
4. ✅ 2 nouveaux `computed` pour les stats
5. ✅ 2 nouveaux graphiques (top profils, répartition quotas)
6. ✅ 2 nouvelles cartes de stats
7. ✅ 2 nouveaux graphiques dans le template
8. ✅ 1 nouveau bouton action rapide
9. ✅ Styles CSS pour les nouvelles icônes

## Test

Après intégration, le dashboard devrait afficher :
- **Statistiques** : Total profils, profils actifs, quotas limités/illimités
- **Graphique** : Top 5 profils les plus utilisés (bar chart)
- **Graphique** : Répartition limités vs illimités (donut chart)
- **Action rapide** : Bouton "Gérer les profils"
