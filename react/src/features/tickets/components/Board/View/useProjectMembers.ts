import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { fetchProjectMembers } from '@/features/tickets/api/projectApi';
import type { ProjectMember } from '@/features/tickets/types/project';

type MemberScope = {
  projectId: string;
  sessionRevision: number;
  sessionExpired: boolean;
};

type MemberState = {
  scope: MemberScope;
  members: ProjectMember[];
  error: string | null;
};

export function useProjectMembers(
  projectId: string,
  sessionRevision: number,
  sessionExpired: boolean,
) {
  const [state, setState] = useState<MemberState | null>(null);
  const [attempt, setAttempt] = useState(0);
  const requestRevision = useRef(0);
  const scope = useMemo(
    () => ({ projectId, sessionRevision, sessionExpired }),
    [projectId, sessionRevision, sessionExpired],
  );
  const currentScope = useRef<MemberScope | null>(null);

  // 前の画面から遅れて届く結果を、同じプロジェクトに戻った場合も破棄する。
  useLayoutEffect(() => {
    currentScope.current = scope;
    return () => {
      currentScope.current = null;
    };
  }, [scope]);

  useEffect(() => {
    if (scope.sessionExpired || !scope.projectId || scope.projectId === 'ALL')
      return;
    const revision = ++requestRevision.current;
    let active = true;
    const isCurrentRequest = () =>
      active &&
      revision === requestRevision.current &&
      currentScope.current === scope;
    fetchProjectMembers(scope.projectId)
      .then((members) => {
        if (isCurrentRequest()) {
          setState({ scope, members, error: null });
        }
      })
      .catch((reason) => {
        if (isCurrentRequest()) {
          setState({
            scope,
            members: [],
            error:
              reason instanceof Error
                ? reason.message
                : 'メンバーを取得できませんでした。',
          });
        }
      });
    return () => {
      active = false;
    };
  }, [scope, attempt]);

  const retryMembers = () => {
    if (currentScope.current !== scope || scope.sessionExpired) return;
    requestRevision.current += 1;
    setState(null);
    setAttempt((value) => value + 1);
  };

  const acceptMembers = (
    changedProjectId: string,
    members: ProjectMember[],
  ) => {
    if (
      currentScope.current !== scope ||
      scope.projectId !== changedProjectId ||
      scope.sessionExpired
    )
      return;
    requestRevision.current += 1;
    setState({ scope, members, error: null });
  };

  const current = state?.scope === scope ? state : null;
  return {
    projectMembers: current?.members ?? [],
    membersProjectId: current && !current.error ? projectId : '',
    memberError: current?.error ? { projectId, message: current.error } : null,
    retryMembers,
    acceptMembers,
  };
}
