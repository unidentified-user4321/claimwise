import { ArrowUpRight, CarFront } from "lucide-react";
import { Link } from "react-router-dom";
import type { Claim } from "../types/api";
import { StatusBadge } from "./ui";

export function ClaimRow({
  claim,
  basePath,
}: {
  claim: Claim;
  basePath: "/client" | "/employee";
}) {
  return (
    <Link
      to={`${basePath}/claims/${encodeURIComponent(claim.claim_id)}`}
      className="group grid grid-cols-[1fr_auto] gap-4 border-b border-line px-5 py-4 transition last:border-0 hover:bg-paper/70 md:grid-cols-[1.3fr_1fr_0.8fr_0.8fr_auto]"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-muted">
            {claim.claim_id}
          </span>
          <StatusBadge status={claim.status} />
        </div>
        <p className="mt-2 truncate font-semibold text-ink">
          {claim.incident_type}
        </p>
        <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
          <CarFront size={13} />
          {claim.incident_location}
        </p>
      </div>
      <div className="hidden self-center md:block">
        <p className="text-xs uppercase tracking-[0.14em] text-muted">
          Incident
        </p>
        <p className="mt-1 text-sm font-medium text-ink">
          {new Date(claim.incident_date).toLocaleDateString()}
        </p>
      </div>
      <div className="hidden self-center md:block">
        <p className="text-xs uppercase tracking-[0.14em] text-muted">Amount</p>
        <p className="mt-1 text-sm font-semibold text-ink">
          {Number(claim.total_claim_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
      </div>
      <div className="hidden self-center md:block">
        <p className="text-xs uppercase tracking-[0.14em] text-muted">
          Created
        </p>
        <p className="mt-1 text-sm font-medium text-ink">
          {claim.created_at && Number.isFinite(new Date(claim.created_at).getTime())
            ? new Date(claim.created_at).toLocaleDateString()
            : "Date unavailable"}
        </p>
      </div>
      <ArrowUpRight
        size={18}
        className="self-center text-muted transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-ink"
      />
    </Link>
  );
}

export function ClaimsTable({
  claims,
  basePath,
}: {
  claims: Claim[];
  basePath: "/client" | "/employee";
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-white">
      <div className="hidden grid-cols-[1.3fr_1fr_0.8fr_0.8fr_auto] gap-4 border-b border-line bg-paper px-5 py-3 text-[10px] font-bold uppercase tracking-[0.16em] text-muted md:grid">
        <span>Claim</span>
        <span>Incident</span>
        <span>Amount</span>
        <span>Created</span>
        <span />
      </div>
      {claims.map((claim) => (
        <ClaimRow key={claim.claim_id} claim={claim} basePath={basePath} />
      ))}
    </div>
  );
}
