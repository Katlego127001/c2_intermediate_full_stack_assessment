import { api } from "@/lib/api";
import type { Job, JobPriority, JobStatus, Page } from "@/types/api";

export interface JobListParams {
  q?: string;
  status?: JobStatus;
  priority?: JobPriority;
  mine?: boolean;
  assignee_id?: string;
  page?: number;
  size?: number;
}

export interface JobCreatePayload {
  title: string;
  description?: string;
  priority?: JobPriority;
  due_date?: string | null;
  assigned_employee_id?: string | null;
  status?: JobStatus;
}

export interface JobUpdatePayload {
  title?: string;
  description?: string;
  priority?: JobPriority;
  status?: JobStatus;
  due_date?: string | null;
  assigned_employee_id?: string | null;
}

export const jobsService = {
  async list(params: JobListParams = {}): Promise<Page<Job>> {
    const { data } = await api.get<Page<Job>>("/jobs", { params });
    return data;
  },
  async get(id: string): Promise<Job> {
    const { data } = await api.get<Job>(`/jobs/${id}`);
    return data;
  },
  async create(payload: JobCreatePayload): Promise<Job> {
    const { data } = await api.post<Job>("/jobs", payload);
    return data;
  },
  async update(id: string, payload: JobUpdatePayload): Promise<Job> {
    const { data } = await api.put<Job>(`/jobs/${id}`, payload);
    return data;
  },
  async setStatus(id: string, status: JobStatus, comment?: string | null): Promise<Job> {
    const { data } = await api.patch<Job>(`/jobs/${id}/status`, { status, comment });
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/jobs/${id}`);
  },
};
