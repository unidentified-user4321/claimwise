import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { SimilarClaimsResponse } from "../types/api";
import { Card, ErrorState, LoadingState } from "./ui";

export function SimilarClaims({ claimId }: { claimId: string }) {
  const [result, setResult] = useState<SimilarClaimsResponse | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let cancelled = false;
    setResult(null); setError("");
    api.getSimilarClaims(claimId).then(data => {
      if (!cancelled) setResult(data);
    }).catch((err: unknown) => {
      if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load similar claims.");
    });
    return () => { cancelled = true; };
  }, [claimId, attempt]);
  return <Card>
    <h2 className="font-display text-lg font-semibold">Similar Claims</h2>
    <p className="mt-2 text-sm text-muted">Potentially related incidents for analyst review. Similarity is not a fraud decision.</p>
    <div className="mt-5">
      {error ? <ErrorState message={error} onRetry={() => setAttempt(value => value + 1)} />
        : !result ? <LoadingState label="Finding similar claims..." />
        : !result.similar_claims.length ? <p className="text-sm text-muted">No similar claims detected.</p>
        : <ul className="space-y-5">{result.similar_claims.map(match => <li key={match.claim_id} className="border-b border-line pb-4 last:border-0">
          <div className="flex flex-wrap justify-between gap-2 text-sm font-semibold">
            <Link className="text-teal underline" to={`/employee/claims/${encodeURIComponent(match.claim_id)}`}>{match.claim_id}</Link>
            <span>{Math.round(match.similarity_score * 100)}% similarity</span>
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">{match.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
        </li>)}</ul>}
    </div>
  </Card>;
}
