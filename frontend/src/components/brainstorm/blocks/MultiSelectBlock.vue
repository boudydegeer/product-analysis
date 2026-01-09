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
}>()

const selected = ref<string[]>([])

function handleSubmit() {
  if (props.interactive && selected.value.length > 0) {
    emit('interact', props.block.id, selected.value)
  }
}

function toggleOption(value: string) {
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
          :disabled="!interactive"
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
    <Button
      size="sm"
      :disabled="!interactive || selected.length === 0"
      @click="handleSubmit"
    >
      Submit ({{ selected.length }} selected)
    </Button>
  </div>
</template>
