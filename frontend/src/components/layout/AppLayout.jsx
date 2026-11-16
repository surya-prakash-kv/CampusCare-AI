
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function AppLayout({
  role,
  activeSection,
  onNavigate,
  userName,
  onLogout,
  onRefresh,
  refreshing = false,
  children,
}) {
  const isAdmin = role === "ADMIN";

  const navigation = isAdmin
    ? [
        { id: "overview", label: "Overview", icon: "LayoutDashboard" },
        { id: "complaints", label: "All Complaints", icon: "ClipboardList" },
        { id: "ai-reviews", label: "AI Reviews", icon: "Sparkles" },
        { id: "ai-operations", label: "AI Operations", icon: "Activity" },
      ]
    : [
        { id: "overview", label: "Overview", icon: "LayoutDashboard" },
        { id: "complaints", label: "My Complaints", icon: "ClipboardList" },
        { id: "submit", label: "Submit Complaint", icon: "PlusCircle" },
      ];

  return (
    <div className={`app-layout ${isAdmin ? "app-layout-admin" : "app-layout-student"}`}>
      <Sidebar
        role={role}
        navigation={navigation}
        activeSection={activeSection}
        onNavigate={onNavigate}
        onLogout={onLogout}
      />

      <div className="app-main">
        <Topbar
          role={role}
          userName={userName}
          onRefresh={isAdmin ? onRefresh : undefined}
          refreshing={refreshing}
          onLogout={onLogout}
        />

        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
