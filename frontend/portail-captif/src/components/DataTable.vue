<script setup lang="ts" generic="T extends Record<string, any>">
import { ref, computed } from 'vue'
import LoadingSpinner from './LoadingSpinner.vue'

interface Column {
  key: string
  label: string
  sortable?: boolean
  formatter?: (value: any, row: T) => string
}

interface Props {
  columns: Column[]
  data: T[]
  loading?: boolean
  searchable?: boolean
  exportable?: boolean
  exportFilename?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchable: true,
  exportable: true,
  exportFilename: 'export'
})

const emit = defineEmits<{
  rowClick: [row: T]
}>()

const searchQuery = ref('')
const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const itemsPerPage = ref(10)

// Filtered data
const filteredData = computed(() => {
  if (!searchQuery.value) return props.data

  const query = searchQuery.value.toLowerCase()
  return props.data.filter((row) => {
    return Object.values(row).some((value) =>
      String(value).toLowerCase().includes(query)
    )
  })
})

// Sorted data
const sortedData = computed(() => {
  if (!sortKey.value) return filteredData.value

  return [...filteredData.value].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]

    let comparison = 0
    if (aVal > bVal) comparison = 1
    if (aVal < bVal) comparison = -1

    return sortOrder.value === 'asc' ? comparison : -comparison
  })
})

// Paginated data
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return sortedData.value.slice(start, end)
})

const totalPages = computed(() =>
  Math.ceil(sortedData.value.length / itemsPerPage.value)
)

function sort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

function exportToCSV() {
  const headers = props.columns.map((col) => col.label).join(',')
  const rows = sortedData.value.map((row) => {
    return props.columns
      .map((col) => {
        const value = col.formatter ? col.formatter(row[col.key], row) : row[col.key]
        return `"${String(value).replace(/"/g, '""')}"`
      })
      .join(',')
  })

  const csv = [headers, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${props.exportFilename}.csv`
  link.click()
}

function getCellValue(row: T, column: Column) {
  const value = row[column.key]
  return column.formatter ? column.formatter(value, row) : value
}
</script>

<template>
  <div class="data-table">
    <!-- Toolbar -->
    <div class="table-toolbar">
      <div class="search-box" v-if="searchable">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" />
          <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher..."
          @input="currentPage = 1"
        />
      </div>

      <button v-if="exportable" @click="exportToCSV" class="btn-export">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        Exporter CSV
      </button>
    </div>

    <!-- Table -->
    <div class="table-container">
      <LoadingSpinner v-if="loading" size="large" />

      <table v-else>
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="{ sortable: column.sortable }"
              @click="column.sortable && sort(column.key)"
            >
              <span>{{ column.label }}</span>
              <svg
                v-if="column.sortable"
                class="sort-icon"
                :class="{
                  active: sortKey === column.key,
                  desc: sortKey === column.key && sortOrder === 'desc'
                }"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 5v14M5 12l7 7 7-7"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in paginatedData"
            :key="index"
            @click="emit('rowClick', row)"
          >
            <td v-for="column in columns" :key="column.key">
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                {{ getCellValue(row, column) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && paginatedData.length === 0" class="empty-state">
        <p>Aucune donnée trouvée</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="currentPage--"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        ← Précédent
      </button>

      <div class="page-numbers">
        <button
          v-for="page in totalPages"
          :key="page"
          @click="currentPage = page"
          :class="['page-btn', { active: currentPage === page }]"
        >
          {{ page }}
        </button>
      </div>

      <button
        @click="currentPage++"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Suivant →
      </button>
    </div>

    <!-- Info -->
    <div class="table-info">
      Affichage de {{ (currentPage - 1) * itemsPerPage + 1 }} à
      {{ Math.min(currentPage * itemsPerPage, sortedData.length) }} sur
      {{ sortedData.length }} résultats
    </div>
  </div>
</template>

<style scoped>
.data-table {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f9fafb;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  flex: 1;
  min-width: 250px;
  max-width: 400px;
  transition: all 0.3s ease;
}

.search-box:focus-within {
  border-color: #f97316;
  background: white;
}

.search-box svg {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  flex-shrink: 0;
}

.search-box input {
  border: none;
  background: none;
  outline: none;
  font-size: 0.95rem;
  width: 100%;
  color: #111827;
}

.btn-export {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(249, 115, 22, 0.4);
}

.btn-export svg {
  width: 18px;
  height: 18px;
}

.table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f9fafb;
}

th {
  text-align: left;
  padding: 1rem;
  font-weight: 700;
  font-size: 0.875rem;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

th.sortable:hover {
  background: #f3f4f6;
}

th span {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-icon {
  width: 16px;
  height: 16px;
  color: #d1d5db;
  transition: all 0.3s ease;
}

.sort-icon.active {
  color: #f97316;
}

.sort-icon.desc {
  transform: rotate(180deg);
}

tbody tr {
  border-top: 1px solid #e5e7eb;
  transition: background 0.2s ease;
}

tbody tr:hover {
  background: #f9fafb;
  cursor: pointer;
}

td {
  padding: 1rem;
  font-size: 0.95rem;
  color: #111827;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #9ca3af;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.pagination-btn,
.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled),
.page-btn:hover {
  background: #f9fafb;
  border-color: #f97316;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn.active {
  background: #f97316;
  color: white;
  border-color: #f97316;
}

.page-numbers {
  display: flex;
  gap: 0.25rem;
}

.table-info {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: none;
  }

  .table-container {
    overflow-x: scroll;
  }

  th,
  td {
    padding: 0.75rem 0.5rem;
    font-size: 0.875rem;
  }
}
</style>
