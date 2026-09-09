export interface Company {
  id: number;
  name: string;
  code: string;
  createdAt: string;
}

export interface Department {
  id: number;
  companyId: number;
  name: string;
}

export interface User {
  id: number;
  email: string;
  name: string;         
  companyId: number;    
  companyName: string;     
  role: 'admin' | 'member' | 'guest'; 
  status: 'active' | 'suspended' | 'invited'; 
  createdAt: string;
}

export interface UserProfile {
  id: number;
  userId: number;           
  departmentId?: number;   
  departmentName?: string; 
  position?: string;       
  employeeNumber?: string;  
  phone?: string;           
  avatarUrl?: string;    
  bio?: string;             
}

export interface UserSummary {
  id: number;
  name: string;
  email: string;
  avatarUrl?: string;
  departmentName?: string;
}