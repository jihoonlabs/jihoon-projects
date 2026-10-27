import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

import { AppSidebar } from './index';

const { pathname } = vi.hoisted(() => ({ pathname: vi.fn() }));
vi.mock('next/navigation', () => ({ usePathname: pathname }));

beforeEach(() => pathname.mockReturnValue('/attendance'));

it('shows implemented modules and marks the current page', () => {
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

it('marks ticket subpages as active', () => {
  pathname.mockReturnValue('/tickets/project-1');
  render(<AppSidebar />);

  expect(screen.getByRole('link', { name: 'チケット' })).toHaveAttribute(
    'aria-current',
    'page',
  );
});
