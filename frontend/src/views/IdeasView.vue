<template>
  <div class="container mx-auto py-6">
    <IdeaList @create-idea="showCreateDialog = true" @select-idea="navigateToIdea" />

    <!-- Create Idea Dialog -->
    <Dialog v-model:open="showCreateDialog">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New Idea</DialogTitle>
          <DialogDescription>
            Capture a new product idea and optionally evaluate it with AI
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="handleCreate" class="space-y-4">
          <div class="space-y-2">
            <Label for="title">Title</Label>
            <Input
              id="title"
              v-model="formData.title"
              placeholder="Dark Mode Feature"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="formData.description"
              placeholder="Add dark mode support to improve user experience in low-light environments"
              rows="4"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="priority">Priority</Label>
            <Select v-model="formData.priority">
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox id="evaluate" v-model:checked="evaluateAfterCreate" />
            <Label for="evaluate" class="cursor-pointer">
              Evaluate with AI after creation
            </Label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" @click="showCreateDialog = false">
              Cancel
            </Button>
            <Button type="submit" :disabled="loading || evaluating">
              {{ evaluating ? 'Evaluating...' : 'Create Idea' }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useIdeasStore } from '@/stores/ideas'
import type { IdeaPriority } from '@/types/idea'
import IdeaList from '@/components/IdeaList.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const router = useRouter()
const store = useIdeasStore()

const showCreateDialog = ref(false)
const evaluateAfterCreate = ref(true)
const formData = ref<{
  title: string
  description: string
  priority: IdeaPriority
}>({
  title: '',
  description: '',
  priority: 'medium',
})

const loading = computed(() => store.loading)
const evaluating = computed(() => store.evaluating)

async function handleCreate() {
  try {
    const idea = await store.createIdea(formData.value)

    // Evaluate if requested
    if (evaluateAfterCreate.value) {
      const evaluation = await store.evaluateIdea({
        title: formData.value.title,
        description: formData.value.description,
      })

      // Update idea with evaluation
      await store.updateIdea(idea.id, {
        business_value: evaluation.business_value,
        technical_complexity: evaluation.technical_complexity,
        estimated_effort: evaluation.estimated_effort,
        market_fit_analysis: evaluation.market_fit_analysis,
        risk_assessment: evaluation.risk_assessment,
      })
    }

    showCreateDialog.value = false
    formData.value = { title: '', description: '', priority: 'medium' }
    evaluateAfterCreate.value = true

    router.push(`/ideas/${idea.id}`)
  } catch (error) {
    console.error('Failed to create idea:', error)
  }
}

function navigateToIdea(id: string) {
  router.push(`/ideas/${id}`)
}
</script>
