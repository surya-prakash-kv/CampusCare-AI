
import { useEffect, useState } from "react";

import AuthPage from "./pages/AuthPage";
import StudentDashboard from "./pages/StudentDashboard";
import AdminDashboard from "./pages/AdminDashboard";

import {
  getAccessToken,
  getSessionRole,
  getCurrentStudent,
  logout,
} from "./services/authService";

function App() {
  const [session, setSession] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const token = getAccessToken();

      if (!token) {
        setCheckingSession(false);
        return;
      }

      const role = getSessionRole();

      if (role === "STUDENT") {
        try {
          const student = await getCurrentStudent();
          if (active) setSession({ role, student });
        } catch {
          logout();
        }
      } else if (role === "ADMIN") {
        if (active) setSession({ role, student: null });
      } else {
        logout();
      }

      if (active) setCheckingSession(false);
    }

    restoreSession();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
  function handleUnauthorized() {
    logout();
    setSession(null);
  }

  window.addEventListener(
    "campuscare:unauthorized",
    handleUnauthorized
  );

  return () => {
    window.removeEventListener(
      "campuscare:unauthorized",
      handleUnauthorized
    );
  };
}, []);

  function handleAuthenticated(user) {
    setSession(user);
  }

  function handleLogout() {
    logout();
    setSession(null);
  }

  if (checkingSession) {
    return <main className="dashboard-feedback">Checking your session...</main>;
  }

  if (!session) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  if (session.role === "STUDENT") {
    return (
      <StudentDashboard
        student={session.student}
        onLogout={handleLogout}
      />
    );
  }

  if (session.role === "ADMIN") {
    return <AdminDashboard onLogout={handleLogout} />;
  }

  return <AuthPage onAuthenticated={handleAuthenticated} />;
}

export default App;
