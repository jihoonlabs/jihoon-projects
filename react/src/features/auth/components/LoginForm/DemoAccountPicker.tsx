import styles from './LoginForm.module.css';

export const DEMO_ACCOUNTS = {
  user: { email: 'demo@example.com', password: 'TicketDemo2026!' },
  admin: { email: 'demo-admin@example.com', password: 'TicketAdmin2026!' },
};

interface DemoAccountPickerProps {
  email: string;
  disabled: boolean;
  onSelect: (account: keyof typeof DEMO_ACCOUNTS) => void;
}

export function DemoAccountPicker({
  email,
  disabled,
  onSelect,
}: DemoAccountPickerProps) {
  return (
    <div
      className={styles.demoAccountChoices}
      role="group"
      aria-label="デモ用アカウント"
    >
      <button
        type="button"
        className={styles.demoAccountButton}
        aria-pressed={email === DEMO_ACCOUNTS.user.email}
        disabled={disabled}
        onClick={() => onSelect('user')}
      >
        一般ユーザー
        <span>1プロジェクト</span>
      </button>
      <button
        type="button"
        className={styles.demoAccountButton}
        aria-pressed={email === DEMO_ACCOUNTS.admin.email}
        disabled={disabled}
        onClick={() => onSelect('admin')}
      >
        管理者
        <span>2プロジェクト</span>
      </button>
    </div>
  );
}
