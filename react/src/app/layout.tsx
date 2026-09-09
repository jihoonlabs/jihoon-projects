import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';

import { AuthInitializer } from '@/features/auth/AuthInitializer';

import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'タスク管理',
  description: 'チケット管理アプリケーション',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <AuthInitializer />
        {children}
      </body>
    </html>
  );
}