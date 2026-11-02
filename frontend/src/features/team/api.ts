import { apiClient } from "../../api/client";
import type { UserBrief } from "../../types";

export async function fetchDirectReports(): Promise<UserBrief[]> {
  const { data } = await apiClient.get<UserBrief[]>("/direct-reports/");
  return data;
}
