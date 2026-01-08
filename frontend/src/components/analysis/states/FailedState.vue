<script setup lang="ts">
defineProps<{
  message?: string
}>()

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div>Failed: {{ message }}</div>
</template>
