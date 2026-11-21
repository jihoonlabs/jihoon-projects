<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { getProjectBorderColor } from '../../utils/projectColor';

const props = defineProps<{
  heading: string;
  issueKey?: string | null;
  /** 見出しにフォーカスを置く（詳細表示・読み込み中の案内） */
  focusHeading: boolean;
  projectColor: string | null;
  /** 保存・削除の最中は、背景や Escape で閉じない */
  locked: boolean;
}>();

const emit = defineEmits<{ close: [] }>();

const headingElement = ref<HTMLHeadingElement | null>(null);
const borderColor = getProjectBorderColor(props.projectColor);

function close() {
  if (!props.locked) emit('close');
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close();
}

const focusIfNeeded = () => {
  if (props.focusHeading) headingElement.value?.focus();
};

onMounted(() => {
  focusIfNeeded();
  document.addEventListener('keydown', onKeydown);
});
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown));
watch(
  () => props.focusHeading,
  () => void nextTick(focusIfNeeded),
);
</script>

<template>
  <div :class="$style.backdrop" role="presentation" @mousedown.self="close">
    <section
      :class="$style.modal"
      :style="borderColor ? { '--project-color': borderColor } : undefined"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ticket-modal-title"
    >
      <header :class="$style.header">
        <span v-if="issueKey" :class="$style.key">{{ issueKey }}</span>
        <h2
          id="ticket-modal-title"
          ref="headingElement"
          :tabindex="focusHeading ? -1 : undefined"
          :class="$style.title"
        >
          {{ heading }}
        </h2>
      </header>
      <slot />
    </section>
  </div>
</template>

<style module lang="scss">
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(17, 24, 39, 0.4);
}

.modal {
  width: min(36rem, 100%);
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.25rem;
  border-top: 4px solid var(--project-color, #d1d5db);
  border-radius: 0.75rem;
  background: #fff;
  color: #111827;
}

.header {
  margin-bottom: 1rem;
}

.key {
  color: #6b7280;
  font-size: 0.75rem;
}

.title {
  margin: 0.25rem 0 0;
  font-size: 1.25rem;
  font-weight: 700;
  outline: none;
}
</style>
