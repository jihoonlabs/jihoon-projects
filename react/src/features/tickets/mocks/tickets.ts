import { Ticket, TicketStatus } from '../types/ticket';

export interface ColumnConfig {
  id: TicketStatus;
  label: string;
  order: number;
}

// 5段階のカンバンカラム設定
export const INITIAL_COLUMNS: ColumnConfig[] = [
  { id: 'BACKLOG', label: 'バックログ', order: 1 },
  { id: 'TODO', label: '未対応', order: 2 },
  { id: 'IN_PROGRESS', label: '進行中', order: 3 },
  { id: 'IN_REVIEW', label: 'レビュー中', order: 4 },
  { id: 'DONE', label: '完了', order: 5 },
];

// テスト用モックデータ (日本語表記)
export const MOCK_TICKETS: Ticket[] = [
  {
    id: '1',
    issueKey: 'KAN-101',
    title: '認証セッションクッキーの処理改善',
    description: 'CSRFトークンの未反映問題の解決およびテスト作成',
    status: 'DONE',
    priority: 'HIGHEST',
    assignee: { id: 1, name: '朴 (Park)' },
    position: 1000,
    createdAt: '2026-09-23T10:00:00Z',
    updatedAt: '2026-09-23T12:00:00Z',
  },
  {
    id: '2',
    issueKey: 'KAN-102',
    title: 'JiraスタイルのカンバンボードUIレイアウト実装',
    description: '5段階のカラムおよびカードコンポーネントのマークアップ',
    status: 'IN_PROGRESS',
    priority: 'HIGH',
    assignee: { id: 1, name: '朴 (Park)' },
    position: 1000,
    createdAt: '2026-09-24T09:00:00Z',
    updatedAt: '2026-09-24T09:00:00Z',
  },
  {
    id: '3',
    issueKey: 'KAN-103',
    title: 'ドラッグ＆ドロップライブラリの検討と連携',
    description: '@hello-pangea/dnd導入の検討',
    status: 'TODO',
    priority: 'MEDIUM',
    position: 1000,
    createdAt: '2026-09-24T09:10:00Z',
    updatedAt: '2026-09-24T09:10:00Z',
  },
  {
    id: '4',
    issueKey: 'KAN-104',
    title: 'チケット詳細モーダルコンポーネントの設計',
    description: '担当者、優先度、説明の編集機能を含む',
    status: 'BACKLOG',
    priority: 'LOW',
    position: 1000,
    createdAt: '2026-09-24T09:20:00Z',
    updatedAt: '2026-09-24T09:20:00Z',
  },
  {
    id: '5',
    issueKey: 'KAN-105',
    title: 'コードレビューとリファクタリング',
    description: 'Boardコンポーネントのディレクトリ構造の最適化',
    status: 'IN_REVIEW',
    priority: 'HIGH',
    assignee: { id: 2, name: '田中 (Tanaka)' },
    position: 1000,
    createdAt: '2026-09-24T09:30:00Z',
    updatedAt: '2026-09-24T09:30:00Z',
  },
];