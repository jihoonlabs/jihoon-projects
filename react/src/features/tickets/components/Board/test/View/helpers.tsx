import { fireEvent, render, screen } from '@testing-library/react';
import { TicketBoardView } from '../../View';

export async function renderSelectedProject() {
  render(<TicketBoardView />);
  const projectSelect = screen.getByRole('combobox', { name: 'プロジェクト' });
  await screen.findByRole('option', { name: 'General' });
  fireEvent.change(projectSelect, {
    target: { value: '1' },
  });
}
