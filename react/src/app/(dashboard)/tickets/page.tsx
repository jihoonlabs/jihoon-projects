'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { useTicketStore } from '@/store/useTicketStore';
import TicketCard from './_components/TicketCard';
import styles from './page.module.scss';

export default function TicketsPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const tickets = useTicketStore((state) => state.tickets);

  const handleLogout = () => {
    logout();
    alert('ログアウトしました。');
    router.push('/login');
  };

  const todoTickets = tickets.filter((t) => t.status === 'TODO');
  const inProgressTickets = tickets.filter((t) => t.status === 'IN_PROGRESS');
  const doneTickets = tickets.filter((t) => t.status === 'DONE');

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>タスク管理ボード (Task Board)</h1>
        <div className={styles.userInfo}>
          <span>ようこそ、<strong>{user?.name || 'P.jh'}</strong> さん</span>
          <button onClick={handleLogout} className={styles.logoutBtn}>
            ログアウト
          </button>
        </div>
      </header>

      <main className={styles.board}>
        {/* 未対応 (TODO) */}
        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>未対応 (TODO)</span>
            <span className={styles.count}>{todoTickets.length}</span>
          </div>
          {todoTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>

        {/* 進行中 (IN_PROGRESS) */}
        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>進行中 (IN PROGRESS)</span>
            <span className={styles.count}>{inProgressTickets.length}</span>
          </div>
          {inProgressTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>

        {/* 完了 (DONE) */}
        <section className={styles.column}>
          <div className={styles.columnTitle}>
            <span>完了 (DONE)</span>
            <span className={styles.count}>{doneTickets.length}</span>
          </div>
          {doneTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </section>
      </main>
    </div>
  );
}