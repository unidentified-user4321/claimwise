import {
  AlertTriangle,
  ArrowUpRight,
  ClipboardList,
  Clock3,
  FileSearch,
  UsersRound,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { ClaimsTable } from "../components/ClaimRow";
import {
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";
import { api } from "../services/api";
import type { Claim } from "../types/api";

export function EmployeeDashboard() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    api
      .listClaims()
      .then((items) => { if (!cancelled) setClaims(items); })
      .catch((err: unknown) => {
        if (!cancelled) setError(`Unable to load claims.${err instanceof Error ? ` ${err.message}` : ""}`);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);
  const timestamp = (value: string | null | undefined) => {
    const time = value ? new Date(value).getTime() : NaN;
    return Number.isFinite(time) ? time : -Infinity;
  };
  const active = claims
    .filter((claim) => ["submitted", "under_review"].includes(claim.status))
    .sort((a, b) => timestamp(b.created_at) - timestamp(a.created_at));
  const today = new Date();
  const newToday = claims.filter((claim) => {
    const time = timestamp(claim.created_at);
    if (!Number.isFinite(time)) return false;
    const created = new Date(time);
    return created.getFullYear() === today.getFullYear()
      && created.getMonth() === today.getMonth()
      && created.getDate() === today.getDate();
  });
  const countsAvailable = !loading && !error;
  return (
    <>
      <PageHeader
        eyebrow="Employee workspace"
        title="Claims control room."
        description="Review incoming claims, inspect available analysis, and record the next human decision."
        action={
          <Link to="/employee/claims">
            <Button className="button-dark">
              <FileSearch size={17} />
              Open claims queue
            </Button>
          </Link>
        }
      />
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="stat-card">
              <div className="stat-icon bg-mint/20 text-teal">
                <ClipboardList size={19} />
              </div>
              <p className="stat-label">Total claims</p>
              <p className="stat-value">{countsAvailable ? claims.length : "—"}</p>
              <p className="stat-note">In the current queue</p>
            </Card>
            <Card className="stat-card">
              <div className="stat-icon bg-amber/20 text-amber">
                <Clock3 size={19} />
              </div>
              <p className="stat-label">Needs review</p>
              <p className="stat-value">{countsAvailable ? active.length : "—"}</p>
              <p className="stat-note">Open workflow items</p>
            </Card>
            <Card className="stat-card">
              <div className="stat-icon bg-coral/10 text-coral">
                <AlertTriangle size={19} />
              </div>
              <p className="stat-label">New today</p>
              <p className="stat-value">{countsAvailable ? newToday.length : "—"}</p>
              <p className="stat-note">Created today</p>
            </Card>
          </div>
          <div className="mt-10">
            <div className="mb-4 flex items-end justify-between">
              <div>
                <p className="eyebrow">Work queue</p>
                <h2 className="section-title">Claims needing attention</h2>
              </div>
              <Link
                to="/employee/claims"
                className="text-sm font-semibold text-teal hover:text-ink"
              >
                View queue <ArrowUpRight size={15} className="inline" />
              </Link>
            </div>
            {loading ? (
              <LoadingState label="Loading claims..." />
            ) : error ? (
              <ErrorState message={error} />
            ) : active.length ? (
              <ClaimsTable claims={active.slice(0, 5)} basePath="/employee" />
            ) : (
              <EmptyState
                title="The queue is clear"
                description="New claims will appear here when clients submit them."
              />
            )}
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Card className="flex gap-4 bg-ink text-white">
              <div className="stat-icon bg-white/10 text-mint">
                <UsersRound size={19} />
              </div>
              <div>
                <p className="font-display text-lg font-semibold">
                  Human review stays central
                </p>
                <p className="mt-2 text-sm leading-6 text-white/55">
                  AI/ML outputs support investigation. They are not proof of
                  fraud or a replacement for employee judgment.
                </p>
              </div>
            </Card>
          </div>
    </>
  );
}
