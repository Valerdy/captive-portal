<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const users = computed(() => userStore.users)
const isLoading = computed(() => userStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const selectedUser = ref<any>(null)
const newUser = ref({
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  is_staff: false
})

const columns = [
  { key: 'id', label: 'ID', sortable: true },
  { key: 'username', label: 'Utilisateur', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'is_staff', label: 'Rôle', sortable: true, formatter: (value: boolean) => value ? 'Admin' : 'Utilisateur' },
  { key: 'is_active', label: 'Statut', sortable: true },
  { key: 'date_joined', label: 'Inscription', sortable: true, formatter: (value: string) => new Date(value).toLocaleDateString('fr-FR') },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await userStore.fetchUsers()
  } catch (error) {
    notificationStore.error('Erreur lors du chargement des utilisateurs')
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

async function handleAddUser() {
  if (!newUser.value.username || !newUser.value.email || !newUser.value.password) {
    notificationStore.warning('Veuillez remplir tous les champs requis')
    return
  }

  try {
    await userStore.createUser({
      username: newUser.value.username,
      email: newUser.value.email,
      password: newUser.value.password,
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
      is_staff: selectedUser.value.is_staff
    })

    notificationStore.success('Utilisateur modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleStatus(userId: number, currentStatus: boolean) {
  const action = currentStatus ? 'désactiver' : 'activer'
  if (confirm(`Voulez-vous vraiment ${action} cet utilisateur ?`)) {
    try {
      await userStore.updateUser(userId, {
        is_active: !currentStatus
      })
      notificationStore.success(`Utilisateur ${currentStatus ? 'désactivé' : 'activé'} avec succès`)
    } catch (error) {
      notificationStore.error(userStore.error || 'Erreur lors de la modification')
    }
  }
}

async function handleDelete(userId: number) {
  if (confirm('Voulez-vous vraiment supprimer cet utilisateur ? Cette action est irréversible.')) {
    try {
      await userStore.deleteUser(userId)
      notificationStore.success('Utilisateur supprimé avec succès')
    } catch (error) {
      notificationStore.error(userStore.error || 'Erreur lors de la suppression')
    }
  }
}

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-users">
    <header class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retour
      </button>

      <div class="header-content">
        <div class="header-info">
          <h1>Gestion des utilisateurs</h1>
          <p>{{ users.length }} utilisateurs au total</p>
        </div>
        <button @click="openAddModal" class="add-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Ajouter un utilisateur
        </button>
      </div>
    </header>

    <main class="page-content">
      <LoadingSpinner v-if="isLoading" />

      <div v-else class="content-card">
        <DataTable
          :columns="columns"
          :data="users"
          :loading="isLoading"
          export-filename="utilisateurs-ucac-icam"
        >
          <template #cell-is_active="{ value }">
            <span :class="['status-badge', value ? 'active' : 'inactive']">
              {{ value ? 'Actif' : 'Inactif' }}
            </span>
          </template>
          <template #cell-actions="{ row }">
            <div class="action-buttons">
              <button @click="handleEdit(row)" class="action-btn edit" title="Modifier">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="handleToggleStatus(row.id, row.is_active)" class="action-btn toggle" :title="row.is_active ? 'Désactiver' : 'Activer'">
                <svg v-if="row.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="handleDelete(row.id)" class="action-btn delete" title="Supprimer">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </template>
        </DataTable>
      </div>
    </main>

    <!-- Modal Ajout -->
    <Teleport to="body">
      <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
        <div class="modal-content" @click.stop>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <h2>Ajouter un utilisateur</h2>

          <form @submit.prevent="handleAddUser" class="form">
            <div class="form-row">
              <div class="form-group">
                <label>Nom d'utilisateur *</label>
                <input v-model="newUser.username" type="text" required />
              </div>
              <div class="form-group">
                <label>Email *</label>
                <input v-model="newUser.email" type="email" required />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Prénom</label>
                <input v-model="newUser.first_name" type="text" />
              </div>
              <div class="form-group">
                <label>Nom</label>
                <input v-model="newUser.last_name" type="text" />
              </div>
            </div>

            <div class="form-group">
              <label>Mot de passe *</label>
              <input v-model="newUser.password" type="password" required />
            </div>

            <div class="form-group checkbox">
              <label>
                <input v-model="newUser.is_staff" type="checkbox" />
                <span>Administrateur</span>
              </label>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeAddModal" class="btn-secondary">Annuler</button>
              <button type="submit" class="btn-primary">Ajouter</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Modal Édition -->
    <Teleport to="body">
      <div v-if="showEditModal && selectedUser" class="modal-overlay" @click="closeEditModal">
        <div class="modal-content" @click.stop>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <h2>Modifier l'utilisateur</h2>

          <form @submit.prevent="handleUpdateUser" class="form">
            <div class="form-row">
              <div class="form-group">
                <label>Nom d'utilisateur</label>
                <input v-model="selectedUser.username" type="text" required />
              </div>
              <div class="form-group">
                <label>Email</label>
                <input v-model="selectedUser.email" type="email" required />
              </div>
            </div>

            <div class="form-group checkbox">
              <label>
                <input v-model="selectedUser.is_staff" type="checkbox" />
                <span>Administrateur</span>
              </label>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="btn-secondary">Annuler</button>
              <button type="submit" class="btn-primary">Enregistrer</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-users {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 2rem;
}

.page-header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(-4px);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.header-info h1 {
  color: white;
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.header-info p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1rem;
}

.add-btn {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border: 2px solid rgba(220, 38, 38, 0.5);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.add-btn svg {
  width: 20px;
  height: 20px;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.page-content {
  max-width: 1400px;
  margin: 0 auto;
}

.content-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
}

.status-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.inactive {
  background: rgba(220, 38, 38, 0.15);
  color: #f87171;
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.edit {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.2);
}

.action-btn.edit:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
}

.action-btn.toggle {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.2);
}

.action-btn.toggle:hover {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.4);
}

.action-btn.delete {
  background: rgba(220, 38, 38, 0.1);
  color: #f87171;
  border-color: rgba(220, 38, 38, 0.2);
}

.action-btn.delete:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(220, 38, 38, 0.4);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2.5rem;
  max-width: 600px;
  width: 100%;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.6);
}

.modal-close:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(220, 38, 38, 0.4);
  color: #f87171;
  transform: rotate(90deg);
}

.modal-content h2 {
  color: white;
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 2rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.95rem;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: 0.875rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: #f97316;
}

.form-group.checkbox {
  flex-direction: row;
  align-items: center;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.form-group.checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.form-actions button {
  flex: 1;
  padding: 1rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border: 2px solid rgba(220, 38, 38, 0.5);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .admin-users {
    padding: 1rem;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .add-btn {
    width: 100%;
    justify-content: center;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
