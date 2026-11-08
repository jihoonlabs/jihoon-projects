/**
 * Laravel の AuthController::formatUser が返す利用者情報（createdAt のみ camelCase で返る）
 */
export interface User {
  id: number;
  email: string | null;
  name: string;
  role: 'user' | 'admin';
  status: 'active' | 'suspended';
  createdAt: string;
}

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
