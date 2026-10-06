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
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="ALL"
      currentUserId={7}
    />,
  );
  expect(screen.getByText('—')).toBeInTheDocument();
  rerender(
    <Main
      tickets={tickets}
      searchQuery="tick-1"
      assigneeFilter="ALL"
      currentUserId={7}
    />,
  );
  expect(screen.getByText('First ticket')).toBeInTheDocument();
  expect(screen.queryByText('Missing key')).not.toBeInTheDocument();
  rerender(
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="UNASSIGNED"
      currentUserId={7}
    />,
  );
  expect(screen.getByText('Missing key')).toBeInTheDocument();
  expect(screen.queryByText('First ticket')).not.toBeInTheDocument();
});

it('renders each column in client position order without mutating input', () => {
  const tickets = [
    toTicket({ ...responseTicket, title: 'Last', position: 10 }),
    toTicket({ ...responseTicket, id: '2', title: 'First', position: 2 }),
  ];
  render(
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="ALL"
      currentUserId={7}
    />,
  );
  expect(
    screen
      .getByText('First')
      .compareDocumentPosition(screen.getByText('Last')) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(tickets[0].title).toBe('Last');
});

it('filters assigned tickets by the signed-in user ID', () => {
  const tickets = [
    toTicket({ ...responseTicket, title: 'Mine' }),
    toTicket({
      ...responseTicket,
      id: '2',
      title: 'Someone else',
      assignee: { id: 1, name: 'Other', avatar_url: null },
    }),
  ];
  const { rerender } = render(
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="ME"
      currentUserId={7}
    />,
  );
  expect(screen.getByText('Mine')).toBeInTheDocument();
  expect(screen.queryByText('Someone else')).not.toBeInTheDocument();

  rerender(
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="ME"
      currentUserId={1}
    />,
  );
  expect(screen.getByText('Someone else')).toBeInTheDocument();
  expect(screen.queryByText('Mine')).not.toBeInTheDocument();

  rerender(
    <Main
      tickets={tickets}
      searchQuery=""
      assigneeFilter="ME"
      currentUserId={null}
    />,
  );
  expect(screen.queryByText('Someone else')).not.toBeInTheDocument();
  expect(screen.queryByText('Mine')).not.toBeInTheDocument();
});
