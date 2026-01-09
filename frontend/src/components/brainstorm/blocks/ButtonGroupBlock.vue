<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import type { ButtonGroupBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: ButtonGroupBlock
  interactive?: boolean
}>()

const emit = defineEmits<{
  interact: [blockId: string, value: string]
  skip: []
}>()

const interacting = ref(false)
const selectedValue = ref<string | null>(null)

function handleClick(value: string) {
  if (props.interactive && !interacting.value) {
    console.log('[ButtonGroupBlock] Clicked:', {
      blockId: props.block.id,
      value,
      fullBlock: props.block
    })
    interacting.value = true
    selectedValue.value = value
    emit('interact', props.block.id, value)
  }
}

function handleSkip() {
  emit('skip')
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
        :disabled="!interactive || interacting"
        @click="handleClick(button.value)"
        class="w-full"
      >
        {{ button.label }}
      </Button>
    </div>
    <div v-if="interactive && !interacting" class="flex justify-end">
      <Button variant="ghost" size="sm" @click="handleSkip">
        Skip
      </Button>
    </div>
    <div v-if="interacting" class="text-sm text-muted-foreground">
      Sending...
    </div>
  </div>
</template>
