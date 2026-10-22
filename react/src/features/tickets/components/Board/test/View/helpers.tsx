import { expect } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { TicketBoardView } from '../../View';

export async function renderSelectedProject() {
  render(<TicketBoardView />);
  await waitFor(() =>
    expect(
      screen
        .getByRole('combobox', { name: 'プロジェクト' })
        .querySelector('option[value="1"]'),
    ).not.toBeNull(),
  );
  fireEvent.change(screen.getByRole('combobox', { name: 'プロジェクト' }), {
    target: { value: '1' },
  });
}
