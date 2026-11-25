import { useState } from 'react';

import { LoginApiError, loginApi } from '@/features/auth/api/login';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { LoginValidationErrors } from '@/features/auth/types/auth';
import { validateLoginForm } from '@/features/auth/validation/auth';

interface LoginSubmitCallbacks {
  onStart: () => void;
  onError: (message: string, requiresVerification: boolean) => void;
}

export function useLoginSubmit({ onStart, onError }: LoginSubmitCallbacks) {
  const login = useAuthStore((state) => state.login);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<LoginValidationErrors>({});

  const clearError = (field: keyof LoginValidationErrors) => {
    setErrors((current) =>
      current[field] ? { ...current, [field]: undefined } : current,
    );
  };

  const resetErrors = () => setErrors({});

  const submit = async (email: string, password: string) => {
    onStart();
    const validationErrors = validateLoginForm(email, password);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    resetErrors();
    setLoading(true);

    try {
      const { user } = await loginApi({ email, password });
      login(user);
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : 'ログイン中にエラーが発生しました。',
        error instanceof LoginApiError && error.code === 'email_not_verified',
      );
    } finally {
      setLoading(false);
    }
  };

  return { loading, errors, clearError, resetErrors, submit };
}
