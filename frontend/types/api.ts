export type UserRole = "admin" | "employee";
export type EmploymentStatus = "active" | "inactive";
export type JobStatus = "pending" | "in_progress" | "completed";
export type JobPriority = "low" | "medium" | "high" | "critical";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface CurrentUser {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  employee_id?: string | null;
  full_name?: string | null;
}

export interface Employee {
  id: string;
  user_id: string;
  email: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string | null;
  department?: string | null;
  employment_status: EmploymentStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AssigneeSummary {
  id: string;
  full_name: string;
  department?: string | null;
}

export interface Job {
  id: string;
  title: string;
  description?: string | null;
  priority: JobPriority;
  status: JobStatus;
  due_date?: string | null;
  assigned_employee_id?: string | null;
  assignee?: AssigneeSummary | null;
  last_status_comment?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AdminDashboardData {
  jobs: { total: number; pending: number; in_progress: number; completed: number };
  employees: { total: number; active: number; inactive: number };
  workload: Array<{
    employee_id: string;
    full_name: string;
    department?: string | null;
    pending: number;
    in_progress: number;
    completed: number;
    total: number;
  }>;
  recent_activity: Array<{
    id: string;
    actor_email?: string | null;
    action: string;
    entity_type: string;
    entity_id?: string | null;
    created_at: string;
  }>;
}

export interface EmployeeDashboardData {
  profile: { id: string; full_name: string; department?: string | null; email: string };
  jobs: { total: number; pending: number; in_progress: number; completed: number };
  upcoming: Array<{
    id: string;
    title: string;
    due_date?: string | null;
    priority: JobPriority;
    status: JobStatus;
  }>;
  alerts?: Array<{
    id: string;
    title: string;
    message?: string | null;
    job_id?: string | null;
    priority: JobPriority;
    status: JobStatus;
  }>;
}
