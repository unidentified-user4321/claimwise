import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { useSession } from "./services/session";
import { Login } from "./pages/Login";
import { ClientDashboard } from "./pages/ClientDashboard";
import { SubmitClaim } from "./pages/SubmitClaim";
import { MyClaims } from "./pages/MyClaims";
import { ClaimDetails } from "./pages/ClaimDetails";
import { EmployeeDashboard } from "./pages/EmployeeDashboard";
import { ClaimsList } from "./pages/ClaimsList";
import { EmployeeClaimDetails } from "./pages/EmployeeClaimDetails";
import { InvestigationHistory } from "./pages/InvestigationHistory";

function RoleRoute({
  role,
  children,
}: {
  role: "client" | "employee";
  children: React.ReactNode;
}) {
  const { session } = useSession();
  if (!session) return <Navigate to="/login" replace />;
  if (session.role !== role)
    return (
      <Navigate
        to={session.role === "employee" ? "/employee" : "/client"}
        replace
      />
    );
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<AppShell />}>
        <Route
          path="/client"
          element={
            <RoleRoute role="client">
              <ClientDashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/client/claims/new"
          element={
            <RoleRoute role="client">
              <SubmitClaim />
            </RoleRoute>
          }
        />
        <Route
          path="/client/claims"
          element={
            <RoleRoute role="client">
              <MyClaims />
            </RoleRoute>
          }
        />
        <Route
          path="/client/claims/:claimId"
          element={
            <RoleRoute role="client">
              <ClaimDetails />
            </RoleRoute>
          }
        />
        <Route
          path="/employee"
          element={
            <RoleRoute role="employee">
              <EmployeeDashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/employee/claims"
          element={
            <RoleRoute role="employee">
              <ClaimsList />
            </RoleRoute>
          }
        />
        <Route
          path="/employee/claims/:claimId"
          element={
            <RoleRoute role="employee">
              <EmployeeClaimDetails />
            </RoleRoute>
          }
        />
        <Route
          path="/employee/claims/:claimId/history"
          element={
            <RoleRoute role="employee">
              <InvestigationHistory />
            </RoleRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
