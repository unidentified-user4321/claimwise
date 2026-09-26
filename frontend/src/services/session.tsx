import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Role } from "../types/api";

interface Session {
  role: Role;
  userId: string;
}

interface SessionContextValue {
  session: Session | null;
  signIn: (role: Role, userId: string) => void;
  signOut: () => void;
}

export const STORAGE_KEY = "claimwise-insurance-project-session";
const SessionContext = createContext<SessionContextValue | undefined>(
  undefined,
);

function readStoredSession(): Session | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const value = stored ? JSON.parse(stored) : null;
    return value && ["client", "employee"].includes(value.role)
      && typeof value.userId === "string" && value.userId.trim()
      ? value as Session : null;
  } catch {
    return null;
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(readStoredSession);
  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      signIn: (role, userId) => {
        const next = { role, userId };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        setSession(next);
      },
      signOut: () => {
        localStorage.removeItem(STORAGE_KEY);
        setSession(null);
      },
    }),
    [session],
  );
  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context)
    throw new Error("useSession must be used within SessionProvider");
  return context;
}
