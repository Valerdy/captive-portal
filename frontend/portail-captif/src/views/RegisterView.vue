<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  phone_number: ''
})
const errorMessage = ref('')

async function handleRegister() {
  errorMessage.value = ''

  try {
    await authStore.register(formData.value)
    router.push('/')
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur lors de l\'inscription'
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <h1>Portail Captif</h1>
      <h2>Créer un compte</h2>

      <form @submit.prevent="handleRegister">
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
          <label for="username">Nom d'utilisateur *</label>
          <input id="username" v-model="formData.username" type="text" required />
        </div>

        <div class="form-group">
          <label for="email">Email *</label>
          <input id="email" v-model="formData.email" type="email" required />
        </div>

        <div class="form-group">
          <label for="phone_number">Téléphone</label>
          <input id="phone_number" v-model="formData.phone_number" type="tel" />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe *</label>
          <input id="password" v-model="formData.password" type="password" required />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
          {{ authStore.isLoading ? 'Inscription...' : "S'inscrire" }}
        </button>
      </form>

      <div class="footer">
        <router-link to="/login">Déjà un compte ? Se connecter</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.register-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
}

h1 {
  color: #667eea;
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

h2 {
  color: #333;
  font-size: 1.3rem;
  margin-bottom: 2rem;
  text-align: center;
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
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #667eea;
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

.footer {
  margin-top: 1.5rem;
  text-align: center;
}

.footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.footer a:hover {
  text-decoration: underline;
}
</style>
