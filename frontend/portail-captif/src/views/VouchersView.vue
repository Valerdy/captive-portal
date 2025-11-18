<script setup lang="ts">
import { ref } from 'vue'
import { useVoucherStore } from '@/stores/voucher'
import { useAuthStore } from '@/stores/auth'

const voucherStore = useVoucherStore()
const authStore = useAuthStore()

const voucherCode = ref('')
const validationResult = ref<any>(null)
const successMessage = ref('')

async function handleValidate() {
  validationResult.value = null
  try {
    const result = await voucherStore.validateVoucher(voucherCode.value)
    validationResult.value = result
  } catch (error) {
    // L'erreur est déjà dans le store
  }
}

async function handleRedeem() {
  if (!authStore.isAuthenticated) {
    alert('Vous devez être connecté pour utiliser un voucher')
    return
  }

  successMessage.value = ''
  try {
    const result = await voucherStore.redeemVoucher(voucherCode.value)
    successMessage.value = `Voucher utilisé avec succès! Durée: ${result.duration} secondes`
    voucherCode.value = ''
    validationResult.value = null
  } catch (error) {
    // L'erreur est déjà dans le store
  }
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}h ${minutes}min`
  return `${minutes} minutes`
}
</script>

<template>
  <div class="voucher-container">
    <div class="voucher-card">
      <h1>🎟️ Codes Voucher</h1>
      <p class="subtitle">Entrez votre code d'accès invité</p>

      <div class="form-group">
        <label for="code">Code Voucher</label>
        <input
          id="code"
          v-model="voucherCode"
          type="text"
          placeholder="Ex: WELCOME2024"
          @keyup.enter="handleValidate"
        />
      </div>

      <div class="button-group">
        <button @click="handleValidate" :disabled="!voucherCode || voucherStore.isLoading" class="btn-secondary">
          Valider
        </button>
        <button
          @click="handleRedeem"
          :disabled="!validationResult?.valid || voucherStore.isLoading"
          class="btn-primary"
        >
          Utiliser
        </button>
      </div>

      <div v-if="voucherStore.error" class="error-message">
        {{ voucherStore.error }}
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <div v-if="validationResult" class="validation-result">
        <div v-if="validationResult.valid" class="valid">
          <h3>✅ Voucher Valide</h3>
          <div class="voucher-details">
            <p><strong>Code:</strong> {{ validationResult.voucher.code }}</p>
            <p><strong>Durée:</strong> {{ formatDuration(validationResult.voucher.duration) }}</p>
            <p>
              <strong>Appareils max:</strong> {{ validationResult.voucher.max_devices }}
            </p>
            <p>
              <strong>Utilisations:</strong> {{ validationResult.voucher.used_count }} /
              {{ validationResult.voucher.max_devices }}
            </p>
            <p>
              <strong>Valide jusqu'au:</strong>
              {{ new Date(validationResult.voucher.valid_until).toLocaleDateString() }}
            </p>
          </div>
        </div>
        <div v-else class="invalid">
          <h3>❌ Voucher Invalide</h3>
          <p>Ce code n'est pas valide ou a expiré</p>
        </div>
      </div>

      <div class="footer">
        <router-link to="/login">Se connecter avec un compte</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voucher-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.voucher-card {
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

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
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
  text-transform: uppercase;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.875rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-primary:hover:not(:disabled),
.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.success-message {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.validation-result {
  margin: 1.5rem 0;
  padding: 1.5rem;
  border-radius: 8px;
}

.valid {
  background: #e8f5e9;
}

.invalid {
  background: #ffebee;
}

.valid h3 {
  color: #2e7d32;
  margin-bottom: 1rem;
}

.invalid h3 {
  color: #c62828;
  margin-bottom: 0.5rem;
}

.voucher-details p {
  margin: 0.5rem 0;
  color: #333;
}

.footer {
  margin-top: 2rem;
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
