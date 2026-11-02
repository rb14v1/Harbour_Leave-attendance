import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/leave");
    } catch {
      setError("Invalid email or password.");
    }
  };

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 320, margin: "4rem auto" }}>
      <h1>Leave & Attendance Tracker</h1>
      <form onSubmit={handleSubmit}>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <div>
          <label>
            Email
            <br />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            Password
            <br />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
        </div>
        <button type="submit">Log in</button>
      </form>
      <p style={{ fontSize: "0.85rem", color: "#555" }}>
        Demo accounts: manager@example.com / employee1@example.com / employee2@example.com, password
        demo12345
      </p>
    </div>
  );
}
