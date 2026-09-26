import { ArrowLeft, BrainCircuit } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ClaimFacts } from "./ClaimDetails";
import { Button, Card, ErrorState, LoadingState, PageHeader, StatusBadge } from "../components/ui";
import { ClaimReviewPanel } from "../components/ClaimReviewPanel";
import { SimilarClaims } from "../components/SimilarClaims";
import { AnalysisSections } from "../components/AnalysisSections";
import { ApiError, api } from "../services/api";
import type { Claim, ClaimAnalysis } from "../types/api";

export function EmployeeClaimDetails() {
  const { claimId } = useParams();
  const [claim, setClaim] = useState<Claim | null>(null);
  const [analysis, setAnalysis] = useState<ClaimAnalysis | null>(null);
  const [error, setError] = useState("");
  const [analysisError, setAnalysisError] = useState("");
  const [analysisLoading, setAnalysisLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const running = useRef(false);
  const version = useRef(0);
  useEffect(() => {
    const current = ++version.current;
    setClaim(null); setAnalysis(null); setError(""); setAnalysisError(""); setAnalysisLoading(true);
    setAnalyzing(false); running.current = false;
    async function load() {
      if (!claimId) return;
      try {
        const item = await api.getClaim(claimId);
        if (current !== version.current) return;
        setClaim(item);
        try {
          const result = await api.getClaimAnalysis(claimId);
          if (current === version.current) setAnalysis(result);
        } catch (err) {
          if (current === version.current && !(err instanceof ApiError && err.status === 404)) {
            setAnalysisError(err instanceof Error ? err.message : "Unable to load analysis.");
          }
        }
      } catch (err) {
        if (current === version.current) setError(err instanceof Error ? err.message : "Unable to load claim.");
      } finally { if (current === version.current) setAnalysisLoading(false); }
    }
    void load();
    return () => { version.current++; };
  }, [claimId]);
  async function runAnalysis() {
    if (!claimId || running.current) return;
    const current = version.current;
    running.current = true; setAnalyzing(true); setAnalysisError("");
    try {
      const result = await api.analyzeClaim(claimId);
      if (current === version.current) setAnalysis(result);
    } catch (err) {
      if (current === version.current) setAnalysisError(err instanceof ApiError && err.status === 429
        ? "Analysis quota or rate limit reached. Please try again later."
        : err instanceof Error ? err.message : "Unable to analyze claim.");
    } finally {
      if (current === version.current) { running.current = false; setAnalyzing(false); }
    }
  }
  if (error) return <ErrorState message={error} />;
  if (!claim) return <LoadingState label="Loading claim review..." />;
  return <>
    <PageHeader eyebrow="Employee review" title={claim.claim_id}
      description={`Submitted ${new Date(claim.created_at).toLocaleString()}`}
      action={<Link to="/employee/claims"><Button><ArrowLeft size={17} />Back to queue</Button></Link>} />
    <div className="mb-6 flex flex-wrap items-center gap-3"><StatusBadge status={claim.status} />
      <span className="font-mono text-xs text-muted">Customer {claim.customer_id}</span></div>
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-6">
        <ClaimFacts claim={claim} />
        <Card>
          <div className="flex items-center gap-3"><span className="section-icon"><BrainCircuit size={18} /></span>
            <h2 className="font-display text-lg font-semibold">AI analysis</h2></div>
          <p className="mt-4 rounded-xl border border-amber/20 bg-amber/5 p-4 text-xs leading-5 text-amber">
            Decision support only. AI output is not a final insurance decision. A human claims analyst remains responsible for the final decision.
          </p>
          {analysisLoading ? <LoadingState label="Loading stored analysis..." /> : <>
            {!analysis && !analysisError && <p className="mt-5 text-sm text-muted">Analysis not generated yet</p>}
            {analysisError && <div className="mt-5"><ErrorState message={analysisError} /></div>}
            <Button className="button-dark mt-5 w-full" disabled={analyzing} onClick={runAnalysis}>
              <BrainCircuit size={17} />{analyzing ? "Analyzing claim..." : analysis ? "Refresh analysis" : "Run analysis"}
            </Button>
            {analysis && <AnalysisSections analysis={analysis} />}
          </>}
        </Card>
      </div>
      <div className="space-y-6">
        <ClaimReviewPanel key={claim.claim_id} claim={claim} onClaimUpdated={setClaim} />
        <SimilarClaims key={`similar-${claim.claim_id}`} claimId={claim.claim_id} />
      </div>
    </div>
  </>;
}
