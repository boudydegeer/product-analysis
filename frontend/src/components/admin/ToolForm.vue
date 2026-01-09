<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? 'Edit Tool' : 'Create New Tool' }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? 'Update tool configuration' : 'Configure a new tool for agents' }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Name (only for create) -->
        <div v-if="!isEdit">
          <Label for="name">Name *</Label>
          <Input
            id="name"
            v-model="formData.name"
            placeholder="e.g., web_search"
            required
            :disabled="isEdit"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Unique identifier for the tool
          </p>
        </div>

        <!-- Description -->
        <div>
          <Label for="description">Description *</Label>
          <Textarea
            id="description"
            v-model="formData.description"
            placeholder="Brief description of what this tool does"
            rows="2"
            required
          />
        </div>

        <!-- Category -->
        <div>
          <Label for="category">Category *</Label>
          <Input
            id="category"
            v-model="formData.category"
            placeholder="e.g., search, data, communication"
            required
          />
        </div>

        <!-- Tool Type -->
        <div>
          <Label for="tool_type">Tool Type *</Label>
          <Select v-model="formData.tool_type" required>
            <SelectTrigger>
              <SelectValue placeholder="Select tool type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="builtin">Built-in</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
              <SelectItem value="mcp">MCP (Model Context Protocol)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Tool Definition (JSON) -->
        <div>
          <Label for="definition">Tool Definition (JSON) *</Label>
          <Textarea
            id="definition"
            v-model="definitionInput"
            placeholder='{"type": "function", "function": { ... }}'
            rows="6"
            required
            class="font-mono text-sm"
          />
          <p class="text-xs text-muted-foreground mt-1">
            JSON definition of the tool schema
          </p>
          <p v-if="definitionError" class="text-xs text-destructive mt-1">
            {{ definitionError }}
          </p>
        </div>

        <!-- Tags -->
        <div>
          <Label for="tags">Tags</Label>
          <Input
            id="tags"
            v-model="tagsInput"
            placeholder="api, external, premium (comma-separated)"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Enter tags separated by commas
          </p>
          <div v-if="formData.tags.length > 0" class="flex flex-wrap gap-1 mt-2">
            <Badge
              v-for="(tag, index) in formData.tags"
              :key="index"
              variant="secondary"
              class="cursor-pointer"
              @click="removeTag(index)"
            >
              {{ tag }}
              <X class="ml-1 h-3 w-3" />
            </Badge>
          </div>
        </div>

        <!-- Example Usage -->
        <div>
          <Label for="example_usage">Example Usage</Label>
          <Textarea
            id="example_usage"
            v-model="formData.example_usage"
            placeholder="Example of how to use this tool"
            rows="2"
          />
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
              id="is_dangerous"
              :checked="formData.is_dangerous"
              @update:checked="formData.is_dangerous = $event"
            />
            <Label for="is_dangerous" class="font-normal cursor-pointer">
              Dangerous (destructive actions)
            </Label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="requires_approval"
              :checked="formData.requires_approval"
              @update:checked="formData.requires_approval = $event"
            />
            <Label for="requires_approval" class="font-normal cursor-pointer">
              Requires approval before use
            </Label>
          </div>
        </div>

        <!-- Actions -->
        <DialogFooter>
          <Button type="button" variant="outline" @click="$emit('update:open', false)">
            Cancel
          </Button>
          <Button type="submit" :disabled="submitting || !!definitionError">
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
import type { ToolResponse, ToolCreate, ToolUpdate } from '@/api/admin'

const props = defineProps<{
  open: boolean
  tool?: ToolResponse | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [data: ToolCreate | ToolUpdate]
}>()

const isEdit = computed(() => !!props.tool)

const formData = ref<ToolCreate>({
  name: '',
  description: '',
  category: '',
  tool_type: 'builtin',
  definition: {},
  enabled: true,
  is_dangerous: false,
  requires_approval: false,
  version: '1.0.0',
  tags: [],
  example_usage: '',
})

const definitionInput = ref('')
const definitionError = ref('')
const tagsInput = ref('')

// Validate JSON definition
watch(definitionInput, (value) => {
  try {
    if (value.trim()) {
      formData.value.definition = JSON.parse(value)
      definitionError.value = ''
    } else {
      formData.value.definition = {}
      definitionError.value = ''
    }
  } catch (e) {
    definitionError.value = 'Invalid JSON'
  }
})

// Update tags when input changes
watch(tagsInput, (value) => {
  if (value) {
    formData.value.tags = value
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)
  } else {
    formData.value.tags = []
  }
})

// Reset form when dialog opens/closes or tool changes
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.tool) {
        // Edit mode: populate with tool data
        formData.value = {
          name: props.tool.name,
          description: props.tool.description,
          category: props.tool.category,
          tool_type: props.tool.tool_type as 'builtin' | 'custom' | 'mcp',
          definition: props.tool.definition,
          enabled: props.tool.enabled,
          is_dangerous: props.tool.is_dangerous,
          requires_approval: props.tool.requires_approval,
          version: props.tool.version,
          tags: [...props.tool.tags],
          example_usage: props.tool.example_usage || '',
        }
        definitionInput.value = JSON.stringify(props.tool.definition, null, 2)
        tagsInput.value = props.tool.tags.join(', ')
      } else {
        // Create mode: reset to defaults
        formData.value = {
          name: '',
          description: '',
          category: '',
          tool_type: 'builtin',
          definition: {},
          enabled: true,
          is_dangerous: false,
          requires_approval: false,
          version: '1.0.0',
          tags: [],
          example_usage: '',
        }
        definitionInput.value = ''
        tagsInput.value = ''
      }
      definitionError.value = ''
    }
  },
  { immediate: true }
)

function removeTag(index: number) {
  formData.value.tags.splice(index, 1)
  tagsInput.value = formData.value.tags.join(', ')
}

function handleSubmit() {
  if (definitionError.value) {
    return
  }

  if (isEdit.value) {
    // For edit, exclude the name field
    const { name, ...updateData } = formData.value
    emit('submit', updateData)
  } else {
    emit('submit', formData.value)
  }
}
</script>
