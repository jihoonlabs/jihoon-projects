// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ProjectCreateDialog from './index';

const createProject = vi.hoisted(() => vi.fn());
vi.mock('@/features/tickets/api/projectApi', () => ({ createProject }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('ProjectCreateDialog', () => {
  it('creates a project and reports its generated key', async () => {
    const project = { id: '5', name: 'Alpha', projectKey: 'ABC', boardVersion: 0 };
    createProject.mockResolvedValue(project);
    const onCreated = vi.fn();

    render(<ProjectCreateDialog onClose={vi.fn()} onCreated={onCreated} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'プロジェクト名' }), {
      target: { value: ' Alpha ' },
    });
    fireEvent.click(screen.getByRole('button', { name: '作成する' }));

    await waitFor(() => expect(createProject).toHaveBeenCalledWith('Alpha'));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(project));
  });

  it('keeps the dialog open and shows an error on failure', async () => {
    createProject.mockRejectedValue(new Error('サーバーエラー'));
    const onCreated = vi.fn();
    render(<ProjectCreateDialog onClose={vi.fn()} onCreated={onCreated} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'プロジェクト名' }), {
      target: { value: 'Beta' },
    });
    fireEvent.click(screen.getByRole('button', { name: '作成する' }));

    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'サーバーエラー');
    expect(onCreated).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });
});
