import { apiClient } from "../../api/client";
import type { LeaveRequest, LeaveType } from "../../types";

export async function fetchLeaveRequests(): Promise<LeaveRequest[]> {
  const { data } = await apiClient.get<LeaveRequest[]>("/leave-requests/");
  return data;
}

export async function createLeaveRequest(payload: {
  start_date: string;
  end_date: string;
  leave_type: LeaveType;
  reason?: string;
}): Promise<LeaveRequest> {
  const { data } = await apiClient.post<LeaveRequest>("/leave-requests/", payload);
  return data;
}

export async function cancelLeaveRequest(id: number): Promise<void> {
  await apiClient.post(`/leave-requests/${id}/cancel/`);
}

export async function approveLeaveRequest(id: number): Promise<LeaveRequest> {
  const { data } = await apiClient.post<LeaveRequest>(`/leave-requests/${id}/approve/`);
  return data;
}

export async function rejectLeaveRequest(id: number): Promise<LeaveRequest> {
  const { data } = await apiClient.post<LeaveRequest>(`/leave-requests/${id}/reject/`);
  return data;
}
