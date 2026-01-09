<script setup lang="ts">
import { ref } from 'vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import type { MultiSelectBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: MultiSelectBlock
  interactive?: boolean
}>()

const emit = defineEmits<{
  interact: [blockId: string, value: string[]]
  skip: []
}>()

const selected = ref<string[]>([])
const interacting = ref(false)

function handleSubmit() {
  if (props.interactive && selected.value.length > 0 && !interacting.value) {
    interacting.value = true
    emit('interact', props.block.id, selected.value)
  }
}

function handleSkip() {
  emit('skip')
}

function toggleOption(value: string) {
  if (interacting.value) return

  const index = selected.value.indexOf(value)
  if (index === -1) {
    selected.value.push(value)
  } else {
    selected.value.splice(index, 1)
  }
}
</script>

<template>
  <div class="space-y-3">
    <p class="text-sm font-medium">{{ block.label }}</p>
    <div class="space-y-2">
      <div v-for="option in block.options" :key="option.value" class="flex items-start gap-2">
        <Checkbox
          :id="option.value"
          :checked="selected.includes(option.value)"
          :disabled="!interactive || interacting"
          @update:checked="toggleOption(option.value)"
        />
        <div class="grid gap-1.5 leading-none">
          <Label :for="option.value" class="text-sm font-normal cursor-pointer">
            {{ option.label }}
          </Label>
          <p v-if="option.description" class="text-xs text-muted-foreground">
            {{ option.description }}
          </p>
        </div>
      </div>
    </div>
    <div class="flex items-center justify-between">
      <Button
        size="sm"
        :disabled="!interactive || selected.length === 0 || interacting"
        @click="handleSubmit"
      >
        Submit ({{ selected.length }} selected)
      </Button>
      <Button
        v-if="interactive && !interacting"
        variant="ghost"
        size="sm"
        @click="handleSkip"
      >
        Skip
      </Button>
    </div>
    <div v-if="interacting" class="text-sm text-muted-foreground">
      Sending...
    </div>
  </div>
</template>
