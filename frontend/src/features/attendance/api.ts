import { apiClient } from "../../api/client";
import type { AttendanceRecord, AttendanceSummary } from "../../types";

export async function checkIn(): Promise<AttendanceRecord> {
  const { data } = await apiClient.post<AttendanceRecord>("/attendance/check-in/");
  return data;
}

export async function checkOut(): Promise<AttendanceRecord> {
  const { data } = await apiClient.post<AttendanceRecord>("/attendance/check-out/");
  return data;
}

export async function fetchSummary(month: string, employeeId?: number): Promise<AttendanceSummary> {
  const { data } = await apiClient.get<AttendanceSummary>("/attendance/summary/", {
    params: employeeId ? { month, employee: employeeId } : { month },
  });
  return data;
}

export async function fetchAttendanceList(): Promise<AttendanceRecord[]> {
  const { data } = await apiClient.get<AttendanceRecord[]>("/attendance/");
  return data;
}
