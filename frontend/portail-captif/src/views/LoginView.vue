<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''

  try {
    await authStore.login({
      username: username.value,
      password: password.value
    })

    // Redirection vers le dashboard ou l'URL d'origine
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur de connexion'
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Portail Captif</h1>
      <h2>Connexion</h2>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Nom d'utilisateur</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
          {{ authStore.isLoading ? 'Connexion...' : 'Se connecter' }}
        </button>
      </form>

      <div class="footer">
        <router-link to="/register">Créer un compte</router-link>
        <span>|</span>
        <router-link to="/vouchers">Utiliser un voucher</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
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
  color: #666;
  display: flex;
  gap: 1rem;
  justify-content: center;
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
