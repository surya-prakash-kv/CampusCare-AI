
import { RefreshCw, ShieldCheck, GraduationCap, LogOut } from "lucide-react";

function Topbar({
  role,
  userName,
  onRefresh,
  refreshing = false,
  onLogout,
}) {
  const isAdmin = role === "ADMIN";

  return (
    <header className="app-topbar">
      <div className="topbar-heading">
        <span className="topbar-breadcrumb">
          CampusCare AI <span>/</span> {isAdmin ? "Administration" : "Student Portal"}
        </span>

        <div className="topbar-welcome">
          <h2>{isAdmin ? "Admin Workspace" : "Student Workspace"}</h2>
          <span className="topbar-role-icon">
            {isAdmin ? <ShieldCheck size={16} /> : <GraduationCap size={17} />}
          </span>
        </div>
      </div>

      <div className="topbar-actions">
        {onRefresh && (
          <button
            type="button"
            className="topbar-refresh"
            onClick={onRefresh}
            disabled={refreshing}
            aria-label={refreshing ? "Refreshing dashboard" : "Refresh dashboard"}
            title={refreshing ? "Refreshing dashboard" : "Refresh dashboard"}
          >
            <RefreshCw
              size={16}
              className={refreshing ? "admin-spin" : ""}
            />
            <span>{refreshing ? "Refreshing..." : "Refresh"}</span>
          </button>
        )}

        <div className="topbar-user">
          <div
  className="topbar-avatar"
  aria-hidden="true"
>
            {userName?.trim()?.charAt(0)?.toUpperCase() || (
              isAdmin ? "A" : "S"
            )}
          </div>

          <div className="topbar-user-info">
            <strong>{userName?.trim() || (isAdmin ? "Administrator" : "Student")}</strong>
            <span>{isAdmin ? "Administrator" : "Student"}</span>
          </div>
        </div>

        <button
          type="button"
          className="topbar-logout"
          onClick={onLogout}
          aria-label="Sign out"
          title="Sign out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;
