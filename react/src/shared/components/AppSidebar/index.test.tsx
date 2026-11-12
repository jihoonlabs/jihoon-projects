import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

import { AppSidebar } from './index';

const { pathname } = vi.hoisted(() => ({ pathname: vi.fn() }));
vi.mock('next/navigation', () => ({ usePathname: pathname }));

beforeEach(() => pathname.mockReturnValue('/attendance'));

it('出退勤とチケットのリンクを表示し、現在のページを示す', () => {
  render(<AppSidebar />);

  expect(
    screen.getByRole('navigation', { name: 'アプリメニュー' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '出退勤' })).toHaveAttribute(
    'href',
    '/attendance',
  );
  expect(screen.getByRole('link', { name: '出退勤' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  expect(screen.getByRole('link', { name: 'チケット' })).toHaveAttribute(
    'href',
    '/tickets',
  );
  expect(screen.getByRole('link', { name: 'チケット' })).not.toHaveAttribute(
    'aria-current',
  );
});

it('チケット配下のページでもチケットのリンクを選択中として示す', () => {
  pathname.mockReturnValue('/tickets/project-1');
  render(<AppSidebar />);

  expect(screen.getByRole('link', { name: 'チケット' })).toHaveAttribute(
    'aria-current',
    'page',
  );
});
