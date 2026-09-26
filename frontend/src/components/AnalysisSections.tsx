import type { ClaimAnalysis } from "../types/api";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="mt-6 border-t border-line pt-5"><h3 className="eyebrow">{title}</h3><div className="mt-3 text-sm leading-6 text-ink/80">{children}</div></section>;
}
function Items({ items }: { items?: string[] }) {
  return items?.length ? <ul className="list-disc space-y-2 pl-5">{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
    : <p className="text-muted">{items ? "None reported." : "Not returned by the analysis service."}</p>;
}
export function AnalysisSections({ analysis }: { analysis: ClaimAnalysis }) {
  const { fraud_analysis: fraud, nlp_analysis: nlp, policy_checks: checks, policy_analysis: policy } = analysis;
  const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
  return <>
    {analysis.created_at && <p className="mt-4 text-xs text-muted">Generated {new Date(analysis.created_at).toLocaleString()}</p>}
    <Section title="Fraud risk"><p>Probability: {percent(fraud.probability)}</p><p>Prediction: {fraud.prediction}</p></Section>
    <Section title="Incident classification"><p>Submitted: {nlp.submitted_incident_type}</p><p>Predicted: {nlp.predicted_incident_type}</p>
      <p>Confidence: {percent(nlp.confidence)}</p><p>{nlp.incident_type_match ? "Match" : "Mismatch"}</p></Section>
    <Section title="Policy checks">
      <dl className="grid gap-3 sm:grid-cols-2">{([
        ["Policy active", checks.policy_active], ["Within policy period", checks.incident_within_policy_period],
        ["Within coverage limit", checks.within_coverage_limit], ["Vehicle matches policy", checks.vehicle_matches_policy],
        ["Claim amount", checks.claim_amount], ["Coverage limit", checks.coverage_limit],
        ["Deductible", checks.deductible], ["Amount after deductible", checks.amount_after_deductible],
      ] as [string, number | boolean][]).map(([label, value]) => <div key={label}><dt className="text-xs text-muted">{label}</dt>
        <dd className="font-semibold">{typeof value === "boolean" ? value ? "Yes" : "No" : value.toLocaleString()}</dd></div>)}</dl>
      <p className="mb-2 mt-4 font-semibold">Issues</p><Items items={checks.issues} />
    </Section>
    <Section title="Summary"><p>{policy.summary}</p></Section>
    <Section title="Coverage analysis">{policy.coverage_analysis ? <><p className="font-semibold">{policy.coverage_analysis.status.replaceAll("_", " ")}</p><p>{policy.coverage_analysis.reasoning}</p></> : <p>Not returned by the analysis service.</p>}</Section>
    <Section title="Policy requirements">{policy.policy_requirements?.length ? policy.policy_requirements.map((item, i) => <div className="mb-3 rounded-xl bg-paper p-3" key={i}><p className="font-semibold">{item.requirement}</p><p>{item.status.replaceAll("_", " ")}</p><p>{item.reasoning}</p></div>) : <Items items={policy.policy_requirements ? [] : undefined} />}</Section>
    <Section title="Discrepancies">{policy.discrepancies?.length ? policy.discrepancies.map((item, i) => <div className="mb-3" key={i}><p className="font-semibold">{item.issue}</p><p>{item.significance}</p></div>) : <Items items={policy.discrepancies ? [] : undefined} />}</Section>
    <Section title="Missing information"><Items items={policy.missing_information} /></Section>
    <Section title="Risk indicators"><Items items={policy.risk_indicators} /></Section>
    <Section title="Recommended human review"><p>{policy.recommended_review ?? "Not returned by the analysis service."}</p></Section>
  </>;
}
