import { screen } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { renderScreen } from '~/test/renderScreen';

import IndexPage from '../index.vue';

describe('トップページ', () => {
  it('アプリ名を見出しとして表示すること', async () => {
    await renderScreen(IndexPage);

    expect(
      screen.getByRole('heading', { level: 1, name: 'タスク管理' }),
    ).toBeInTheDocument();
  });

  it('Vue 版が準備中であることを表示すること', async () => {
    await renderScreen(IndexPage);

    expect(screen.getByText('Vue 版は準備中です。')).toBeInTheDocument();
  });
});
