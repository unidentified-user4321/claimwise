import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  ClipboardCheck,
  FilePlus2,
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { useState } from "react";
import { useSession } from "../services/session";

const clientLinks = [
  { label: "Overview", to: "/client", icon: LayoutDashboard },
  { label: "Submit claim", to: "/client/claims/new", icon: FilePlus2 },
  { label: "My claims", to: "/client/claims", icon: FileText },
];

const employeeLinks = [
  { label: "Overview", to: "/employee", icon: LayoutDashboard },
  { label: "Claims queue", to: "/employee/claims", icon: ClipboardCheck },
];

export function AppShell() {
  const { session, signOut } = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const links = session?.role === "employee" ? employeeLinks : clientLinks;
  const isDetails =
    location.pathname.includes("/claims/") &&
    !location.pathname.endsWith("/new");

  if (!session) return <Outlet />;

  return (
    <div className="min-h-screen bg-paper text-ink">
      <aside
        className={`sidebar ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="flex items-center justify-between px-6 py-6 lg:block">
          <button
            onClick={() =>
              navigate(session.role === "employee" ? "/employee" : "/client")
            }
            className="flex items-center gap-3 text-left"
          >
            <span className="brand-mark">
              <ShieldCheck size={20} strokeWidth={2.5} />
            </span>
            <span>
              <span className="block font-display text-lg font-bold leading-none text-white">
                claimwise
              </span>
              <span className="mt-1 block text-[10px] uppercase tracking-[0.2em] text-white/45">
                motor insurance
              </span>
            </span>
          </button>
          <button
            className="text-white/60 lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>
        <div className="mx-6 mt-7 rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">
            Signed in as
          </p>
          <div className="mt-2 flex items-center gap-2 text-sm font-semibold text-white">
            <UserRound size={15} className="text-mint" />
            {session.role === "employee" ? "Claims employee" : "Client"}
          </div>
        </div>
        <nav className="mt-8 space-y-1 px-3">
          {links.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `nav-link ${isActive || (isDetails && label === "Claims queue") ? "nav-link-active" : ""}`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-6 left-6 right-6">
          <button
            onClick={() => {
              signOut();
              navigate("/login");
            }}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/50 transition hover:bg-white/10 hover:text-white"
          >
            <LogOut size={17} />
            Sign out
          </button>
        </div>
      </aside>
      {mobileOpen && (
        <button
          aria-label="Close navigation overlay"
          className="fixed inset-0 z-30 bg-ink/30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <main className="lg:pl-[260px]">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line/80 bg-paper/90 px-5 backdrop-blur md:px-10 lg:px-12">
          <button
            className="rounded-lg p-2 text-muted hover:bg-white lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={21} />
          </button>
          <div className="hidden text-xs font-semibold uppercase tracking-[0.16em] text-muted lg:block">
            {session.role === "employee"
              ? "Operations workspace"
              : "Your claim workspace"}
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-xs text-muted sm:inline">
              {session.userId
                ? `ID ${session.userId.slice(0, 8)}...`
                : "Local session"}
            </span>
            <span className="avatar">
              {session.role === "employee" ? "E" : "C"}
            </span>
          </div>
        </header>
        <div className="mx-auto max-w-[1440px] px-5 py-8 md:px-10 md:py-10 lg:px-12">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
