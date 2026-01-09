<template>
  <BrainstormChat :session-id="sessionId" />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import BrainstormChat from '@/components/BrainstormChat.vue'

const route = useRoute()
const sessionId = route.params.id as string
</script>
