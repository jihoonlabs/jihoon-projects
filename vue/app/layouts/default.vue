<template>
  <div :class="$style.layout">
    <slot />
  </div>
</template>

<style module lang="scss">
.layout {
  display: flex;
  flex: 1;
  flex-direction: column;
}
</style>
