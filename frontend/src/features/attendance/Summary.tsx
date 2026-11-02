import { useEffect, useState } from "react";
import type { AttendanceSummary } from "../../types";
import { fetchSummary } from "./api";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export default function Summary() {
  const [month, setMonth] = useState(currentMonth());
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (m: string) => {
    try {
      const data = await fetchSummary(m);
      setSummary(data);
      setError(null);
    } catch {
      setError("Failed to load summary.");
    }
  };

  useEffect(() => {
    load(month);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h2>Monthly Summary</h2>
      <label>
        Month:{" "}
        <input
          type="month"
          value={month}
          onChange={(e) => {
            setMonth(e.target.value);
            load(e.target.value);
          }}
        />
      </label>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {summary && (
        <ul>
          <li>Present: {summary.present}</li>
          <li>Absent: {summary.absent}</li>
          <li>Half day: {summary.half_day}</li>
        </ul>
      )}
    </div>
  );
}
