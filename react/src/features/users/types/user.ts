export interface User {
  id: number;
  email: string;
  name: string;
  status: 'active' | 'suspended';
  createdAt: string;
}

export interface UserProfile {
  id: number;
  userId: number;
  phone?: string;
  avatarUrl?: string;
  bio?: string;
}

export interface UserSummary {
  id: number;
  name: string;
  email: string;
  avatarUrl?: string;
}
