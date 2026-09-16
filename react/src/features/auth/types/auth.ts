import type { User } from '@/features/users/types/user';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  passwordConfirmation: string;
}

export interface LoginResponse {
  message: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user: User;
}

export interface VerificationEmailResendRequest {
  email: string;
}

export interface VerificationEmailResendResponse {
  message: string;
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
  name?: string;
  email?: string;
  password?: string;
  passwordConfirmation?: string;
}

export interface LoginRedirectParams {
  error?: string;
  provider?: string;
  verified?: string;
  registered?: string;
}

export interface PasswordResetLinkRequest {
  email: string;
}

export interface PasswordResetLinkResponse {
  message: string;
}

export interface PasswordResetRequest {
  email: string;
  token: string;
  password: string;
  passwordConfirmation: string;
}

export interface PasswordResetResponse {
  message: string;
}

export interface PasswordResetLinkValidationErrors {
  email?: string;
}

export interface PasswordResetValidationErrors {
  password?: string;
  passwordConfirmation?: string;
}