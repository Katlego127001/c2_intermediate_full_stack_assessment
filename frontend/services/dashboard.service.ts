import { api } from "@/lib/api";
import type { AdminDashboardData, EmployeeDashboardData } from "@/types/api";

export const dashboardService = {
  async admin(): Promise<AdminDashboardData> {
    const { data } = await api.get<AdminDashboardData>("/dashboard/admin");
    return data;
  },
  async employee(): Promise<EmployeeDashboardData> {
    const { data } = await api.get<EmployeeDashboardData>("/dashboard/employee");
    return data;
  },
};
