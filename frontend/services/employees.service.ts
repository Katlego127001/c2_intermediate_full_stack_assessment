import { api } from "@/lib/api";
import type { Employee, EmploymentStatus, Page, UserRole } from "@/types/api";

export interface EmployeeListParams {
  q?: string;
  department?: string;
  status?: EmploymentStatus;
  role?: UserRole;
  page?: number;
  size?: number;
}

export interface EmployeeCreatePayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  department?: string;
  role?: UserRole;
  employment_status?: EmploymentStatus;
}

export interface EmployeeUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone_number?: string | null;
  department?: string | null;
  employment_status?: EmploymentStatus;
  role?: UserRole;
}

export const employeesService = {
  async list(params: EmployeeListParams = {}): Promise<Page<Employee>> {
    const { data } = await api.get<Page<Employee>>("/employees", { params });
    return data;
  },
  async get(id: string): Promise<Employee> {
    const { data } = await api.get<Employee>(`/employees/${id}`);
    return data;
  },
  async me(): Promise<Employee> {
    const { data } = await api.get<Employee>("/employees/me");
    return data;
  },
  async updateMe(phone_number: string | null): Promise<Employee> {
    const { data } = await api.patch<Employee>("/employees/me", { phone_number });
    return data;
  },
  async create(payload: EmployeeCreatePayload): Promise<Employee> {
    const { data } = await api.post<Employee>("/employees", payload);
    return data;
  },
  async update(id: string, payload: EmployeeUpdatePayload): Promise<Employee> {
    const { data } = await api.put<Employee>(`/employees/${id}`, payload);
    return data;
  },
  async setStatus(id: string, employment_status: EmploymentStatus): Promise<Employee> {
    const { data } = await api.patch<Employee>(`/employees/${id}/status`, { employment_status });
    return data;
  },
};
