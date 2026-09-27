import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { Button, Card, ErrorState, LoadingState, PageHeader, StatusBadge } from "../components/ui";
import { api } from "../services/api";
import { useSession } from "../services/session";
import type { Claim } from "../types/api";

export function ClaimFacts({ claim }: { claim: Claim }) {
  const facts: [string, string | number | boolean | null][] = [
    ["Policy ID", claim.policy_id], ["Customer ID", claim.customer_id],
    ["Incident type", claim.incident_type], ["Collision type", claim.collision_type],
    ["Incident date", claim.incident_date], ["Location", claim.incident_location],
    ["Claim amount", Number(claim.total_claim_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })],
    ["Severity", claim.incident_severity], ["Authorities contacted", claim.authorities_contacted],
    ["State", claim.incident_state], ["City", claim.incident_city],
    ["Incident hour", claim.incident_hour_of_the_day], ["Vehicles involved", claim.number_of_vehicles_involved],
    ["Property damage", claim.property_damage], ["Bodily injuries", claim.bodily_injuries],
    ["Witnesses", claim.witnesses], ["Police report available", claim.police_report_available],
  ];
  return <Card>
    <div className="grid gap-6 sm:grid-cols-2">
      {facts.map(([label, value]) => <div key={label}>
        <p className="text-xs uppercase tracking-[0.13em] text-muted">{label}</p>
        <p className="mt-1 text-sm font-semibold text-ink">{value === null ? "Not provided" : typeof value === "boolean" ? value ? "Yes" : "No" : value}</p>
      </div>)}
    </div>
    <div className="mt-8 border-t border-line pt-6"><p className="eyebrow">Description</p>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-ink/80">{claim.claim_description}</p></div>
  </Card>;
}

export function ClaimDetails() {
  const location = useLocation();
  const { claimId } = useParams();
  const { session } = useSession();
  const [claim, setClaim] = useState<Claim | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    setClaim(null); setError("");
    if (claimId && session) api.getClaim(claimId).then((item) => {
      if (cancelled) return;
      if (item.customer_id !== session.customerId) setError("This claim is not available in your workspace.");
      else setClaim(item);
    }).catch((err: Error) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [claimId, session?.customerId]);
  if (error) return <ErrorState message={error} />;
  if (!claim) return <LoadingState label="Loading claim..." />;
  return <>
    {location.state?.submitted && <p role="status" className="mb-5 rounded-xl border border-teal/20 bg-mint/20 p-4 text-sm text-teal">Claim submitted successfully. Your report is now in the queue.</p>}
    <PageHeader eyebrow="Claim details" title={claim.claim_id}
      description={`Submitted ${new Date(claim.created_at).toLocaleString()}`}
      action={<Link to="/client/claims"><Button><ArrowLeft size={17} />Back to claims</Button></Link>} />
    <div className="mb-5"><StatusBadge status={claim.status} /></div>
    <ClaimFacts claim={claim} />
  </>;
}
