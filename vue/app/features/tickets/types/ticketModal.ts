import type { Project } from './project';

/**
 * チケット作成モーダルで「作成先プロジェクト」を選ぶための情報
 */
export interface ProjectChoice {
  projects: Project[];
  /** 選択できない理由や確認中の表示（なければ null） */
  message: string | null;
  /** メンバー取得に失敗していて、再取得を促すか */
  canRetry: boolean;
}
