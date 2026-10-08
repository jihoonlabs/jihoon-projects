import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { toTicket } from '../../../api/ticketApi';
import { responseTicket } from '../../../api/test/ticketFixture';
import { getProjectBorderColor } from '../../../utils/projectColor';
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

it('uses the selected project key for subtle card borders without replacing ticket cues', () => {
  const tickets = [
    toTicket(responseTicket),
    toTicket({ ...responseTicket, id: '2', issue_key: 'ABC-2', title: 'Second ticket' }),
  ];
  const { rerender } = render(
    <Main
      tickets={tickets}
      projectKey="ABC"
      searchQuery=""
      assigneeFilter="ALL"
      currentUserId={7}
    />,
  );

  const firstCard = screen.getByText('First ticket').closest('[aria-roledescription="sortable"]');
  const secondCard = screen.getByText('Second ticket').closest('[aria-roledescription="sortable"]');
  expect(firstCard).not.toBeNull();
  expect(secondCard).not.toBeNull();
  expect(firstCard).toHaveAttribute('role', 'button');
  expect(firstCard).toHaveAttribute('tabindex', '0');
  expect(firstCard?.getAttribute('style')).toContain(getProjectBorderColor('ABC'));
  expect(secondCard?.getAttribute('style')).toContain(getProjectBorderColor('ABC'));
  expect(screen.getByText('TICK-1')).toBeInTheDocument();
  expect(screen.getByText('ABC-2')).toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'First ticket のステータス' })).toBeInTheDocument();
  expect(screen.getAllByText('中')).toHaveLength(2);

  rerender(
    <Main
      tickets={tickets}
      projectKey="XYZ"
      searchQuery=""
      assigneeFilter="ALL"
      currentUserId={7}
    />,
  );
  expect(screen.getByText('First ticket').closest('[aria-roledescription="sortable"]')?.getAttribute('style'))
    .toContain(getProjectBorderColor('XYZ'));
});
