import { useEffect, useState } from "react";
import type { LeaveRequest, LeaveType } from "../../types";
import { cancelLeaveRequest, createLeaveRequest, fetchLeaveRequests } from "./api";

export default function LeaveList() {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [leaveType, setLeaveType] = useState<LeaveType>("vacation");
  const [reason, setReason] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchLeaveRequests();
      setRequests(data);
      setError(null);
    } catch {
      setError("Failed to load leave requests.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createLeaveRequest({ start_date: startDate, end_date: endDate, leave_type: leaveType, reason });
      setStartDate("");
      setEndDate("");
      setReason("");
      await load();
    } catch (err: any) {
      const data = err?.response?.data;
      const message =
        typeof data === "string"
          ? data
          : data
          ? Object.values(data).flat().join(" ")
          : "Could not create leave request.";
      setFormError(message);
    }
  };

  const handleCancel = async (id: number) => {
    await cancelLeaveRequest(id);
    await load();
  };

  return (
    <div>
      <h2>My Leave Requests</h2>

      <form onSubmit={handleSubmit} style={{ marginBottom: "1.5rem" }}>
        <h3>New Leave Request</h3>
        {formError && <p style={{ color: "red" }}>{formError}</p>}
        <div>
          <label>
            Start date:{" "}
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            End date:{" "}
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            Type:{" "}
            <select value={leaveType} onChange={(e) => setLeaveType(e.target.value as LeaveType)}>
              <option value="vacation">Vacation</option>
              <option value="sick">Sick</option>
              <option value="personal">Personal</option>
              <option value="other">Other</option>
            </select>
          </label>
        </div>
        <div>
          <label>
            Reason:{" "}
            <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
        </div>
        <button type="submit">Submit request</button>
      </form>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>Start</th>
            <th>End</th>
            <th>Type</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Decided by</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {requests.map((req) => (
            <tr key={req.id}>
              <td>{req.start_date}</td>
              <td>{req.end_date}</td>
              <td>{req.leave_type}</td>
              <td>{req.status}</td>
              <td>{req.reason}</td>
              <td>{req.approved_by ? req.approved_by.email : "-"}</td>
              <td>
                {req.status === "pending" && (
                  <button onClick={() => handleCancel(req.id)}>Cancel</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
