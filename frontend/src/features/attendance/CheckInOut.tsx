import { useState } from "react";
import type { AttendanceRecord } from "../../types";
import { checkIn, checkOut } from "./api";

export default function CheckInOut() {
  const [record, setRecord] = useState<AttendanceRecord | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleCheckIn = async () => {
    try {
      const data = await checkIn();
      setRecord(data);
      setMessage("Checked in.");
    } catch (err: any) {
      setMessage(err?.response?.data?.detail ?? "Check-in failed.");
    }
  };

  const handleCheckOut = async () => {
    try {
      const data = await checkOut();
      setRecord(data);
      setMessage("Checked out.");
    } catch (err: any) {
      setMessage(err?.response?.data?.detail ?? "Check-out failed.");
    }
  };

  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h2>Today</h2>
      <button onClick={handleCheckIn}>Check in</button>{" "}
      <button onClick={handleCheckOut}>Check out</button>
      {message && <p>{message}</p>}
      {record && (
        <ul>
          <li>Status: {record.status}</li>
          <li>Check-in: {record.check_in_time ?? "-"}</li>
          <li>Check-out: {record.check_out_time ?? "-"}</li>
        </ul>
      )}
    </div>
  );
}
