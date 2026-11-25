import { useEffect, useRef, useState } from 'react';

import { resendVerificationEmailApi } from '@/features/auth/api/resendVerificationEmail';

interface VerificationResendCallbacks {
  onStart: () => void;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export function useVerificationResend({
  onStart,
  onSuccess,
  onError,
}: VerificationResendCallbacks) {
  const [isResending, setIsResending] = useState(false);
  const activeRequest = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      const request = activeRequest.current;
      activeRequest.current = null;
      request?.abort();
    };
  }, []);

  const cancelResend = () => {
    // 古い再送応答のSet-Cookieで新しいログインを取り消さない。
    const request = activeRequest.current;
    activeRequest.current = null;
    request?.abort();
    setIsResending(false);
  };

  const resend = async (email: string) => {
    cancelResend();
    const request = new AbortController();
    activeRequest.current = request;
    onStart();
    setIsResending(true);

    try {
      const { message } = await resendVerificationEmailApi(
        { email },
        request.signal,
      );
      if (activeRequest.current === request) onSuccess(message);
    } catch (error) {
      if (activeRequest.current === request) {
        onError(
          error instanceof Error
            ? error.message
            : '認証メールの再送中にエラーが発生しました。',
        );
      }
    } finally {
      if (activeRequest.current === request) {
        activeRequest.current = null;
        setIsResending(false);
      }
    }
  };

  return { isResending, cancelResend, resend };
}
