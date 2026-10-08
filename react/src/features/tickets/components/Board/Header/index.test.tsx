// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import Header from './index';

afterEach(cleanup);

describe('Project selector', () => {
  it('shows immutable keys and filters projects by name or key', () => {
    const onProjectQueryChange = vi.fn();
    const props = {
      searchQuery: '',
      onSearchChange: vi.fn(),
      assigneeFilter: 'ALL',
      onAssigneeChange: vi.fn(),
      onCreate: vi.fn(),
      projects: [
        { id: '1', name: 'Alpha', projectKey: 'ABC', boardVersion: 0 },
        { id: '2', name: 'Beta', projectKey: 'XYZ', boardVersion: 0 },
      ],
      selectedProjectId: '1',
      onProjectChange: vi.fn(),
      projectQuery: 'xyz',
      onProjectQueryChange,
      onCreateProject: vi.fn(),
      canWrite: true,
      canManageMembers: false,
      onManageMembers: vi.fn(),
    };

    const { rerender } = render(<Header {...props} />);
    expect(screen.getByRole('option', { name: 'XYZ · Beta' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'ABC · Alpha' })).toBeTruthy();
    fireEvent.change(screen.getByRole('searchbox', { name: 'プロジェクト検索' }), {
      target: { value: 'beta' },
    });
    expect(onProjectQueryChange).toHaveBeenCalledWith('beta');

    rerender(<Header {...props} projectQuery="alpha" />);
    expect(screen.queryByRole('option', { name: 'XYZ · Beta' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: '+ プロジェクト作成' }));
    expect(props.onCreateProject).toHaveBeenCalledOnce();
  });
});
