export type Role = "employee" | "manager";

export interface UserBrief {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export interface User extends UserBrief {
  manager: UserBrief | null;
  is_active: boolean;
  date_joined: string;
}

export type LeaveType = "vacation" | "sick" | "personal" | "other";
export type LeaveStatus = "pending" | "approved" | "rejected";

export interface LeaveRequest {
  id: number;
  employee: UserBrief;
  start_date: string;
  end_date: string;
  leave_type: LeaveType;
  status: LeaveStatus;
  reason: string;
  approved_by: UserBrief | null;
  decided_at: string | null;
  created_at: string;
}

export type AttendanceStatus = "present" | "absent" | "half_day";

export interface AttendanceRecord {
  id: number;
  employee: UserBrief;
  date: string;
  check_in_time: string | null;
  check_out_time: string | null;
  status: AttendanceStatus;
}

export interface AttendanceSummary {
  employee_id: number;
  month: string;
  present: number;
  absent: number;
  half_day: number;
}
