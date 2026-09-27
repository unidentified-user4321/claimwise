import { FilePlus2, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClaimsTable } from "../components/ClaimRow";
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
} from "../components/ui";
import { api } from "../services/api";
import { useSession } from "../services/session";
import type { Claim } from "../types/api";

export function MyClaims() {
  const { session } = useSession();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!session?.customerId) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    api
      .listClaims({ customer_id: session.customerId })
      .then((items) =>
        !cancelled && setClaims(
          items.filter((claim) => claim.customer_id === session.customerId),
        ),
      )
      .catch((err: Error) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [session?.customerId]);
  const filtered = claims.filter((claim) =>
    `${claim.claim_id} ${claim.policy_id} ${claim.incident_location} ${claim.status}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        eyebrow="Claims"
        title="Your claims"
        description="A clear record of every report submitted through your account."
        action={
          <Link to="/client/claims/new">
            <Button className="button-dark">
              <FilePlus2 size={17} />
              New claim
            </Button>
          </Link>
        }
      />
      <div className="mb-5 flex max-w-md items-center gap-3">
        <Search size={18} className="-mr-10 z-10 ml-3 text-muted" />
        <Input
          className="pl-10"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search policy or location"
        />
      </div>
      {loading ? (
        <LoadingState label="Loading claims" />
      ) : error ? (
        <ErrorState message={error} />
      ) : filtered.length ? (
        <ClaimsTable claims={filtered} basePath="/client" />
      ) : (
        <EmptyState
          title={claims.length ? "No matching claims" : "No claims submitted"}
          description={
            claims.length
              ? "Try a different search term."
              : "Submit your first claim to see it here."
          }
        />
      )}
    </>
  );
}
