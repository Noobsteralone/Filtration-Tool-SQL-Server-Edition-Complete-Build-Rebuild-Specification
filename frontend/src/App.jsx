import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext.jsx";
import AppLayout from "./layout/AppLayout.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import FiltrationPage from "./pages/FiltrationPage.jsx";
import DuplicateTldCheckPage from "./pages/DuplicateTldCheckPage.jsx";
import MasterFilesPage from "./pages/MasterFilesPage.jsx";
import OtherTldMasterPage from "./pages/OtherTldMasterPage.jsx";
import ReferenceListsPage from "./pages/ReferenceListsPage.jsx";
import JobsPage from "./pages/JobsPage.jsx";
import JobDetailPage from "./pages/JobDetailPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import UsersPage from "./pages/UsersPage.jsx";
import ActivityLogsPage from "./pages/ActivityLogsPage.jsx";

function RequireAuth({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RequireRole({ role, children }) {
  const { hasRole } = useAuth();
  if (!hasRole(role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="filtration" element={<FiltrationPage />} />
        <Route path="duplicate-tld-check" element={<DuplicateTldCheckPage />} />
        <Route path="master-files" element={<MasterFilesPage />} />
        <Route path="other-tld-master" element={<OtherTldMasterPage />} />
        <Route
          path="reference-lists"
          element={
            <RequireRole role="ADMIN">
              <ReferenceListsPage />
            </RequireRole>
          }
        />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="jobs/:jobId" element={<JobDetailPage />} />
        <Route
          path="settings"
          element={
            <RequireRole role="ADMIN">
              <SettingsPage />
            </RequireRole>
          }
        />
        <Route
          path="users"
          element={
            <RequireRole role="SUPER_ADMIN">
              <UsersPage />
            </RequireRole>
          }
        />
        <Route
          path="activity-logs"
          element={
            <RequireRole role="ADMIN">
              <ActivityLogsPage />
            </RequireRole>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
