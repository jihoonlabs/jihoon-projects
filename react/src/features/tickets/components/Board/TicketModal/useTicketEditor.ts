import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { fetchTicket, TicketApiError } from '@/features/tickets/api/ticketApi';
import type {
  CreateTicketInput,
  Ticket,
  TicketPriority,
  TicketStatus,
  UpdateTicketInput,
} from '@/features/tickets/types/ticket';
import { detailError } from './detailError';

interface UseTicketEditorOptions {
  initialTicket: Ticket | null;
  projectId: string;
  readOnly: boolean;
  onCreate: (input: CreateTicketInput) => Promise<void>;
  onUpdate: (id: string, input: UpdateTicketInput) => Promise<Ticket>;
  onSaveStart: () => void;
  onCreated: () => void;
  onUpdated: () => void;
}

export default function useTicketEditor({
  initialTicket,
  projectId,
  readOnly,
  onCreate,
  onUpdate,
  onSaveStart,
  onCreated,
  onUpdated,
}: UseTicketEditorOptions) {
  const [ticket, setTicket] = useState(initialTicket);
  const initialValues = {
    title: ticket?.title ?? '',
    description: ticket?.description ?? '',
    status: ticket?.status ?? ('TODO' as TicketStatus),
    priority: ticket?.priority ?? ('MEDIUM' as TicketPriority),
    assigneeId: ticket?.assignee?.id ?? '',
  };
  const savedValues = useRef(initialValues);
  const version = useRef(ticket?.version);
  const [title, setTitle] = useState(initialValues.title);
  const [description, setDescription] = useState(initialValues.description);
  const [status, setStatus] = useState<TicketStatus>(initialValues.status);
  const [priority, setPriority] = useState<TicketPriority>(
    initialValues.priority,
  );
  const [assigneeId, setAssigneeId] = useState(initialValues.assigneeId);
  const [submitting, setSubmitting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [latest, setLatest] = useState<Ticket | null>(null);
  const [reloadError, setReloadError] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const restoreSavedValues = () => {
    setTitle(savedValues.current.title);
    setDescription(savedValues.current.description);
    setStatus(savedValues.current.status);
    setPriority(savedValues.current.priority);
    setAssigneeId(savedValues.current.assigneeId);
  };

  const loadLatest = async () => {
    if (!ticket || reloading) return;
    setReloading(true);
    setReloadError(null);
    try {
      const incoming = await fetchTicket(ticket.id);
      if (alive.current) setLatest(incoming);
    } catch (reason) {
      if (alive.current) {
        setReloadError(detailError(reason));
        if (
          reason instanceof TicketApiError &&
          [401, 403, 404].includes(reason.status)
        )
          setUnavailable(true);
      }
    } finally {
      if (alive.current) setReloading(false);
    }
  };

  const useLatest = () => {
    if (!latest) return;
    // 再取得だけでは入力・保存基準を変更しない。明示操作で編集をやり直す。
    savedValues.current = {
      title: latest.title,
      description: latest.description ?? '',
      status: latest.status,
      priority: latest.priority,
      assigneeId: latest.assignee?.id ?? '',
    };
    version.current = latest.version;
    setTicket(latest);
    restoreSavedValues();
    setLatest(null);
    setConflict(false);
    setSaveError(null);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (readOnly || unavailable || conflict || !title.trim() || submitting)
      return;
    setSubmitting(true);
    setSaveError(null);
    onSaveStart();
    const fields: UpdateTicketInput = {
      ...(ticket ? { expectedVersion: version.current } : {}),
      title: title.trim(),
      description: description.trim() || null,
      status,
      priority,
      // 同じ詳細画面で再編集する場合も、直前の成功した保存値と比較する。
      ...(ticket && assigneeId === savedValues.current.assigneeId
        ? {}
        : { assigneeId: assigneeId || null }),
    };
    try {
      if (ticket) {
        const updated = await onUpdate(ticket.id, fields);
        if (!alive.current) return;
        version.current = updated.version;
        // 応答のフィールドとバージョンを同じスナップショットとして採用する。
        savedValues.current = {
          title: updated.title,
          description: updated.description ?? '',
          status: updated.status,
          priority: updated.priority,
          assigneeId: updated.assignee?.id ?? '',
        };
        setTicket(updated);
        restoreSavedValues();
        onUpdated();
      } else {
        await onCreate({
          projectId,
          title: title.trim(),
          description: description.trim() || null,
          status,
          priority,
          assigneeId: assigneeId || null,
        });
        onCreated();
      }
    } catch (error) {
      if (!alive.current) return;
      if (error instanceof TicketApiError && error.code === 'ticket_conflict') {
        setConflict(true);
        setSaveError(
          '他のユーザーが変更したため保存できませんでした。入力内容は保持されています。',
        );
      } else {
        if (
          error instanceof TicketApiError &&
          [403, 404].includes(error.status)
        )
          setUnavailable(true);
        setSaveError(
          error instanceof TicketApiError &&
            [401, 403, 404].includes(error.status)
            ? detailError(error)
            : error instanceof Error
              ? error.message
              : '保存に失敗しました。',
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return {
    ticket,
    title,
    setTitle,
    description,
    setDescription,
    status,
    setStatus,
    priority,
    setPriority,
    assigneeId,
    setAssigneeId,
    submitting,
    saveError,
    clearSaveError: () => setSaveError(null),
    resetAssigneeForProjectChange: () => {
      setAssigneeId('');
      setSaveError(null);
    },
    conflict,
    latest,
    reloadError,
    reloading,
    unavailable,
    restoreSavedValues,
    loadLatest,
    useLatest,
    submit,
  };
}
