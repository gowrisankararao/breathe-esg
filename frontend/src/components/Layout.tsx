import {
  LayoutDashboard,
  LogOut,
  Upload,
  ClipboardCheck,
  Leaf,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/review", icon: ClipboardCheck, label: "Review queue" },
  { to: "/upload", icon: Upload, label: "Ingest data" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, organization, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-800/80 bg-slate-900/40 backdrop-blur-xl">
        <div className="flex items-center gap-3 border-b border-slate-800/80 px-6 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-breathe-600/20 text-breathe-400">
            <Leaf className="h-5 w-5" />
          </div>
          <div>
            <p className="font-display text-lg font-semibold tracking-tight text-white">
              Breathe
            </p>
            <p className="text-xs text-slate-500">ESG Data Review</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-breathe-600/15 text-breathe-400"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-800/80 p-4">
          <div className="mb-3 rounded-xl bg-slate-800/40 px-4 py-3">
            <p className="truncate text-sm font-medium text-white">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="truncate text-xs text-slate-500">{organization?.name}</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="btn-secondary w-full"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="ml-64 flex-1">
        <div className="mx-auto max-w-7xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
