<script setup lang="ts">
import type { Ticket } from '../../types/ticket';

defineProps<{
  latest: Ticket | null;
  reloading: boolean;
  reloadError: string | null;
  unavailable: boolean;
}>();

defineEmits<{ reload: []; adopt: [] }>();
</script>

<template>
  <section aria-label="競合の解決">
    <button type="button" :disabled="reloading" @click="$emit('reload')">
      {{ reloading ? '取得中...' : '最新情報を再取得' }}
    </button>
    <p v-if="reloadError" role="alert">{{ reloadError }}</p>
    <div v-if="latest">
      <h3>最新情報</h3>
      <p>タイトル: {{ latest.title }}</p>
      <p>説明: {{ latest.description || '説明はありません。' }}</p>
      <p>ステータス: {{ latest.status }} / 優先度: {{ latest.priority }}</p>
      <p>担当者: {{ latest.assignee?.name ?? '未割り当て' }}</p>
      <button type="button" :disabled="unavailable" @click="$emit('adopt')">
        最新情報で編集し直す（入力を置き換える）
      </button>
    </div>
  </section>
</template>
