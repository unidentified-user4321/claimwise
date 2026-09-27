import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { useAuth, useClerk } from "@clerk/react";
import type { AuthUser } from "../types/api";
import { api, ApiError, setTokenGetter } from "./api";

type Session = { userId: string } & (
  { role: "client"; customerId: string } | { role: "employee"; customerId: null }
);
interface SessionContextValue {
  session: Session | null;
  loading: boolean;
  needsLink: boolean;
  error: string;
  refreshUser: () => void;
  signOut: () => Promise<void>;
}
const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, userId, getToken } = useAuth();
  const clerk = useClerk();
  const [mapping, setMapping] = useState<AuthUser | null>(null);
  const [resolvedFor, setResolvedFor] = useState<string | null>(null);
  const [needsLink, setNeedsLink] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const refreshUser = useCallback(() => { setResolvedFor(null); setRevision(value => value + 1); }, []);

  useEffect(() => {
    let cancelled = false;
    setTokenGetter(isSignedIn ? getToken : undefined);
    setMapping(null); setNeedsLink(false); setError(""); setResolvedFor(null);
    if (isLoaded && isSignedIn && userId) {
      api.me().then(user => {
        if (!cancelled) setMapping(user);
      }).catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403 && err.message === "Account linking required") setNeedsLink(true);
        else setError(err instanceof Error ? err.message : "Could not load your workspace.");
      }).finally(() => { if (!cancelled) setResolvedFor(userId); });
    }
    return () => { cancelled = true; setTokenGetter(); };
  }, [isLoaded, isSignedIn, userId, getToken, revision]);

  const loading = !isLoaded || Boolean(isSignedIn && resolvedFor !== userId);
  const current = !loading && isSignedIn && mapping?.clerk_user_id === userId ? mapping : null;
  const session: Session | null = current
    ? current.role === "client" && current.customer_id
      ? { userId: current.user_id, role: "client", customerId: current.customer_id }
      : current.role === "employee" ? { userId: current.user_id, role: "employee", customerId: null } : null
    : null;
  return <SessionContext.Provider value={{
    session, loading, needsLink: !loading && Boolean(isSignedIn) && needsLink, error,
    refreshUser,
    signOut: async () => { await clerk.signOut({ redirectUrl: "/login" }); },
  }}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession must be used within SessionProvider");
  return context;
}
