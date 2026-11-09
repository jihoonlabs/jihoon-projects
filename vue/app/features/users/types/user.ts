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
