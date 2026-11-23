import { render, screen, within } from '@testing-library/vue';
import { describe, expect, it } from 'vitest';

import DemoGuide from '../DemoGuide.vue';

describe('デモの使い方', () => {
  it('お試しの手順と、共通デモである注意を表示すること', () => {
    render(DemoGuide);

    const guide = screen.getByRole('complementary', { name: 'デモの使い方' });
    expect(
      within(guide).getByText('まずはこの3つをお試しください'),
    ).toBeInTheDocument();
    expect(within(guide).getAllByRole('listitem')).toHaveLength(4);
    // 状態はカードではなく、モーダルの編集から変える
    expect(
      within(guide).getByText(/「編集」を開き、「状態」を変える/),
    ).toBeInTheDocument();
    // まだ提供していない機能（コメント）は案内しない
    expect(within(guide).queryByText(/コメント/)).not.toBeInTheDocument();
    expect(
      within(guide).getByText(/個人情報は入力しないでください/),
    ).toBeInTheDocument();
  });
});
