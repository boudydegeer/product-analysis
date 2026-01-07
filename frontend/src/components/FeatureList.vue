<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-semibold text-gray-900">Features</h2>
      <button
        @click="showCreateForm = true"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        New Feature
      </button>
    </div>

    <!-- Create Form Modal -->
    <div v-if="showCreateForm" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-semibold mb-4">Create New Feature</h3>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Feature ID</label>
            <input
              v-model="newFeature.id"
              type="text"
              placeholder="FEAT-001"
              class="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 focus:outline-none px-3 py-2 text-gray-900 bg-white placeholder-gray-400"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Name</label>
            <input
              v-model="newFeature.name"
              type="text"
              placeholder="Feature name"
              class="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 focus:outline-none px-3 py-2 text-gray-900 bg-white placeholder-gray-400"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              v-model="newFeature.description"
              rows="4"
              placeholder="Detailed feature description"
              class="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 focus:outline-none px-3 py-2 text-gray-900 bg-white placeholder-gray-400"
              required
            ></textarea>
          </div>
          <div class="flex justify-end space-x-2">
            <button
              type="button"
              @click="showCreateForm = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.loading" class="text-center py-8">
      <p class="text-gray-500">Loading features...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-800">{{ store.error }}</p>
    </div>

    <!-- Feature List -->
    <div v-else-if="store.features.length > 0" class="bg-white shadow overflow-hidden rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="feature in store.features" :key="feature.id" class="p-4 hover:bg-gray-50">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-2">
                <h3 class="text-lg font-medium text-gray-900">{{ feature.name }}</h3>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="getStatusClass(feature.status)"
                >
                  {{ feature.status }}
                </span>
              </div>
              <p class="text-sm text-gray-500 mt-1">{{ feature.id }}</p>
              <p class="text-sm text-gray-700 mt-2">{{ feature.description }}</p>
            </div>
            <div class="flex space-x-2 ml-4">
              <button
                @click="handleAnalyze(feature.id)"
                :disabled="feature.status === 'analyzing'"
                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {{ feature.status === 'analyzing' ? 'Analyzing...' : 'Analyze' }}
              </button>
              <button
                @click="handleDelete(feature.id)"
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12 bg-white rounded-lg shadow">
      <p class="text-gray-500">No features yet. Create your first feature to get started!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFeaturesStore } from '@/stores/features'
import type { FeatureStatus } from '@/types/feature'

const store = useFeaturesStore()
const showCreateForm = ref(false)
const newFeature = ref({
  id: '',
  name: '',
  description: '',
})

onMounted(() => {
  store.fetchFeatures()
})

async function handleCreate() {
  try {
    await store.createFeature(newFeature.value)
    showCreateForm.value = false
    newFeature.value = { id: '', name: '', description: '' }
  } catch (e) {
    console.error('Failed to create feature:', e)
  }
}

async function handleAnalyze(id: string) {
  try {
    await store.triggerAnalysis(id)
  } catch (e) {
    console.error('Failed to trigger analysis:', e)
  }
}

async function handleDelete(id: string) {
  try {
    await store.deleteFeature(id)
  } catch (e) {
    console.error('Failed to delete feature:', e)
  }
}

function getStatusClass(status: FeatureStatus): string {
  const classes: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    analyzing: 'bg-yellow-100 text-yellow-800',
    analyzed: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    in_progress: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}
</script>
