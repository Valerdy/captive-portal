<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentPage: number
  totalItems: number
  itemsPerPage?: number
  maxVisiblePages?: number
}

const props = withDefaults(defineProps<Props>(), {
  itemsPerPage: 10,
  maxVisiblePages: 5
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
}>()

const totalPages = computed(() => Math.ceil(props.totalItems / props.itemsPerPage))

const startItem = computed(() =>
  props.totalItems === 0 ? 0 : (props.currentPage - 1) * props.itemsPerPage + 1
)

const endItem = computed(() =>
  Math.min(props.currentPage * props.itemsPerPage, props.totalItems)
)

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = props.currentPage
  const maxVisible = props.maxVisiblePages

  if (total <= maxVisible + 2) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)

    if (current > 3) {
      pages.push('...')
    }

    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) {
      if (i !== 1 && i !== total) {
        pages.push(i)
      }
    }

    if (current < total - 2) {
      pages.push('...')
    }

    pages.push(total)
  }

  return pages
})

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    emit('update:currentPage', page)
  }
}

function prevPage() {
  if (props.currentPage > 1) {
    emit('update:currentPage', props.currentPage - 1)
  }
}

function nextPage() {
  if (props.currentPage < totalPages.value) {
    emit('update:currentPage', props.currentPage + 1)
  }
}
</script>

<template>
  <div v-if="totalPages > 0" class="pagination-wrapper">
    <div class="pagination-info">
      <span>Affichage de <strong>{{ startItem }}</strong> à <strong>{{ endItem }}</strong> sur <strong>{{ totalItems }}</strong> résultats</span>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="prevPage"
        :disabled="currentPage === 1"
        class="pagination-btn nav-btn"
        title="Page précédente"
      >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="btn-text">Précédent</span>
      </button>

      <div class="page-numbers">
        <template v-for="(page, index) in visiblePages" :key="index">
          <span v-if="page === '...'" class="ellipsis">...</span>
          <button
            v-else
            @click="goToPage(page as number)"
            :class="['page-btn', { active: currentPage === page }]"
          >
            {{ page }}
          </button>
        </template>
      </div>

      <button
        @click="nextPage"
        :disabled="currentPage === totalPages"
        class="pagination-btn nav-btn"
        title="Page suivante"
      >
        <span class="btn-text">Suivant</span>
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.pagination-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.pagination-info {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.pagination-info strong {
  color: #F29400;
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  background: rgba(15, 15, 25, 0.9);
  border: 2px solid rgba(0, 142, 207, 0.4);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 142, 207, 0.1);
}

.pagination-btn,
.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  color: rgba(0, 142, 207, 0.8);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.pagination-btn svg {
  width: 18px;
  height: 18px;
}

.page-btn {
  min-width: 40px;
  padding: 0.5rem;
  border-radius: 6px;
}

.pagination-btn:hover:not(:disabled),
.page-btn:hover:not(.active) {
  color: #F29400;
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-btn.active {
  background: linear-gradient(135deg, #008ecf 0%, #00b4d8 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 142, 207, 0.4);
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.ellipsis {
  padding: 0.5rem;
  color: rgba(0, 142, 207, 0.5);
  font-family: 'Inter', sans-serif;
}

@media (max-width: 640px) {
  .pagination-wrapper {
    gap: 0.75rem;
  }

  .pagination {
    gap: 0.5rem;
    padding: 0.5rem 1rem;
  }

  .pagination-btn {
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
  }

  .btn-text {
    display: none;
  }

  .page-btn {
    min-width: 34px;
    padding: 0.4rem;
    font-size: 0.85rem;
  }

  .pagination-info {
    font-size: 0.8rem;
    text-align: center;
  }
}
</style>
