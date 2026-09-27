import {
  ArrowRight,
  BriefcaseBusiness,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SignIn, SignUp, useAuth } from "@clerk/react";
import type { Role } from "../types/api";
import { useSession } from "../services/session";
import { api } from "../services/api";
import { Button, Field, Input } from "../components/ui";

export function Login() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const workspace: Role = params.get("workspace") === "employee" ? "employee" : "client";
  const registering = workspace === "client" && params.get("mode") === "signup";
  const { isLoaded, isSignedIn } = useAuth();
  const { session, loading, needsLink, error: sessionError, refreshUser, signOut } = useSession();
  const [customerId, setCustomerId] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const redirectUrl = `/login?workspace=${workspace}`;
  const mismatch = session && session.role !== workspace
    ? `This account belongs to the ${session.role === "employee" ? "Employee" : "Client"} workspace.` : "";

  useEffect(() => {
    if (session && session.role === workspace) {
      navigate(session.role === "employee" ? "/employee" : "/client", { replace: true });
    }
  }, [session?.userId, session?.role, workspace, navigate]);

  function selectWorkspace(role: Role) {
    setParams({ workspace: role });
    setError("");
  }

  async function linkCustomer(event: React.FormEvent) {
    event.preventDefault();
    setError(""); setSubmitting(true);
    try {
      await api.linkCustomer(customerId.trim());
      refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not link customer.");
    } finally { setSubmitting(false); }
  }

  return (
    <main className="grid min-h-screen bg-ink lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative hidden overflow-hidden bg-ink px-14 py-14 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -left-24 top-28 h-80 w-80 rounded-full border border-mint/20" />
        <div className="absolute -left-12 top-40 h-56 w-56 rounded-full border border-mint/10" />
        <div className="relative flex items-center gap-3">
          <span className="brand-mark">
            <ShieldCheck size={20} />
          </span>
          <span>
            <span className="block font-display text-lg font-bold">
              claimwise
            </span>
            <span className="block text-[10px] uppercase tracking-[0.2em] text-white/45">
              motor insurance
            </span>
          </span>
        </div>
        <div className="relative max-w-xl">
          <p className="eyebrow text-mint">Clearer claims, better decisions</p>
          <h1 className="mt-5 font-display text-6xl font-semibold leading-[1.02] tracking-tight">
            A calmer way to move a claim forward.
          </h1>
          <p className="mt-7 max-w-md text-base leading-7 text-white/60">
            One workspace for claimants and the people who review their claims.
            Every signal stays explainable, every final decision stays human.
          </p>
        </div>
        <p className="relative text-xs text-white/35">
          AI-assisted insurance claim analysis · Decision support only
        </p>
      </section>
      <section className="flex items-center justify-center bg-paper px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <span className="brand-mark bg-ink text-mint">
              <ShieldCheck size={20} />
            </span>
            <p className="mt-4 font-display text-xl font-bold text-ink">
              claimwise
            </p>
          </div>
          <p className="eyebrow">Welcome back</p>
          <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight text-ink">
            {registering ? "Register as Client" : "Sign in to your workspace."}
          </h2>
          <div className="mt-8 grid grid-cols-2 gap-3">
            <button
              type="button"
              disabled={submitting}
              aria-pressed={workspace === "client"}
              onClick={() => selectWorkspace("client")}
              className={`role-card ${workspace === "client" ? "role-card-active" : ""}`}
            >
              <UserRound size={19} />
              <span>Client</span>
              <small>Submit and track claims</small>
            </button>
            <button
              type="button"
              disabled={submitting}
              aria-pressed={workspace === "employee"}
              onClick={() => selectWorkspace("employee")}
              className={`role-card ${workspace === "employee" ? "role-card-active" : ""}`}
            >
              <BriefcaseBusiness size={19} />
              <span>Employee</span>
              <small>Review the claim queue</small>
            </button>
          </div>
          <div className="mt-8 space-y-5">
            {(!isLoaded || loading) ? <p role="status">Loading your workspace...</p> : !isSignedIn ? (
              registering ? <SignUp routing="hash" signInUrl="/login?workspace=client"
                forceRedirectUrl={redirectUrl} /> :
              <SignIn key={workspace} routing="hash" withSignUp={false} transferable={workspace === "client"}
                appearance={workspace === "employee" ? { elements: { footerAction: { display: "none" } } } : undefined}
                signUpUrl="/login?workspace=client&mode=signup"
                forceRedirectUrl={redirectUrl} signUpForceRedirectUrl="/login?workspace=client" />
            ) : <>
              {sessionError ? <>
                <p role="alert" className="text-sm text-coral">{sessionError}</p>
                <Button onClick={refreshUser}>Retry</Button>
              </> : mismatch ? <p role="alert" className="text-sm text-coral">{mismatch}</p>
              : session ? <Button className="button-dark w-full"
                onClick={() => navigate(session.role === "employee" ? "/employee" : "/client")}>
                Enter {workspace === "employee" ? "Employee" : "Client"} workspace <ArrowRight size={17} />
              </Button> : needsLink && workspace === "client" ? (
                <form onSubmit={linkCustomer} className="space-y-5">
                  <p className="text-sm text-muted">Link your existing Customer ID to continue.</p>
                  <Field label="Customer ID">
                    <Input required maxLength={50} disabled={submitting} value={customerId}
                      onChange={event => setCustomerId(event.target.value)} />
                  </Field>
                  <Button type="submit" disabled={submitting} className="button-dark w-full">
                    {submitting ? "Linking..." : "Link customer"}
                  </Button>
                </form>
              ) : needsLink ? <div className="space-y-3">
                <p className="text-sm text-muted">This account has no employee mapping. Ask the project maintainer to provision it.</p>
                <Button onClick={refreshUser}>Retry</Button>
              </div> : null}
              {error && <p role="alert" className="text-sm text-coral">{error}</p>}
              <button type="button" className="text-sm text-ink underline" onClick={() => void signOut()}>
                Sign out
              </button>
            </>}
          </div>
        </div>
      </section>
    </main>
  );
}
