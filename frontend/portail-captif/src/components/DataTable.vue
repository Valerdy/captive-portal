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
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
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
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Précédent
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
        Suivant
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

.data-table {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 10px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
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
  background: rgba(255, 255, 255, 0.05);
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex: 1;
  min-width: 250px;
  max-width: 400px;
  transition: all 0.3s ease;
}

.search-box:focus-within {
  border-color: #F29400;
  background: rgba(242, 148, 0, 0.05);
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.15);
}

.search-box svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.search-box input {
  border: none;
  background: none;
  outline: none;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  width: 100%;
  color: rgba(255, 255, 255, 0.9);
}

.search-box input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.btn-export {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(242, 148, 0, 0.3);
}

.btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(242, 148, 0, 0.4);
}

.btn-export svg {
  width: 18px;
  height: 18px;
}

.table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: rgba(255, 255, 255, 0.03);
}

th {
  text-align: left;
  padding: 1rem;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

th.sortable {
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

th.sortable:hover {
  background: rgba(242, 148, 0, 0.08);
  color: #F29400;
}

th span {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-icon {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.sort-icon.active {
  color: #F29400;
}

.sort-icon.desc {
  transform: rotate(180deg);
}

tbody tr {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

tbody tr:hover {
  background: rgba(242, 148, 0, 0.08);
  cursor: pointer;
}

td {
  padding: 1rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.85);
}

.empty-state {
  text-align: center;
  padding: 4rem 1rem;
}

.empty-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 28px;
  height: 28px;
  color: rgba(255, 255, 255, 0.3);
}

.empty-state p {
  color: rgba(255, 255, 255, 0.4);
  font-family: 'Inter', sans-serif;
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
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pagination-btn svg {
  width: 16px;
  height: 16px;
}

.pagination-btn:hover:not(:disabled),
.page-btn:hover {
  background: rgba(242, 148, 0, 0.15);
  border-color: #F29400;
  color: #F29400;
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-btn.active {
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(242, 148, 0, 0.3);
}

.page-numbers {
  display: flex;
  gap: 0.25rem;
}

.table-info {
  text-align: center;
  margin-top: 1rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Scrollbar */
.table-container::-webkit-scrollbar {
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb {
  background: rgba(242, 148, 0, 0.3);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(242, 148, 0, 0.5);
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

  .pagination-btn span {
    display: none;
  }
}
</style>
