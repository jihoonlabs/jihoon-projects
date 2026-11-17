<script setup lang="ts">
defineProps<{
  loading: boolean;
  ticketError: string | null;
  projectError: string | null;
  memberError: string | null;
  noProjects: boolean;
  archived: boolean;
}>();

defineEmits<{
  retryTickets: [];
  retryMembers: [];
  retryProjects: [];
}>();
</script>

<template>
  <div :class="$style.notices">
    <p v-if="archived">
      終了したプロジェクトです。チケットとコメントは閲覧のみです。
    </p>
    <p v-if="loading" role="status">チケット一覧を更新中...</p>

    <div v-if="memberError" :class="$style.recovery">
      <p role="alert">{{ memberError }}</p>
      <button type="button" @click="$emit('retryMembers')">
        メンバーと権限を再取得
      </button>
    </div>
    <div v-if="ticketError" :class="$style.recovery">
      <p role="alert">{{ ticketError }}</p>
      <button type="button" :disabled="loading" @click="$emit('retryTickets')">
        チケット一覧を再取得
      </button>
    </div>
    <div v-if="projectError" :class="$style.recovery">
      <p role="alert">{{ projectError }}</p>
      <button type="button" @click="$emit('retryProjects')">
        プロジェクトを再取得
      </button>
    </div>
    <p v-if="noProjects">
      利用可能なプロジェクトがありません。リーダーにメンバー追加を依頼してください。
    </p>
  </div>
</template>

<style module lang="scss">
.notices {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: #374151;
}

.recovery {
  display: flex;
  align-items: center;
  gap: 0.75rem;

  [role='alert'] {
    color: #b91c1c;
  }
}
</style>
