// @nuxt/eslint が生成する設定（nuxt prepare で .nuxt に出力）を使う
import withNuxt from './.nuxt/eslint.config.mjs';

export default withNuxt({
  rules: {
    // 整形は Prettier に任せる。Prettier は空要素を <input /> の形で出力するため、それに合わせる
    'vue/html-self-closing': [
      'error',
      {
        html: { void: 'always', normal: 'always', component: 'always' },
        svg: 'always',
        math: 'always',
      },
    ],
  },
});
