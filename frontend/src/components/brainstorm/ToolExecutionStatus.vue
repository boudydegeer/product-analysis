<script setup lang="ts">
import { Search } from 'lucide-vue-next'
</script>

<template>
  <div class="flex items-center gap-2 text-sm text-muted-foreground">
    <Search class="h-4 w-4 animate-pulse" />
    <span>Analizando codebase</span>
    <div class="flex gap-0.5">
      <div class="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.3s]"></div>
      <div class="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.15s]"></div>
      <div class="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce"></div>
    </div>
  </div>
</template>
