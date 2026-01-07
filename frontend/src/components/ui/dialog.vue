<script setup lang="ts">
import { DialogClose, DialogContent, DialogDescription, DialogOverlay, DialogPortal, DialogRoot, DialogTitle, DialogTrigger, type DialogContentEmits, type DialogContentProps, type DialogRootEmits, type DialogRootProps } from 'radix-vue'
import { X } from 'lucide-vue-next'
import { type HTMLAttributes, computed } from 'vue'
import { cn } from '@/lib/utils'

interface DialogProps extends DialogRootProps {
  open?: boolean
}

interface DialogEmits extends DialogRootEmits {}

const props = defineProps<DialogProps>()
const emits = defineEmits<DialogEmits>()
</script>

<template>
  <DialogRoot v-bind="props" @update:open="emits('update:open', $event)">
    <slot />
  </DialogRoot>
</template>

<script lang="ts">
export { DialogTrigger, DialogClose }
</script>
