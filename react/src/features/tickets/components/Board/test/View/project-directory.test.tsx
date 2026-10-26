import './setup';
import { expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { TicketBoardView } from '../../View';
import * as projectApi from '@/features/tickets/api/projectApi';

it('keeps the project directory off the board until requested and closes after selection', async () => {
  const user = userEvent.setup();
  render(<TicketBoardView />);
  await screen.findByRole('option', { name: 'General' });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  const trigger = screen.getByRole('button', {
    name: 'プロジェクト一覧・作成',
  });
  await user.click(trigger);
  const dialog = screen.getByRole('dialog', { name: 'プロジェクト一覧' });
  expect(within(dialog).getByRole('searchbox')).toHaveFocus();
  await user.click(
    within(dialog).getByRole('button', { name: 'General GEN ボードを開く' }),
  );
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'プロジェクト' })).toHaveValue(
    '1',
  );
  expect(trigger).toHaveFocus();
});

it('opens creation directly and blocks closing until a failed save can be retried', async () => {
  const user = userEvent.setup();
  let rejectSave!: (reason: Error) => void;
  vi.mocked(projectApi.createProject).mockImplementation(
    () =>
      new Promise((_, reject) => {
        rejectSave = reject;
      }),
  );
  render(<TicketBoardView />);
  await screen.findByRole('option', { name: 'General' });
  const trigger = screen.getByRole('button', { name: '+ プロジェクト作成' });
  await user.click(trigger);
  const dialog = screen.getByRole('dialog', { name: 'プロジェクト一覧' });
  const input = within(dialog).getByLabelText('プロジェクト名');
  expect(input).toHaveFocus();
  await user.type(input, 'Draft team');
  await user.click(
    within(dialog).getByRole('button', { name: 'プロジェクトを作成' }),
  );
  expect(
    within(dialog).getByRole('button', { name: 'プロジェクト一覧を閉じる' }),
  ).toBeDisabled();
  fireEvent(dialog, new Event('cancel', { cancelable: true }));
  expect(dialog).toBeInTheDocument();
  await act(async () => rejectSave(new Error('Please retry')));
  expect(within(dialog).getByRole('alert')).toHaveTextContent('Please retry');
  expect(input).toHaveValue('Draft team');
  fireEvent(dialog, new Event('cancel', { cancelable: true }));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
