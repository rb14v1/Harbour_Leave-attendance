import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import CheckInOut from "../features/attendance/CheckInOut";
import Summary from "../features/attendance/Summary";
import Approvals from "../features/leave/Approvals";
import LeaveList from "../features/leave/LeaveList";
import TeamView from "../features/team/TeamView";
import EmployeeLayout from "../layouts/EmployeeLayout";
import ManagerLayout from "../layouts/ManagerLayout";
import Login from "./Login";

function AttendancePage() {
  return (
    <div>
      <CheckInOut />
      <Summary />
    </div>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RequireManager({ children }: { children: JSX.Element }) {
  const { user } = useAuth();
  if (user?.role !== "manager") return <Navigate to="/leave" replace />;
  return children;
}

export default function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  const Layout = user?.role === "manager" ? ManagerLayout : EmployeeLayout;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/leave" replace /> : <Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/leave" element={<LeaveList />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route
          path="/approvals"
          element={
            <RequireManager>
              <Approvals />
            </RequireManager>
          }
        />
        <Route
          path="/team"
          element={
            <RequireManager>
              <TeamView />
            </RequireManager>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to={user ? "/leave" : "/login"} replace />} />
    </Routes>
  );
}
