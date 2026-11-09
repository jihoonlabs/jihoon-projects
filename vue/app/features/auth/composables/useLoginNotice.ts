import { onMounted } from 'vue';

import { useRoute, useRouter } from '#imports';

import type { LoginNotice, LoginNoticeMessages } from '../types/auth';
import { LOGIN_PATH } from '../utils/navigation';

const providerLabel = (provider?: string) => {
  if (provider === 'google') return 'Google';
  if (provider === 'line') return 'LINE';

  return null;
};

/**
 * 遷移元（ソーシャルログイン・メール認証・会員登録）から渡された結果を、ログイン画面の表示文言にする
 */
export function loginNoticeMessages(notice: LoginNotice): LoginNoticeMessages {
  let error = '';
  let success = '';

  if (notice.error === 'social_login_failed') {
    const label = providerLabel(notice.provider);
    error = label
      ? `${label}認証に失敗しました。`
      : 'ソーシャルログインに失敗しました。';
  } else if (notice.error === 'account_unavailable') {
    error = 'このアカウントは現在利用できません。';
  }

  if (notice.verified === '1') {
    success = 'メールアドレスの認証が完了しました。ログインしてください。';
  } else if (notice.registered === '1') {
    success = '認証メールを送信しました。メールをご確認ください。';
  }

  return { error, success };
}

/**
 * ログイン画面を開いた時点のクエリから通知を読み取り、表示後はアドレスバーから消す。
 * 再読み込みで同じ通知を出さないため。
 */
export function useLoginNotice(): LoginNoticeMessages {
  const route = useRoute();
  const router = useRouter();

  const queryValue = (key: string) => {
    const value = route.query[key];

    return typeof value === 'string' ? value : undefined;
  };

  const messages = loginNoticeMessages({
    error: queryValue('error'),
    provider: queryValue('provider'),
    verified: queryValue('verified'),
    registered: queryValue('registered'),
  });

  onMounted(() => {
    if (Object.keys(route.query).length > 0) {
      void router.replace({ path: LOGIN_PATH });
    }
  });

  return messages;
}
