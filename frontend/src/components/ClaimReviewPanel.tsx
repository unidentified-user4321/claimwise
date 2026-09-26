import { History } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import type { Claim, HistoryEvent, ReviewAction } from "../types/api";
import { Button, Card, ErrorState, Field, LoadingState, Textarea } from "./ui";

// Presentation only: the server validates every requested action.
const visibleActions: Record<string, ReviewAction[]> = {
  submitted: ["start_review"],
  under_review: ["request_information", "investigate", "approve", "reject"],
  approved: ["close"],
  rejected: ["close"],
  closed: [],
};
const noteRequired = new Set<ReviewAction>(["reject", "request_information", "investigate"]);
function label(value: string) {
  return value.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

export function ClaimReviewPanel({ claim, onClaimUpdated }: {
  claim: Claim;
  onClaimUpdated: (claim: Claim) => void;
}) {
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  const [refreshError, setRefreshError] = useState("");
  const running = useRef(false);
  const version = useRef(0);
  const actions = visibleActions[claim.status] ?? [];

  useEffect(() => {
    const current = ++version.current;
    api.getHistory(claim.claim_id).then(rows => {
      if (current === version.current) setHistory(rows);
    }).catch((err: unknown) => {
      if (current === version.current) setHistoryError(err instanceof Error ? err.message : "Unable to load history.");
    }).finally(() => {
      if (current === version.current) setHistoryLoading(false);
    });
    return () => { version.current++; };
  }, [claim.claim_id]);

  async function refresh(current: number) {
    setHistoryLoading(true); setHistoryError(""); setRefreshError("");
    const [claimResult, historyResult] = await Promise.allSettled([
      api.getClaim(claim.claim_id), api.getHistory(claim.claim_id),
    ]);
    if (current !== version.current) return;
    if (claimResult.status === "fulfilled") onClaimUpdated(claimResult.value);
    else setRefreshError(`Unable to refresh current status. ${claimResult.reason instanceof Error ? claimResult.reason.message : "Please try again."}`);
    if (historyResult.status === "fulfilled") setHistory(historyResult.value);
    else setHistoryError(historyResult.reason instanceof Error ? historyResult.reason.message : "Unable to load history.");
    setHistoryLoading(false);
  }

  async function retryRefresh() {
    if (running.current) return;
    const current = version.current;
    running.current = true; setBusy(true);
    try { await refresh(current); }
    finally { if (current === version.current) { running.current = false; setBusy(false); } }
  }

  async function submit(action: ReviewAction) {
    if (running.current) return;
    setError(""); setSuccess("");
    if (noteRequired.has(action) && !note.trim()) {
      setError(`Please add a note for ${label(action).toLowerCase()}.`);
      return;
    }
    const current = version.current;
    running.current = true; setBusy(true);
    try {
      await api.reviewClaim(claim.claim_id, action, note.trim() || null);
      if (current !== version.current) return;
      setNote(""); setSuccess(`${label(action)} recorded successfully.`);
      await refresh(current);
    } catch (err) {
      if (current === version.current) setError(err instanceof Error ? err.message : "Unable to record review action.");
    } finally {
      if (current === version.current) { running.current = false; setBusy(false); }
    }
  }

  return <>
    <Card>
      <h2 className="font-display text-lg font-semibold">Reviewer Actions</h2>
      <p className="mt-3 text-sm text-muted">Current Status: <span className="font-semibold text-ink">{label(claim.status)}</span></p>
      {actions.length ? <>
        <div className="mt-5"><Field label="Note" hint="Required for reject, information requests, and investigation">
          <Textarea value={note} disabled={busy} onChange={event => setNote(event.target.value)} />
        </Field></div>
        <div className="mt-5 grid gap-2">
          {actions.map(action => <Button key={action} disabled={busy || historyLoading || !!refreshError}
            className={action === "approve" || action === "start_review" ? "button-dark" : ""}
            onClick={() => void submit(action)}>{action === "close" ? "Close Claim" : label(action)}</Button>)}
        </div>
      </> : <p className="mt-5 text-sm text-muted">No reviewer actions available for this claim.</p>}
      {busy && <p role="status" className="mt-3 text-sm text-muted">Processing...</p>}
      {error && <p role="alert" className="mt-3 text-sm text-coral">{error}</p>}
      {success && <p role="status" className="mt-3 text-sm text-teal">{success}</p>}
      {refreshError && <div className="mt-3"><ErrorState message={refreshError} onRetry={() => void retryRefresh()} /></div>}
    </Card>
    <Card>
      <div className="flex items-center gap-3"><History size={18} /><h2 className="font-display text-lg font-semibold">Claim History</h2></div>
      <div className="mt-5">
        {historyLoading ? <LoadingState label="Loading claim history..." /> : historyError
          ? <ErrorState message={historyError} onRetry={() => void retryRefresh()} />
          : history.length === 0 ? <p className="text-sm text-muted">No claim history yet.</p>
          : <ol className="space-y-5">{history.map(entry => <li key={entry.history_id} className="border-b border-line pb-5 last:border-0 last:pb-0">
            <p className="text-sm font-semibold">{label(entry.action)}</p>
            <p className="mt-1 text-sm text-muted">{entry.old_status ? label(entry.old_status) : "Not set"} → {label(entry.new_status)}</p>
            {entry.note && <p className="mt-2 whitespace-pre-wrap break-words text-sm">{entry.note}</p>}
            <p className="mt-2 text-xs text-muted">{label(entry.actor_type)}{entry.actor_id ? ` (${entry.actor_id})` : ""}</p>
            <time dateTime={entry.created_at} className="mt-1 block text-xs text-muted">{new Date(entry.created_at).toLocaleString()}</time>
          </li>)}</ol>}
      </div>
    </Card>
  </>;
}
