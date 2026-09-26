import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { Button, EmptyState, PageHeader } from "../components/ui";
export function InvestigationHistory() {
  const { claimId } = useParams();
  return <>
    <PageHeader eyebrow="Audit trail" title="Investigation history"
      action={<Link to={`/employee/claims/${encodeURIComponent(claimId ?? "")}`}><Button><ArrowLeft size={17} />Back to claim</Button></Link>} />
    <EmptyState title="History is not available yet" description="The current service does not provide investigation history." />
  </>;
}
