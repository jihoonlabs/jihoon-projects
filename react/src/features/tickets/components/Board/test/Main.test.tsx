import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { toTicket } from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import Main from '../Main';

it('renders null issue keys safely and searches actual ticket numbers', () => {
  const tickets = [
    toTicket({
      ...responseTicket,
      id: '2',
      title: 'Missing key',
      issue_key: null,
      assignee: null,
    }),
    toTicket(responseTicket),
  ];
  const { rerender } = render(
    <Main tickets={tickets} searchQuery="" assigneeFilter="ALL" />,
  );
  expect(screen.getByText('—')).toBeInTheDocument();
  rerender(
    <Main tickets={tickets} searchQuery="tick-1" assigneeFilter="ALL" />,
  );
  expect(screen.getByText('First ticket')).toBeInTheDocument();
  expect(screen.queryByText('Missing key')).not.toBeInTheDocument();
  rerender(
    <Main tickets={tickets} searchQuery="" assigneeFilter="UNASSIGNED" />,
  );
  expect(screen.getByText('Missing key')).toBeInTheDocument();
  expect(screen.queryByText('First ticket')).not.toBeInTheDocument();
});

it('renders each column in client position order without mutating input', () => {
  const tickets = [
    toTicket({ ...responseTicket, title: 'Last' }, 10),
    toTicket({ ...responseTicket, id: '2', title: 'First' }, 2),
  ];
  render(<Main tickets={tickets} searchQuery="" assigneeFilter="ALL" />);
  expect(
    screen
      .getByText('First')
      .compareDocumentPosition(screen.getByText('Last')) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(tickets[0].title).toBe('Last');
});
