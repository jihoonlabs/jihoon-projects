<template>
  <div :class="$style.layout">
    <!-- 認証まわりの画面（ログイン・会員登録・パスワード再設定）の共通の背景と配置 -->
    <slot />
  </div>
</template>

<style module lang="scss">
.layout {
  display: grid;
  flex: 1;
  place-items: center;
  align-content: center;
  gap: 1rem;
  min-height: 100vh;
  min-height: 100svh;
  padding: 2rem 1.25rem;
  background: #f3f5f9;
  color: #17243b;
  color-scheme: light;
}
</style>
