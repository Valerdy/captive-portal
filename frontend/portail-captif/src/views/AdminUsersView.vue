<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const users = computed(() => userStore.users)
const isLoading = computed(() => userStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const selectedUser = ref<any>(null)
const searchQuery = ref('')
const filterRole = ref('all')
const filterStatus = ref('all')
const isDeleting = ref(false)

const newUser = ref({
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  is_staff: false
})

// Filtrage des utilisateurs
const filteredUsers = computed(() => {
  let filtered = users.value

  // Filtre par recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(u =>
      u.username?.toLowerCase().includes(query) ||
      u.email?.toLowerCase().includes(query) ||
      u.first_name?.toLowerCase().includes(query) ||
      u.last_name?.toLowerCase().includes(query)
    )
  }

  // Filtre par rôle
  if (filterRole.value !== 'all') {
    if (filterRole.value === 'admin') {
      filtered = filtered.filter(u => u.is_staff || u.is_superuser)
    } else {
      filtered = filtered.filter(u => !u.is_staff && !u.is_superuser)
    }
  }

  // Filtre par statut
  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'active') {
      filtered = filtered.filter(u => u.is_active)
    } else {
      filtered = filtered.filter(u => !u.is_active)
    }
  }

  return filtered
})

// Statistiques
const stats = computed(() => ({
  total: users.value.length,
  active: users.value.filter(u => u.is_active).length,
  admins: users.value.filter(u => u.is_staff || u.is_superuser).length,
  regular: users.value.filter(u => !u.is_staff && !u.is_superuser).length
}))

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await userStore.fetchUsers()
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des utilisateurs: ${message}`)
    console.error('Erreur chargement utilisateurs:', error)
  }
})

function openAddModal() {
  newUser.value = {
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    is_staff: false
  }
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

// Fonction de validation d'email
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Fonction de validation de mot de passe
function isValidPassword(password: string): boolean {
  return password.length >= 8
}

async function handleAddUser() {
  // Validation des champs obligatoires
  if (!newUser.value.username || !newUser.value.email || !newUser.value.password) {
    notificationStore.warning('Veuillez remplir tous les champs requis')
    return
  }

  // Validation du format email
  if (!isValidEmail(newUser.value.email)) {
    notificationStore.warning('Format d\'email invalide')
    return
  }

  // Validation de la force du mot de passe
  if (!isValidPassword(newUser.value.password)) {
    notificationStore.warning('Le mot de passe doit contenir au moins 8 caractères')
    return
  }

  try {
    await userStore.createUser({
      username: newUser.value.username,
      email: newUser.value.email,
      password: newUser.value.password,
      password2: newUser.value.password,
      first_name: newUser.value.first_name,
      last_name: newUser.value.last_name,
      is_staff: newUser.value.is_staff
    })

    notificationStore.success('Utilisateur ajouté avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de l\'ajout')
  }
}

function handleEdit(user: any) {
  selectedUser.value = { ...user }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedUser.value = null
}

async function handleUpdateUser() {
  if (!selectedUser.value) return

  try {
    await userStore.updateUser(selectedUser.value.id, {
      username: selectedUser.value.username,
      email: selectedUser.value.email,
      first_name: selectedUser.value.first_name,
      last_name: selectedUser.value.last_name,
      is_staff: selectedUser.value.is_staff,
      is_active: selectedUser.value.is_active
    })

    notificationStore.success('Utilisateur modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleActive(user: any) {
  try {
    await userStore.updateUser(user.id, {
      is_active: !user.is_active
    })
    notificationStore.success(`Utilisateur ${user.is_active ? 'désactivé' : 'activé'}`)
  } catch (error) {
    notificationStore.error('Erreur lors de la modification')
  }
}

async function handleDelete(user: any) {
  // Protection contre les double-clics
  if (isDeleting.value) {
    return
  }

  if (!confirm(`Voulez-vous vraiment supprimer l'utilisateur ${user.username} ?`)) {
    return
  }

  isDeleting.value = true
  try {
    await userStore.deleteUser(user.id)
    notificationStore.success('Utilisateur supprimé avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <AdminLayout activePage="users">
    <div class="content-header">
        <div>
          <h2 class="page-title">Gestion des utilisateurs</h2>
          <p class="page-subtitle">Créer, modifier et gérer les comptes utilisateurs</p>
        </div>
        <button @click="openAddModal" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Nouvel utilisateur
        </button>
      </div>

      <!-- Statistiques -->
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">Total utilisateurs</div>
        </div>
        <div class="stat-box success">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">Actifs</div>
        </div>
        <div class="stat-box danger">
          <div class="stat-value">{{ stats.admins }}</div>
          <div class="stat-label">Administrateurs</div>
        </div>
        <div class="stat-box info">
          <div class="stat-value">{{ stats.regular }}</div>
          <div class="stat-label">Utilisateurs</div>
        </div>
      </div>

      <!-- Filtres et recherche -->
      <div class="filters-section">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher un utilisateur..."
            class="search-input"
          />
        </div>

        <div class="filter-group">
          <select v-model="filterRole" class="filter-select">
            <option value="all">Tous les rôles</option>
            <option value="admin">Administrateurs</option>
            <option value="user">Utilisateurs</option>
          </select>

          <select v-model="filterStatus" class="filter-select">
            <option value="all">Tous les statuts</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>
        </div>
      </div>

      <!-- Table -->
      <div v-if="isLoading" class="loading-container">
        <LoadingSpinner />
      </div>

      <div v-else class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Utilisateur</th>
              <th>Email</th>
              <th>Rôle</th>
              <th>Statut</th>
              <th>Date d'inscription</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td><span class="id-badge">{{ user.id }}</span></td>
              <td>
                <div class="user-cell">
                  <div class="user-avatar-sm">{{ user.username.charAt(0).toUpperCase() }}</div>
                  <div>
                    <div class="user-name-text">{{ user.username }}</div>
                    <div v-if="user.first_name || user.last_name" class="user-full-name">
                      {{ user.first_name }} {{ user.last_name }}
                    </div>
                  </div>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <span v-if="user.is_staff || user.is_superuser" class="badge badge-danger">Admin</span>
                <span v-else class="badge badge-info">Utilisateur</span>
              </td>
              <td>
                <span v-if="user.is_active" class="badge badge-success">Actif</span>
                <span v-else class="badge badge-gray">Inactif</span>
              </td>
              <td>{{ new Date(user.date_joined).toLocaleDateString('fr-FR') }}</td>
              <td>
                <div class="action-buttons">
                  <button @click="handleEdit(user)" class="action-btn edit" title="Modifier">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleToggleActive(user)" :class="['action-btn', user.is_active ? 'danger' : 'success']" :title="user.is_active ? 'Désactiver' : 'Activer'">
                    <svg v-if="user.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleDelete(user)" class="action-btn delete" title="Supprimer">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="filteredUsers.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
          </svg>
          <h3>Aucun utilisateur trouvé</h3>
          <p>Aucun utilisateur ne correspond à vos critères de recherche</p>
        </div>
      </div>
    </main>

    <!-- Modal Ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Ajouter un utilisateur</h3>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Nom d'utilisateur *</label>
              <input v-model="newUser.username" type="text" placeholder="johndoe" />
            </div>
            <div class="form-group">
              <label>Email *</label>
              <input v-model="newUser.email" type="email" placeholder="john@example.com" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Prénom</label>
              <input v-model="newUser.first_name" type="text" placeholder="John" />
            </div>
            <div class="form-group">
              <label>Nom</label>
              <input v-model="newUser.last_name" type="text" placeholder="Doe" />
            </div>
          </div>

          <div class="form-group">
            <label>Mot de passe *</label>
            <input v-model="newUser.password" type="password" placeholder="••••••••" />
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="newUser.is_staff" type="checkbox" />
              <span class="checkbox-text">
                <strong>Administrateur</strong>
                <small>L'utilisateur aura accès à l'administration</small>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn-secondary">Annuler</button>
          <button @click="handleAddUser" class="btn-primary">Créer l'utilisateur</button>
        </div>
      </div>
    </div>

    <!-- Modal Édition -->
    <div v-if="showEditModal && selectedUser" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Modifier l'utilisateur</h3>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Nom d'utilisateur</label>
              <input v-model="selectedUser.username" type="text" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="selectedUser.email" type="email" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Prénom</label>
              <input v-model="selectedUser.first_name" type="text" />
            </div>
            <div class="form-group">
              <label>Nom</label>
              <input v-model="selectedUser.last_name" type="text" />
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedUser.is_staff" type="checkbox" />
              <span class="checkbox-text">
                <strong>Administrateur</strong>
              </span>
            </label>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedUser.is_active" type="checkbox" />
              <span class="checkbox-text">
                <strong>Compte actif</strong>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Annuler</button>
          <button @click="handleUpdateUser" class="btn-primary">Enregistrer</button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Contenu spécifique à la page utilisateurs */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1rem;
  color: #6B7280;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #6B7280;
}

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.danger {
  border-left-color: #DC2626;
}

.stat-box.info {
  border-left-color: #3B82F6;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6B7280;
  font-weight: 500;
}

/* Filtres */
.filters-section {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-box svg {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: #9CA3AF;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1F2937;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

/* Table */
.table-container {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.data-table th {
  padding: 1rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: #1F2937;
  border-bottom: 1px solid #F3F4F6;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #F9FAFB;
}

.id-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #F3F4F6;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6B7280;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-sm {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-name-text {
  font-weight: 600;
  color: #1F2937;
}

.user-full-name {
  font-size: 0.75rem;
  color: #9CA3AF;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: #D1FAE5;
  color: #10B981;
}

.badge-danger {
  background: #FEE2E2;
  color: #DC2626;
}

.badge-info {
  background: #DBEAFE;
  color: #3B82F6;
}

.badge-gray {
  background: #F3F4F6;
  color: #6B7280;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: #6B7280;
}

.action-btn.edit:hover {
  background: #EFF6FF;
  border-color: #3B82F6;
}

.action-btn.edit:hover svg {
  color: #3B82F6;
}

.action-btn.success:hover {
  background: #D1FAE5;
  border-color: #10B981;
}

.action-btn.success:hover svg {
  color: #10B981;
}

.action-btn.danger:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.danger:hover svg {
  color: #DC2626;
}

.action-btn.delete:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.delete:hover svg {
  color: #DC2626;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #D1D5DB;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: #6B7280;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1F2937;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: #F3F4F6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: #6B7280;
}

.modal-close:hover {
  background: #FEE2E2;
}

.modal-close:hover svg {
  color: #DC2626;
}

.modal-body {
  padding: 2rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.checkbox-group {
  margin-top: 1.5rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: #DC2626;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1F2937;
}

.checkbox-text small {
  font-size: 0.75rem;
  color: #6B7280;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #F3F4F6;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #E5E7EB;
}

.loading-container {
  padding: 4rem 0;
  display: flex;
  justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    gap: 1rem;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }

  .filters-section {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .table-container {
    overflow-x: auto;
  }

  .data-table {
    min-width: 800px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
