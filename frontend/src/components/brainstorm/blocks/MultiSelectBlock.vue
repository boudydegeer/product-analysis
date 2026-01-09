<script setup lang="ts">
import { ref, computed } from 'vue'
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

const selectedCount = computed(() => selected.value.length)
const canSubmit = computed(() => props.interactive && selectedCount.value > 0 && !interacting.value)

function handleSubmit() {
  if (canSubmit.value) {
    console.log('[MultiSelectBlock] Submitting with selected:', selected.value)
    interacting.value = true
    emit('interact', props.block.id, selected.value)
  }
}

function handleSkip() {
  emit('skip')
}

function isChecked(value: string) {
  return selected.value.includes(value)
}

function toggleOption(value: string, checked: boolean | 'indeterminate') {
  console.log('[MultiSelectBlock] toggleOption called:', {
    value,
    checked,
    interactive: props.interactive,
    interacting: interacting.value,
    currentSelected: [...selected.value]
  })

  if (interacting.value || !props.interactive) return

  const isBoolean = typeof checked === 'boolean'
  if (!isBoolean) return

  if (checked) {
    // Add to selection
    if (!selected.value.includes(value)) {
      selected.value = [...selected.value, value]
    }
  } else {
    // Remove from selection
    selected.value = selected.value.filter(v => v !== value)
  }

  console.log('[MultiSelectBlock] After toggle, selected:', [...selected.value], 'count:', selected.value.length)
}
</script>

<template>
  <div class="space-y-3">
    <p class="text-sm font-medium">{{ block.label }}</p>
    <div class="space-y-2">
      <div v-for="option in block.options" :key="option.value" class="flex items-start gap-2">
        <Checkbox
          :id="option.value"
          :model-value="isChecked(option.value)"
          :disabled="!interactive || interacting"
          @update:model-value="(checked) => toggleOption(option.value, checked)"
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
          :disabled="!canSubmit"
          @click="handleSubmit"
        >
          Submit ({{ selectedCount }} selected)
        </Button>
      </div>
    </TooltipProvider>
    <div v-if="interacting" class="text-sm text-muted-foreground">
      Sending...
    </div>
  </div>
</template>
