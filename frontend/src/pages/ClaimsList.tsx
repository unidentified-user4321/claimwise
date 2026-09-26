import { Filter, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ClaimsTable } from "../components/ClaimRow";
import {
  EmptyState,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Select,
} from "../components/ui";
import { api } from "../services/api";
import type { Claim } from "../types/api";

export function ClaimsList() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [incidentType, setIncidentType] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .listClaims()
      .then(setClaims)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);
  const filtered = useMemo(
    () =>
      claims.filter(
        (claim) =>
          (status === "all" || claim.status === status) &&
          (incidentType === "all" || claim.incident_type === incidentType) &&
          `${claim.claim_id} ${claim.policy_id} ${claim.customer_id} ${claim.incident_location}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [claims, query, status, incidentType],
  );
  return (
    <>
      <PageHeader
        eyebrow="Employee workspace"
        title="Claims queue"
        description="Search and triage all submitted motor insurance claims."
      />
      <div className="mb-5 grid gap-3 md:grid-cols-[1fr_180px_180px]">
        <div className="relative">
          <Search size={18} className="absolute left-3 top-3 text-muted" />
          <Input
            className="pl-10"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search claims by ID, customer, policy or location"
            placeholder="Search ID, customer, policy, location"
          />
        </div>
        <div className="relative">
          <Filter
            size={16}
            className="pointer-events-none absolute left-3 top-3.5 z-10 text-muted"
          />
          <Select
            aria-label="Filter by status"
            className="pl-9"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="all">All statuses</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under review</option>
            <option value="awaiting_information">Awaiting information</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="closed">Closed</option>
          </Select>
        </div>
        <Select aria-label="Filter by incident type" value={incidentType} onChange={(e) => setIncidentType(e.target.value)}>
          <option value="all">All incident types</option>
          {[...new Set(claims.map((claim) => claim.incident_type))].sort().map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </Select>
      </div>
      {loading ? (
        <LoadingState label="Loading claim queue" />
      ) : error ? (
        <ErrorState message={error} />
      ) : filtered.length ? (
        <>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-muted">
            {filtered.length} claim{filtered.length === 1 ? "" : "s"}
          </p>
          <ClaimsTable claims={filtered} basePath="/employee" />
        </>
      ) : (
        <EmptyState
          title="No claims match"
          description="Try clearing the search or status filter."
        />
      )}
    </>
  );
}
