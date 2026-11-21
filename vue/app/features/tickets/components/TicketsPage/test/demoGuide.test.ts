import { screen } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import { signInAs } from '~/test/auth/signInAs';
import { enableDemoMode } from '~/test/demoMode';
import { renderRoute } from '~/test/renderRoute';

describe('チケットボードのデモ案内', () => {
  it('公開デモでは、使い方の案内を表示すること', async () => {
    signInAs();
    enableDemoMode();

    await renderRoute('/tickets');

    expect(
      await screen.findByRole('complementary', { name: 'デモの使い方' }),
    ).toBeInTheDocument();
  });

  it('通常の環境では、案内を表示しないこと', async () => {
    signInAs();

    await renderRoute('/tickets');

    await screen.findByRole('heading', { name: 'チケット管理' });
    expect(
      screen.queryByRole('complementary', { name: 'デモの使い方' }),
    ).not.toBeInTheDocument();
  });
});
