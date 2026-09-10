import type { User } from '@/features/users/types/user';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  companyCode?: string;
}

export interface AuthResponse {
  user: User;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  login: (user: User) => void;
  logout: () => void;
  initialize: () => void;
}

export interface LoginValidationErrors {
  email?: string;
  password?: string;
}

export interface RegisterValidationErrors {
  email?: string;
  password?: string;
  name?: string;
  companyCode?: string;
}