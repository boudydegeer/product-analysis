<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-semibold">Features</h2>
      <Button @click="showCreateForm = true">
        <Plus class="mr-2 h-4 w-4" />
        New Feature
      </Button>
    </div>

    <!-- Create Form Dialog -->
    <DialogRoot v-model:open="showCreateForm">
      <DialogContent class="sm:max-w-[425px]">
        <DialogTitle class="text-lg font-semibold text-foreground">Create New Feature</DialogTitle>
        <DialogDescription class="text-sm text-muted-foreground">
          Add a new feature to your product analysis
        </DialogDescription>
        <div class="space-y-4">
          <form @submit.prevent="handleCreate" class="space-y-4">
            <div class="space-y-2">
              <Label for="feature-id">Feature ID</Label>
              <Input
                id="feature-id"
                v-model="newFeature.id"
                placeholder="FEAT-001"
                required
              />
            </div>
            <div class="space-y-2">
              <Label for="feature-name">Name</Label>
              <Input
                id="feature-name"
                v-model="newFeature.name"
                placeholder="Feature name"
                required
              />
            </div>
            <div class="space-y-2">
              <Label for="feature-description">Description</Label>
              <Textarea
                id="feature-description"
                v-model="newFeature.description"
                placeholder="Detailed feature description"
                :rows="4"
                required
              />
            </div>
            <div class="flex justify-end space-x-2">
              <Button type="button" variant="outline" @click="showCreateForm = false">
                Cancel
              </Button>
              <Button type="submit">
                Create
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </DialogRoot>

    <!-- Loading State -->
    <Card v-if="store.loading" class="p-8">
      <p class="text-center text-muted-foreground">Loading features...</p>
    </Card>

    <!-- Error State -->
    <Card v-else-if="store.error" class="p-4 border-destructive bg-destructive/10">
      <p class="text-destructive">{{ store.error }}</p>
    </Card>

    <!-- Feature List -->
    <div v-else-if="store.features.length > 0" class="space-y-4">
      <Card
        v-for="feature in store.features"
        :key="feature.id"
        class="p-6 hover:shadow-md transition-shadow cursor-pointer"
        @click="handleViewFeature(feature.id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 space-y-2">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-semibold">{{ feature.name }}</h3>
              <Badge :class="getStatusClass(feature.status)">
                {{ feature.status }}
              </Badge>
            </div>
            <p class="text-sm text-muted-foreground">{{ feature.id }}</p>
            <p class="text-sm">{{ feature.description }}</p>
          </div>
          <div class="flex gap-2 ml-4">
            <Button
              @click.stop="handleAnalyze(feature.id)"
              :disabled="feature.status === 'analyzing'"
              variant="secondary"
              size="sm"
            >
              {{ feature.status === 'analyzing' ? 'Analyzing...' : 'Analyze' }}
            </Button>
            <Button
              @click.stop="handleDelete(feature.id)"
              variant="destructive"
              size="sm"
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Empty State -->
    <Card v-else class="p-12">
      <div class="text-center space-y-2">
        <p class="text-muted-foreground">No features yet. Create your first feature to get started!</p>
        <Button @click="showCreateForm = true" class="mt-4">
          <Plus class="mr-2 h-4 w-4" />
          Create Feature
        </Button>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFeaturesStore } from '@/stores/features'
import type { FeatureStatus } from '@/types/feature'
import { Plus, Trash2 } from 'lucide-vue-next'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import Card from '@/components/ui/card.vue'
import { DialogRoot, DialogTitle, DialogDescription } from 'radix-vue'
import DialogContent from '@/components/ui/dialog-content.vue'
import Input from '@/components/ui/input.vue'
import Textarea from '@/components/ui/textarea.vue'
import Label from '@/components/ui/label.vue'

const store = useFeaturesStore()
const router = useRouter()
const showCreateForm = ref(false)
const newFeature = ref({
  id: '',
  name: '',
  description: '',
})

onMounted(() => {
  store.fetchFeatures()
})

function handleViewFeature(id: string) {
  router.push({ name: 'analysis', params: { id } })
}

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

// Expose refs for testing
defineExpose({
  showCreateForm,
})
</script>
