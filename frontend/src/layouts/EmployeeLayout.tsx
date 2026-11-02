import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function EmployeeLayout() {
  const { user, logout } = useAuth();
  return (
    <div style={{ fontFamily: "sans-serif", margin: "1rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
        <nav>
          <Link to="/leave" style={{ marginRight: "1rem" }}>
            My Leave
          </Link>
          <Link to="/attendance">Attendance</Link>
        </nav>
        <div>
          {user?.email} ({user?.role}) <button onClick={logout}>Logout</button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
