import { User } from './user';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  companyCode: string; 
}

export interface AuthResponse {
  user: User;       
  accessToken: string; 
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
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
