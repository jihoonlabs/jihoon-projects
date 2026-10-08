export type ProjectRole = 'leader' | 'member';
export type ProjectPermission = 'read' | 'write';

export interface Project {
  id: string;
  name: string;
  projectKey: string | null;
  boardVersion: number;
}

export interface ProjectMember {
  id: string;
  name: string;
  email: string | null;
  role: ProjectRole;
  permission: ProjectPermission;
}
