'use client';

import { useEffect, useLayoutEffect, useRef, type ReactNode } from 'react';
import styles from './index.module.css';

interface Props {
  children: ReactNode;
  busy: boolean;
  focusCreate: boolean;
  onClose: () => void;
}

export default function ProjectDirectoryDialog({
  children,
  busy,
  focusCreate,
  onClose,
}: Props) {
  const dialog = useRef<HTMLDialogElement>(null);

  useLayoutEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    element?.showModal();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      element?.close();
      document.body.style.overflow = previousOverflow;
      if (trigger?.isConnected) trigger.focus();
    };
  }, []);

  useEffect(() => {
    if (focusCreate)
      dialog.current
        ?.querySelector<HTMLInputElement>('input[maxlength="255"]')
        ?.focus();
    else
      dialog.current
        ?.querySelector<HTMLInputElement>('input[type="search"]')
        ?.focus();
  }, [focusCreate]);

  return (
    <dialog
      ref={dialog}
      id="project-directory-dialog"
      className={styles.dialog}
      aria-labelledby="project-directory-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className={styles.dialogToolbar}>
        <button
          type="button"
          disabled={busy}
          onClick={onClose}
          aria-label="プロジェクト一覧を閉じる"
        >
          閉じる
        </button>
      </div>
      {children}
    </dialog>
  );
}
