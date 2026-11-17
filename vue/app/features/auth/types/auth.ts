import type { Ref } from 'vue';

import type { User } from '~/features/users/types/user';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  user: User;
}

export type SocialProvider = 'google' | 'line';

/**
 * ログイン画面へ戻るときに Laravel が付けるクエリ（処理結果の表示に使う）
 */
export interface LoginNotice {
  error?: string;
  provider?: string;
  verified?: string;
  registered?: string;
}

/** 通知クエリから決めた、ログイン画面に最初に出す文言（なければ空文字） */
export interface LoginNoticeMessages {
  error: string;
  success: string;
}

/** フォームの結果表示。再送など別の処理からも同じ表示欄を更新する */
export interface FormMessages {
  error: Ref<string>;
  success: Ref<string>;
  clear: () => void;
}

export interface MessageResponse {
  message: string;
}

export interface Registration {
  name: string;
  email: string;
  password: string;
  passwordConfirmation: string;
}

export interface PasswordReset {
  email: string;
  token: string;
  password: string;
  passwordConfirmation: string;
}
