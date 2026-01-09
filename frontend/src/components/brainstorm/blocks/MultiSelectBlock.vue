<script setup lang="ts">
import { ref } from 'vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
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

function toggleOption(value: string, checked: boolean) {
  console.log('[MultiSelectBlock] toggleOption called:', {
    value,
    checked,
    interactive: props.interactive,
    interacting: interacting.value,
    currentSelected: selected.value
  })

  if (interacting.value) return

  if (checked) {
    // Add to selection - create new array to trigger reactivity
    if (!selected.value.includes(value)) {
      selected.value = [...selected.value, value]
    }
  } else {
    // Remove from selection - create new array to trigger reactivity
    selected.value = selected.value.filter(v => v !== value)
  }

  console.log('[MultiSelectBlock] After toggle, selected:', selected.value)
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
          @update:checked="(checked: boolean) => toggleOption(option.value, checked)"
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
    <TooltipProvider v-if="interactive && !interacting">
      <div class="flex justify-between items-center">
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="sm" @click="handleSkip">
              Skip
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Skip to respond with your own text</p>
          </TooltipContent>
        </Tooltip>

        <Button
          size="sm"
          :disabled="!interactive || selected.length === 0 || interacting"
          @click="handleSubmit"
        >
          Submit ({{ selected.length }} selected)
        </Button>
      </div>
    </TooltipProvider>
    <div v-if="interacting" class="text-sm text-muted-foreground">
      Sending...
    </div>
  </div>
</template>
