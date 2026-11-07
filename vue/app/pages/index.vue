<template>
  <main :class="$style.page">
    <h1 :class="$style.title">タスク管理</h1>
    <p :class="$style.description">Vue 版は準備中です。</p>
  </main>
</template>

<style module lang="scss">
.page {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
}

.title {
  margin: 0;
  font-size: 1.5rem;
}

.description {
  margin: 0;
  color: var(--text-secondary);
}
</style>
