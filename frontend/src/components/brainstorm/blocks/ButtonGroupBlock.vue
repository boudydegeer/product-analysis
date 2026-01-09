<script setup lang="ts">
import { Button } from '@/components/ui/button'
import type { ButtonGroupBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: ButtonGroupBlock
  interactive?: boolean
}>()

const emit = defineEmits<{
  interact: [blockId: string, value: string]
}>()

function handleClick(value: string) {
  if (props.interactive) {
    emit('interact', props.block.id, value)
  }
}
</script>

<template>
  <div class="space-y-2">
    <p v-if="block.label" class="text-sm font-medium">{{ block.label }}</p>
    <div class="grid grid-cols-2 gap-2">
      <Button
        v-for="button in block.buttons"
        :key="button.value"
        :variant="button.style === 'primary' ? 'default' : 'outline'"
        :disabled="!interactive"
        @click="handleClick(button.value)"
        class="w-full"
      >
        {{ button.label }}
      </Button>
    </div>
  </div>
</template>
