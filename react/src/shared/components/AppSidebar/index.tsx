'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Clock3, Ticket } from 'lucide-react';

import styles from './AppSidebar.module.css';

const items = [
  { href: '/tickets', label: 'チケット', Icon: Ticket },
  { href: '/attendance', label: '出退勤', Icon: Clock3 },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.identity}>
        <span className={styles.mark} aria-hidden="true">
          J
        </span>
        <div>
          <strong>JIHOON</strong>
          <span>WORKSPACE</span>
        </div>
      </div>

      <nav aria-label="アプリメニュー" className={styles.navigation}>
        <p className={styles.sectionLabel}>メニュー</p>
        {items.map(({ href, label, Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={`${styles.link} ${active ? styles.active : ''}`}
              aria-current={active ? 'page' : undefined}
            >
              <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <p className={styles.footer}>日々の仕事を、ひとつの場所に。</p>
    </aside>
  );
}
