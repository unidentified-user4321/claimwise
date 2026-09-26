import {
  ArrowRight,
  BriefcaseBusiness,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Role } from "../types/api";
import { useSession } from "../services/session";
import { api } from "../services/api";
import { Button, Field, Input } from "../components/ui";

export function Login() {
  const navigate = useNavigate();
  const { signIn } = useSession();
  const [role, setRole] = useState<Role>("client");
  const [customerId, setCustomerId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const localSession = await api.createLocalSession(role, role === "client" ? customerId : employeeId);
      signIn(localSession.role, localSession.user_id);
      navigate(role === "employee" ? "/employee" : "/client");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the demo session.");
    } finally {
      setSubmitting(false);
    }
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
            Choose your workspace.
          </h2>
          <div className="mt-8 grid grid-cols-2 gap-3">
            <button
              disabled={submitting}
              onClick={() => {
                setRole("client");
                setError("");
              }}
              className={`role-card ${role === "client" ? "role-card-active" : ""}`}
            >
              <UserRound size={19} />
              <span>Client</span>
              <small>Submit and track claims</small>
            </button>
            <button
              disabled={submitting}
              onClick={() => {
                setRole("employee");
                setError("");
              }}
              className={`role-card ${role === "employee" ? "role-card-active" : ""}`}
            >
              <BriefcaseBusiness size={19} />
              <span>Employee</span>
              <small>Review the claim queue</small>
            </button>
          </div>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <p className="text-sm leading-6 text-muted">
              Enter a local demo workspace to submit or review claims.
            </p>
            <Field label={role === "client" ? "Customer ID" : "Employee ID"}>
              <Input
                required
                disabled={submitting}
                value={role === "client" ? customerId : employeeId}
                onChange={(event) => {
                  if (role === "client") setCustomerId(event.target.value);
                  else setEmployeeId(event.target.value);
                  setError("");
                }}
              />
            </Field>
            {error && <p role="alert" className="text-sm text-coral">{error}</p>}
            <Button disabled={submitting} type="submit" className="button-dark w-full">
              {submitting ? "Starting workspace..." : "Enter workspace"} <ArrowRight size={17} />
            </Button>
          </form>
        </div>
      </section>
    </main>
  );
}
