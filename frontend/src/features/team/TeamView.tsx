import { useEffect, useState } from "react";
import type { AttendanceSummary, LeaveRequest, UserBrief } from "../../types";
import { fetchSummary } from "../attendance/api";
import { fetchLeaveRequests } from "../leave/api";
import { fetchDirectReports } from "./api";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export default function TeamView() {
  const [reports, setReports] = useState<UserBrief[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [summaries, setSummaries] = useState<Record<number, AttendanceSummary>>({});
  const month = currentMonth();

  useEffect(() => {
    (async () => {
      const [reportsData, leaveData] = await Promise.all([fetchDirectReports(), fetchLeaveRequests()]);
      setReports(reportsData);
      setLeaveRequests(leaveData);

      const summaryEntries = await Promise.all(
        reportsData.map(async (r) => [r.id, await fetchSummary(month, r.id)] as const)
      );
      setSummaries(Object.fromEntries(summaryEntries));
    })();
  }, [month]);

  return (
    <div>
      <h2>My Team</h2>
      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>Employee</th>
            <th>Present ({month})</th>
            <th>Absent</th>
            <th>Half day</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.id}>
              <td>
                {r.first_name} {r.last_name} ({r.email})
              </td>
              <td>{summaries[r.id]?.present ?? "-"}</td>
              <td>{summaries[r.id]?.absent ?? "-"}</td>
              <td>{summaries[r.id]?.half_day ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Team Leave Requests</h3>
      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>Employee</th>
            <th>Start</th>
            <th>End</th>
            <th>Type</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {leaveRequests.map((req) => (
            <tr key={req.id}>
              <td>{req.employee.email}</td>
              <td>{req.start_date}</td>
              <td>{req.end_date}</td>
              <td>{req.leave_type}</td>
              <td>{req.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
