import {
  ArrowUpRight,
  Clock3,
  FileCheck2,
  FilePlus2,
  ShieldAlert,
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
import { useSession } from "../services/session";
import type { Claim } from "../types/api";

export function ClientDashboard() {
  const { session } = useSession();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!session?.userId) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    api
      .listClaims({ customer_id: session.userId })
      .then((items) => { if (!cancelled) setClaims(items); })
      .catch((err: Error) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [session?.userId]);
  const mine = claims.filter((claim) => claim.customer_id === session?.userId)
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  const reviewCount = mine.filter((claim) =>
    ["submitted", "under_review"].includes(claim.status),
  ).length;
  const latest = mine.slice(0, 3);

  return (
    <>
      <PageHeader
        eyebrow="Client workspace"
        title="Good morning."
        description="Keep an eye on your submitted claims and start a new report when you need to."
        action={
          <Link to="/client/claims/new">
            <Button className="button-dark">
              <FilePlus2 size={17} />
              Submit a claim
            </Button>
          </Link>
        }
      />
      {loading ? (
        <LoadingState label="Loading your claims" />
      ) : error ? (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="stat-card">
              <div className="stat-icon bg-mint/20 text-teal">
                <FileCheck2 size={19} />
              </div>
              <p className="stat-label">My claims</p>
              <p className="stat-value">{mine.length}</p>
              <p className="stat-note">All submitted reports</p>
            </Card>
            <Card className="stat-card">
              <div className="stat-icon bg-amber/20 text-amber">
                <Clock3 size={19} />
              </div>
              <p className="stat-label">Under review</p>
              <p className="stat-value">{reviewCount}</p>
              <p className="stat-note">Awaiting a decision</p>
            </Card>
            <Card className="stat-card">
              <div className="stat-icon bg-coral/10 text-coral">
                <ShieldAlert size={19} />
              </div>
              <p className="stat-label">Next step</p>
              <p className="mt-2 font-display text-xl font-semibold text-ink">
                Stay reachable
              </p>
              <p className="stat-note">We may request more details</p>
            </Card>
          </div>
          <div className="mt-10">
            <div className="mb-4 flex items-end justify-between">
              <div>
                <p className="eyebrow">Recent activity</p>
                <h2 className="section-title">Your latest claims</h2>
              </div>
              <Link
                to="/client/claims"
                className="text-sm font-semibold text-teal hover:text-ink"
              >
                View all <ArrowUpRight size={15} className="inline" />
              </Link>
            </div>
            {latest.length ? (
              <ClaimsTable claims={latest} basePath="/client" />
            ) : (
              <EmptyState
                title="No claims yet"
                description="Your submitted claims will appear here once the backend accepts them."
                action={
                  <Link to="/client/claims/new">
                    <Button className="button-dark">Start a claim</Button>
                  </Link>
                }
              />
            )}
          </div>
        </>
      )}
    </>
  );
}
