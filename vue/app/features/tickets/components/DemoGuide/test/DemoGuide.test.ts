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
    expect(
      within(guide).getByText(/個人情報は入力しないでください/),
    ).toBeInTheDocument();
  });

  it('状態の変更を、編集画面の項目名と保存の操作で案内すること', () => {
    render(DemoGuide);

    const guide = screen.getByRole('complementary', { name: 'デモの使い方' });
    expect(
      within(guide).getByText(
        /「編集」を開き、「ステータス」を変更して「保存」を押してください/,
      ),
    ).toBeInTheDocument();
  });

  it('まだ提供していない機能（コメント）は案内しないこと', () => {
    render(DemoGuide);

    const guide = screen.getByRole('complementary', { name: 'デモの使い方' });
    expect(within(guide).queryByText(/コメント/)).not.toBeInTheDocument();
  });
});
