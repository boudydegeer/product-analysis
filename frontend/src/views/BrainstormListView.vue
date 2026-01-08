<template>
  <div class="container mx-auto py-6">
    <BrainstormList
      @create-session="showCreateDialog = true"
      @select-session="navigateToSession"
    />

    <!-- Create Session Dialog -->
    <Dialog v-model:open="showCreateDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Brainstorming Session</DialogTitle>
          <DialogDescription>
            Create a new session to collaborate with Claude on ideas
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="handleCreate" class="space-y-4">
          <div class="space-y-2">
            <Label for="title">Title</Label>
            <Input
              id="title"
              v-model="formData.title"
              placeholder="Mobile App Redesign"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="formData.description"
              placeholder="Explore ideas for reimagining our mobile experience"
              rows="4"
              required
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              @click="showCreateDialog = false"
            >
              Cancel
            </Button>
            <Button type="submit" :disabled="loading">
              Create Session
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
import { useBrainstormStore } from '@/stores/brainstorm'
import BrainstormList from '@/components/BrainstormList.vue'
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

const router = useRouter()
const store = useBrainstormStore()

const showCreateDialog = ref(false)
const formData = ref({
  title: '',
  description: '',
})

const loading = computed(() => store.loading)

async function handleCreate() {
  try {
    const session = await store.createSession(formData.value)
    showCreateDialog.value = false
    formData.value = { title: '', description: '' }
    router.push(`/brainstorm/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

function navigateToSession(id: string) {
  router.push(`/brainstorm/${id}`)
}
</script>
