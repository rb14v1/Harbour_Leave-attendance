import { useEffect, useState } from "react";
import type { LeaveRequest } from "../../types";
import { approveLeaveRequest, fetchLeaveRequests, rejectLeaveRequest } from "./api";

export default function Approvals() {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const data = await fetchLeaveRequests();
    setRequests(data.filter((r) => r.status === "pending"));
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleApprove = async (id: number) => {
    await approveLeaveRequest(id);
    await load();
  };

  const handleReject = async (id: number) => {
    await rejectLeaveRequest(id);
    await load();
  };

  return (
    <div>
      <h2>Pending Approvals</h2>
      {loading && <p>Loading...</p>}
      {!loading && requests.length === 0 && <p>No pending requests from your direct reports.</p>}
      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>Employee</th>
            <th>Start</th>
            <th>End</th>
            <th>Type</th>
            <th>Reason</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {requests.map((req) => (
            <tr key={req.id}>
              <td>{req.employee.email}</td>
              <td>{req.start_date}</td>
              <td>{req.end_date}</td>
              <td>{req.leave_type}</td>
              <td>{req.reason}</td>
              <td>
                <button onClick={() => handleApprove(req.id)}>Approve</button>{" "}
                <button onClick={() => handleReject(req.id)}>Reject</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
