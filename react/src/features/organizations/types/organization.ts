export interface Organization {
  id: number;
  name: string;
  code: string;
  createdAt: string;
}

export interface Department {
  id: number;
  organizationId: number;
  name: string;
}

export type OrganizationRole = 'admin' | 'member' | 'guest';

export interface OrganizationMembership {
  id: number;
  organizationId: number;
  userId: number;
  role: OrganizationRole;
  departmentId?: number;
  position?: string;
  employeeNumber?: string;
  joinedAt: string;
}
