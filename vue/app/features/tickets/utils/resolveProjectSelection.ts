import type { Project } from '../types/project';
import { ALL_PROJECTS } from './filterTickets';

/**
 * 最初に選ぶプロジェクト。URL で指定され、一覧にあるものを優先する。
 * なければデモモードのときだけ先頭のプロジェクト、それ以外は全体表示にする。
 */
export function resolveInitialProjectId(
  projects: readonly Project[],
  requestedId: string | null,
  demoMode: boolean,
): string {
  if (requestedId && projects.some((project) => project.id === requestedId)) {
    return requestedId;
  }

  const [first] = projects;

  return demoMode && first ? first.id : ALL_PROJECTS;
}
