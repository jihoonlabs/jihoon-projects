<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    id: string;
    label: string;
    type?: string;
    autocomplete?: string;
    placeholder?: string;
    /** 表示中の入力エラー。あれば aria-invalid と説明文で入力欄に結び付ける */
    error?: string;
    disabled?: boolean;
  }>(),
  {
    type: 'text',
    autocomplete: undefined,
    placeholder: undefined,
    error: undefined,
    disabled: false,
  },
);

const model = defineModel<string>({ required: true });

const errorId = computed(() => `${props.id}-error`);
</script>

<template>
  <div :class="$style.field">
    <label :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="model"
      :type="type"
      :autocomplete="autocomplete"
      :placeholder="placeholder"
      :aria-invalid="Boolean(error)"
      :aria-describedby="error ? errorId : undefined"
      :disabled="disabled"
      required
    />
    <span v-if="error" :id="errorId" :class="$style.error">{{ error }}</span>
  </div>
</template>

<style module lang="scss">
.field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;

  label {
    color: #475569;
    font-size: 0.8rem;
    font-weight: 600;
  }

  input {
    width: 100%;
    min-height: 44px;
    padding: 0.7rem 0.85rem;
    color: #17243b;
    background: #f8fafc;
    border: 1px solid #dce2eb;
    border-radius: 8px;
    font: inherit;
    font-size: 0.9rem;

    &:focus-visible {
      outline: 2px solid #3b6de0;
      outline-offset: 2px;
    }

    &[aria-invalid='true'] {
      border-color: #c66565;
    }

    &:disabled {
      opacity: 0.7;
      cursor: wait;
    }
  }
}

.error {
  color: #b91c1c;
  font-size: 0.75rem;
}
</style>
