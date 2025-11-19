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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.voucher-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #c31432 0%, #e85d04 50%, #ff6b35 100%);
  padding: 1rem;
}

.voucher-card {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 540px;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h1 {
  color: #c31432;
  font-size: 2rem;
  margin-bottom: 0.5rem;
  text-align: center;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 600;
  font-size: 0.95rem;
}

label svg {
  width: 18px;
  height: 18px;
  color: #e85d04;
}

input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
  transition: all 0.3s ease;
  background: #f8f8f8;
  text-align: center;
}

input:focus {
  outline: none;
  border-color: #e85d04;
  background: white;
  box-shadow: 0 0 0 3px rgba(232, 93, 4, 0.1);
}

input::placeholder {
  text-transform: none;
  letter-spacing: normal;
  font-weight: normal;
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.btn-primary,
.btn-secondary {
  padding: 1rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(195, 20, 50, 0.3);
}

.btn-secondary {
  background: white;
  color: #e85d04;
  border: 2px solid #e85d04;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(195, 20, 50, 0.4);
}

.btn-secondary:hover:not(:disabled) {
  background: #e85d04;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(232, 93, 4, 0.3);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  background: #fff5f5;
  border: 1px solid #feb2b2;
  color: #c53030;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.success-message {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  color: #2e7d32;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  font-weight: 600;
  text-align: center;
  border: 1px solid #81c784;
}

.validation-result {
  margin: 1.5rem 0;
  padding: 1.75rem;
  border-radius: 16px;
  border: 2px solid;
}

.valid {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-color: #4caf50;
}

.invalid {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border-color: #ef5350;
}

.valid h3 {
  color: #2e7d32;
  margin-bottom: 1.25rem;
  font-size: 1.25rem;
  font-weight: 700;
}

.invalid h3 {
  color: #c62828;
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
}

.voucher-details p {
  margin: 0.75rem 0;
  color: #333;
  font-size: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.voucher-details p:last-child {
  border-bottom: none;
}

.voucher-details strong {
  color: #2e7d32;
  font-weight: 700;
  min-width: 150px;
  display: inline-block;
}

.footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
  text-align: center;
}

.footer a {
  color: #e85d04;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.footer a:hover {
  color: #c31432;
  transform: translateX(-4px);
}

/* Responsive */
@media (max-width: 640px) {
  .voucher-container {
    padding: 0.5rem;
  }

  .voucher-card {
    padding: 2rem 1.5rem;
  }

  .button-group {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 1.75rem;
  }
}

@media (max-width: 380px) {
  .voucher-card {
    padding: 1.5rem 1rem;
  }

  input {
    padding: 0.875rem;
    font-size: 1rem;
  }

  .btn-primary,
  .btn-secondary {
    padding: 0.875rem;
  }
}
</style>
