import { onBeforeUnmount, ref, type Ref } from 'vue';

import { useApiClient } from '~/shared/api/apiClient';

import { AccountError } from '../api/accountRequest';
import { resendVerificationEmail } from '../api/resendVerificationEmail';
import type { FormMessages } from '../types/auth';

/**
 * メール未認証のときの認証メール再送。
 * 入力の変更や新しいログインで取り消し、古い再送結果を表示に反映しない。
 */
export function useVerificationResend(
  email: Ref<string>,
  messages: FormMessages,
) {
  const client = useApiClient();
  const required = ref(false);
  const resending = ref(false);
  let controller: AbortController | null = null;
  // 取り消すたびに進め、遅れて届いた結果を捨てる
  let revision = 0;

  const cancel = () => {
    controller?.abort();
    controller = null;
    resending.value = false;
    revision += 1;
  };

  /** 進行中の再送を取り消し、再送の案内も閉じる */
  const reset = () => {
    cancel();
    required.value = false;
  };

  const resend = async () => {
    cancel();
    const current = new AbortController();
    const currentRevision = revision;
    controller = current;
    messages.clear();
    resending.value = true;

    try {
      const response = await resendVerificationEmail(
        client,
        email.value,
        current.signal,
      );

      if (currentRevision !== revision) return;
      messages.success.value = response.message;
      required.value = false;
    } catch (error) {
      if (currentRevision !== revision) return;
      messages.error.value =
        error instanceof AccountError
          ? error.message
          : '認証メールの再送中にエラーが発生しました。';
    } finally {
      if (controller === current) {
        controller = null;
        resending.value = false;
      }
    }
  };

  onBeforeUnmount(() => controller?.abort());

  return { required, resending, resend, reset };
}
