<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? 'Edit Agent' : 'Create New Agent' }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? 'Update agent configuration' : 'Configure a new AI agent' }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Name (only for create) -->
        <div v-if="!isEdit">
          <Label for="name">Name (Internal ID) *</Label>
          <Input
            id="name"
            v-model="formData.name"
            placeholder="e.g., brainstorm-agent"
            required
            :disabled="isEdit"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Lowercase with hyphens, used as unique identifier
          </p>
        </div>

        <!-- Display Name -->
        <div>
          <Label for="display_name">Display Name *</Label>
          <Input
            id="display_name"
            v-model="formData.display_name"
            placeholder="e.g., Brainstorming Assistant"
            required
          />
        </div>

        <!-- Description -->
        <div>
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="formData.description"
            placeholder="Brief description of the agent's purpose"
            rows="2"
          />
        </div>

        <!-- Avatar -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <Label for="avatar_url">Avatar Emoji</Label>
            <Input
              id="avatar_url"
              v-model="formData.avatar_url"
              placeholder="🤖"
              maxlength="2"
            />
          </div>
          <div>
            <Label for="avatar_color">Avatar Color</Label>
            <Input
              id="avatar_color"
              v-model="formData.avatar_color"
              type="color"
            />
          </div>
        </div>

        <!-- Model -->
        <div>
          <Label for="model">Model *</Label>
          <Select v-model="formData.model" required>
            <SelectTrigger>
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="claude-sonnet-4-5">Claude Sonnet 4.5</SelectItem>
              <SelectItem value="claude-opus-4-5">Claude Opus 4.5</SelectItem>
              <SelectItem value="claude-sonnet-3-5">Claude Sonnet 3.5</SelectItem>
              <SelectItem value="claude-haiku-3-5">Claude Haiku 3.5</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- System Prompt -->
        <div>
          <Label for="system_prompt">System Prompt *</Label>
          <Textarea
            id="system_prompt"
            v-model="formData.system_prompt"
            placeholder="You are a helpful AI assistant..."
            rows="4"
            required
          />
        </div>

        <!-- Personality Traits -->
        <div>
          <Label for="personality_traits">Personality Traits</Label>
          <Input
            id="personality_traits"
            v-model="personalityTraitsInput"
            placeholder="creative, analytical, friendly (comma-separated)"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Enter traits separated by commas
          </p>
          <div v-if="formData.personality_traits.length > 0" class="flex flex-wrap gap-1 mt-2">
            <Badge
              v-for="(trait, index) in formData.personality_traits"
              :key="index"
              variant="secondary"
              class="cursor-pointer"
              @click="removeTrait(index)"
            >
              {{ trait }}
              <X class="ml-1 h-3 w-3" />
            </Badge>
          </div>
        </div>

        <!-- Temperature -->
        <div>
          <Label for="temperature">Temperature: {{ formData.temperature }}</Label>
          <Input
            id="temperature"
            v-model.number="formData.temperature"
            type="range"
            min="0"
            max="2"
            step="0.1"
          />
          <p class="text-xs text-muted-foreground mt-1">
            0 = deterministic, 2 = very creative
          </p>
        </div>

        <!-- Max Context Tokens -->
        <div>
          <Label for="max_context_tokens">Max Context Tokens</Label>
          <Input
            id="max_context_tokens"
            v-model.number="formData.max_context_tokens"
            type="number"
            min="1000"
            max="1000000"
          />
        </div>

        <!-- Checkboxes -->
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <Checkbox
              id="enabled"
              :checked="formData.enabled"
              @update:checked="formData.enabled = $event"
            />
            <Label for="enabled" class="font-normal cursor-pointer">Enabled</Label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="is_default"
              :checked="formData.is_default"
              @update:checked="formData.is_default = $event"
            />
            <Label for="is_default" class="font-normal cursor-pointer">Set as default agent</Label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="streaming_enabled"
              :checked="formData.streaming_enabled"
              @update:checked="formData.streaming_enabled = $event"
            />
            <Label for="streaming_enabled" class="font-normal cursor-pointer">
              Enable streaming
            </Label>
          </div>
        </div>

        <!-- Version -->
        <div>
          <Label for="version">Version</Label>
          <Input
            id="version"
            v-model="formData.version"
            placeholder="1.0.0"
          />
        </div>

        <!-- Actions -->
        <DialogFooter>
          <Button type="button" variant="outline" @click="$emit('update:open', false)">
            Cancel
          </Button>
          <Button type="submit" :disabled="submitting">
            {{ submitting ? 'Saving...' : isEdit ? 'Update' : 'Create' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { X } from 'lucide-vue-next'
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
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { AgentTypeResponse, AgentTypeCreate, AgentTypeUpdate } from '@/api/admin'

const props = defineProps<{
  open: boolean
  agent?: AgentTypeResponse | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [data: AgentTypeCreate | AgentTypeUpdate]
}>()

const isEdit = computed(() => !!props.agent)

const formData = ref<AgentTypeCreate>({
  name: '',
  display_name: '',
  description: '',
  avatar_url: '🤖',
  avatar_color: '#6366f1',
  personality_traits: [],
  model: 'claude-sonnet-4-5',
  system_prompt: '',
  streaming_enabled: true,
  max_context_tokens: 200000,
  temperature: 0.7,
  enabled: true,
  is_default: false,
  version: '1.0.0',
})

const personalityTraitsInput = ref('')

// Reset form when dialog opens/closes or agent changes
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.agent) {
        // Edit mode: populate with agent data
        formData.value = {
          name: props.agent.name,
          display_name: props.agent.display_name,
          description: props.agent.description || '',
          avatar_url: props.agent.avatar_url || '🤖',
          avatar_color: props.agent.avatar_color,
          personality_traits: [...props.agent.personality_traits],
          model: props.agent.model,
          system_prompt: props.agent.system_prompt,
          streaming_enabled: props.agent.streaming_enabled,
          max_context_tokens: props.agent.max_context_tokens,
          temperature: props.agent.temperature,
          enabled: props.agent.enabled,
          is_default: props.agent.is_default,
          version: props.agent.version,
        }
        personalityTraitsInput.value = props.agent.personality_traits.join(', ')
      } else {
        // Create mode: reset to defaults
        formData.value = {
          name: '',
          display_name: '',
          description: '',
          avatar_url: '🤖',
          avatar_color: '#6366f1',
          personality_traits: [],
          model: 'claude-sonnet-4-5',
          system_prompt: '',
          streaming_enabled: true,
          max_context_tokens: 200000,
          temperature: 0.7,
          enabled: true,
          is_default: false,
          version: '1.0.0',
        }
        personalityTraitsInput.value = ''
      }
    }
  },
  { immediate: true }
)

// Update personality traits when input changes
watch(personalityTraitsInput, (value) => {
  if (value) {
    formData.value.personality_traits = value
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)
  } else {
    formData.value.personality_traits = []
  }
})

function removeTrait(index: number) {
  formData.value.personality_traits.splice(index, 1)
  personalityTraitsInput.value = formData.value.personality_traits.join(', ')
}

function handleSubmit() {
  if (isEdit.value) {
    // For edit, exclude the name field
    const { name, ...updateData } = formData.value
    emit('submit', updateData)
  } else {
    emit('submit', formData.value)
  }
}
</script>
