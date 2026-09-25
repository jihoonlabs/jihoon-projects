export type TicketStatus = 
  | 'BACKLOG'      
  | 'TODO'         
  | 'IN_PROGRESS'  
  | 'IN_REVIEW'    
  | 'DONE';        

export type TicketPriority = 
  | 'HIGHEST' 
  | 'HIGH'    
  | 'MEDIUM' 
  | 'LOW'     
  | 'LOWEST'; 

export interface UserSummary {
  id: number;
  name: string;
  avatarUrl?: string;
}

export interface Ticket {
  id: string;
  issueKey: string; 
  title: string;
  description?: string;
  status: TicketStatus;
  priority: TicketPriority;
  assignee?: UserSummary;
  position: number;
  createdAt: string;
  updatedAt: string;
}

