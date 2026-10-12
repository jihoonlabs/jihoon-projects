import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { toTicket } from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import Card from '../Card';

it('opens details from the title or card double click while leaving status controls independent', () => {
  const ticket = toTicket(responseTicket);
  const open = vi.fn();
  const status = vi.fn();
  render(
    <Card
      ticket={ticket}
      onOpenDetails={open}
      onStatusChange={status}
      projectKey="ABC"
    />,
  );
  const title = screen.getByRole('button', { name: 'TICK-1 の詳細を開く' });
  expect(
    screen.queryByRole('button', { name: '詳細' }),
  ).not.toBeInTheDocument();
  fireEvent.click(title);
  expect(open).toHaveBeenLastCalledWith(ticket, title);
  open.mockClear();
  fireEvent.doubleClick(screen.getByRole('group'));
  expect(open).toHaveBeenCalledTimes(1);
  expect(open).toHaveBeenLastCalledWith(ticket, title);
  open.mockClear();
  const select = screen.getByRole('combobox');
  fireEvent.doubleClick(select);
  fireEvent.change(select, { target: { value: 'DONE' } });
  expect(open).not.toHaveBeenCalled();
  expect(status).toHaveBeenCalledWith(ticket.id, 'DONE');
});
