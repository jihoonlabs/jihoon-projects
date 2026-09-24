'use client';

import styles from './index.module.css';

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  assigneeFilter: string;
  onAssigneeChange: (value: string) => void;
}

export default function Header({
  searchQuery,
  onSearchChange,
  assigneeFilter,
  onAssigneeChange,
}: HeaderProps) {
  return (
    <header className={styles.container}>
      <div className={styles.leftSection}>
        <h1 className={styles.title}>チケットボード</h1>

        <div className={styles.filterGroup}>
          <input
            type="text"
            placeholder="チケットを検索..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          <select
            className={styles.selectFilter}
            value={assigneeFilter}
            onChange={(e) => onAssigneeChange(e.target.value)}
          >
            <option value="ALL">すべての担当者</option>
            <option value="ME">自分に割り当て (朴)</option>
            <option value="UNASSIGNED">未割り当て</option>
          </select>
        </div>
      </div>

      <div className={styles.rightSection}>
        <button type="button" className={styles.createBtn}>
          + チケット作成
        </button>
      </div>
    </header>
  );
}