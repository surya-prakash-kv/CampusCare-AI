import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ClipboardList,
  LayoutDashboard,
  PlusCircle,
  ShieldCheck,
  Sparkles,
  LogOut,
  Menu,
  X,
  GraduationCap,
} from "lucide-react";

const ICONS = {
  LayoutDashboard,
  ClipboardList,
  PlusCircle,
  Sparkles,
  Activity,
};

function Sidebar({
  role,
  navigation,
  activeSection,
  onNavigate,
  onLogout,
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuTriggerRef = useRef(null);
  const sidebarRef = useRef(null);
  const wasMobileOpen = useRef(false);

  const isAdmin = role === "ADMIN";

  // Handle Escape key and lock background scrolling on mobile.
  useEffect(() => {
  if (!mobileOpen) {
    if (wasMobileOpen.current) {
      menuTriggerRef.current?.focus();
      wasMobileOpen.current = false;
    }

    return undefined;
  }

  wasMobileOpen.current = true;

  const previousOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";

  const sidebar = sidebarRef.current;

  const getFocusableElements = () =>
    sidebar?.querySelectorAll(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

  getFocusableElements()?.[0]?.focus();

  function handleKeyDown(event) {
    if (event.key === "Escape") {
      setMobileOpen(false);
      return;
    }

    if (event.key !== "Tab") return;

    const elements = getFocusableElements();

    if (!elements?.length) return;

    const firstElement = elements[0];
    const lastElement = elements[elements.length - 1];

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (
      !event.shiftKey &&
      document.activeElement === lastElement
    ) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  document.addEventListener("keydown", handleKeyDown);

  return () => {
    document.removeEventListener("keydown", handleKeyDown);
    document.body.style.overflow = previousOverflow;
  };
}, [mobileOpen]);

  function handleNavigate(section) {
    onNavigate?.(section);
    setMobileOpen(false);
  }

  function handleLogout() {
    setMobileOpen(false);
    onLogout?.();
  }

  return (
    <>
      {/* Mobile navigation trigger */}
      <button
  ref={menuTriggerRef}
  type="button"
  className="mobile-menu-trigger"
        aria-label={
          mobileOpen ? "Close navigation menu" : "Open navigation menu"
        }
        aria-expanded={mobileOpen}
        aria-controls="campuscare-sidebar"
        onClick={() => setMobileOpen((previous) => !previous)}
      >
        {mobileOpen ? <X size={21} /> : <Menu size={21} />}
      </button>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Close navigation menu"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Main sidebar */}
      <aside
  ref={sidebarRef}
  id="campuscare-sidebar"
  className={`app-sidebar ${mobileOpen ? "app-sidebar-open" : ""}`}
  aria-label="CampusCare navigation"
>
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <ShieldCheck size={23} />
          </div>

          <div className="sidebar-brand-text">
            <strong>CampusCare</strong>
            <span>AI PLATFORM</span>
          </div>

          <button
            type="button"
            className="sidebar-mobile-close"
            aria-label="Close navigation menu"
            onClick={() => setMobileOpen(false)}
          >
            <X size={19} />
          </button>
        </div>

        {/* Workspace information */}
        <div className="sidebar-workspace">
          <div className="sidebar-workspace-icon">
            {isAdmin ? (
              <ShieldCheck size={17} />
            ) : (
              <GraduationCap size={18} />
            )}
          </div>

          <div>
            <span>WORKSPACE</span>
            <strong>
              {isAdmin ? "Administration" : "Student Portal"}
            </strong>
          </div>
        </div>

        {/* Navigation */}
        <nav
          className="sidebar-navigation"
          aria-label="Main navigation"
        >
          <span className="sidebar-section-label">MENU</span>

          {navigation.map((item) => {
            const Icon = ICONS[item.icon];
            const isActive = activeSection === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={`sidebar-nav-item ${
                  isActive ? "sidebar-nav-active" : ""
                }`}
                aria-current={isActive ? "page" : undefined}
                onClick={() => handleNavigate(item.id)}
              >
                {Icon && (
                  <Icon size={19} strokeWidth={1.9} />
                )}

                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="sidebar-footer">
          <div className="sidebar-footer-note">
            <ShieldCheck size={17} />
            <span>Secure complaint management</span>
          </div>

          <button
            type="button"
            className="sidebar-logout"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            <span>Sign out</span>
          </button>

          <div className="sidebar-version">
            CampusCare AI <span>•</span> Workspace
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
