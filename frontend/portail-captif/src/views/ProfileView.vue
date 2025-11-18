<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const formData = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: ''
})

const successMessage = ref('')
const errorMessage = ref('')

async function handleUpdate() {
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await authStore.updateProfile(formData.value)
    successMessage.value = 'Profil mis à jour avec succès !'
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur lors de la mise à jour'
  }
}

onMounted(() => {
  if (authStore.user) {
    formData.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      email: authStore.user.email || '',
      phone_number: authStore.user.phone_number || ''
    }
  }
})
</script>

<template>
  <div class="page">
    <div class="profile-container">
      <h2>Mon Profil</h2>

      <div class="profile-header">
        <div class="avatar">{{ authStore.user?.username.charAt(0).toUpperCase() }}</div>
        <div class="user-info">
          <h3>{{ authStore.user?.username }}</h3>
          <p>Membre depuis {{ new Date(authStore.user?.date_joined || '').toLocaleDateString() }}</p>
        </div>
      </div>

      <form @submit.prevent="handleUpdate" class="profile-form">
        <div class="form-row">
          <div class="form-group">
            <label for="first_name">Prénom</label>
            <input id="first_name" v-model="formData.first_name" type="text" />
          </div>
          <div class="form-group">
            <label for="last_name">Nom</label>
            <input id="last_name" v-model="formData.last_name" type="text" />
          </div>
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="formData.email" type="email" />
        </div>

        <div class="form-group">
          <label for="phone_number">Téléphone</label>
          <input id="phone_number" v-model="formData.phone_number" type="tel" />
        </div>

        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
          {{ authStore.isLoading ? 'Enregistrement...' : 'Enregistrer' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.profile-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

h2 {
  margin-bottom: 2rem;
  color: #333;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #f8f8f8;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
}

.user-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.user-info p {
  margin: 0;
  color: #666;
}

.profile-form {
  margin-top: 2rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.success-message {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.btn-primary {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
