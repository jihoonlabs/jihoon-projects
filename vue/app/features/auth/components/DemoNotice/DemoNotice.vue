<script setup lang="ts">
/**
 * 公開デモでだけ出す、デモの使い方と注意事項
 */
const demoMode = useRuntimeConfig().public.demoMode === true;
</script>

<template>
  <aside v-if="demoMode" :class="$style.notice">
    <strong>公開デモ</strong>
    <p>一般ユーザーと管理者を選んで、プロジェクトの表示範囲を比べられます。</p>
    <p>
      データは全員で共有する架空データです。個人情報は入力しないでください。
    </p>
    <p>新規登録・メール送信・Google/LINE認証はデモでは利用できません。</p>
  </aside>
</template>

<style module lang="scss">
.notice {
  max-width: 440px;
  font-size: 0.85rem;
  text-align: center;
}
</style>
