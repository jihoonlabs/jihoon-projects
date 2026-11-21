<script setup lang="ts">
import { DEMO_GUIDE } from '../../constants/ticketMessages';
</script>

<template>
  <aside :class="$style.guide" aria-label="デモの使い方">
    <strong>{{ DEMO_GUIDE.title }}</strong>
    <ol>
      <li v-for="step in DEMO_GUIDE.steps" :key="step">{{ step }}</li>
    </ol>
    <p>{{ DEMO_GUIDE.note }}</p>
  </aside>
</template>

<style module lang="scss">
.guide {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
  border: 1px solid #bfdbfe;
  border-radius: 0.75rem;
  background: #eff6ff;
  color: #1e3a5f;
  line-height: 1.55;

  strong {
    display: block;
    margin-bottom: 0.25rem;
  }

  ol {
    display: grid;
    gap: 0.2rem;
    margin: 0.4rem 0;
    padding-left: 1.4rem;
  }

  p {
    margin: 0.45rem 0 0;
    color: #475569;
    font-size: 0.875rem;
  }
}
</style>
