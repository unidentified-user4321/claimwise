import { ArrowLeft, ArrowRight, FilePlus2 } from "lucide-react";
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Card, ErrorState, Field, Input, PageHeader, Select, Textarea } from "../components/ui";
import { api } from "../services/api";
import { useSession } from "../services/session";
import type { ClaimCreatePayload } from "../types/api";

const initialForm = {
  policy_id: "", incident_type: "", collision_type: "", incident_date: "", incident_location: "",
  number_of_vehicles_involved: "", bodily_injuries: "", witnesses: "", total_claim_amount: "",
  claim_description: "", incident_severity: "", authorities_contacted: "", incident_state: "",
  incident_city: "", incident_hour_of_the_day: "", property_damage: "", police_report_available: "",
};
type FormKey = keyof typeof initialForm;
const fields: { name: FormKey; label: string; type?: string; required?: boolean; min?: string; max?: string; step?: string }[] = [
  { name: "policy_id", label: "Policy ID", required: true },
  { name: "incident_type", label: "Incident type", required: true },
  { name: "incident_date", label: "Incident date", type: "date", required: true },
  { name: "incident_location", label: "Incident location", required: true },
  { name: "number_of_vehicles_involved", label: "Vehicles involved", type: "number", min: "0", step: "1", required: true },
  { name: "bodily_injuries", label: "Bodily injuries", type: "number", min: "0", step: "1", required: true },
  { name: "witnesses", label: "Witnesses", type: "number", min: "0", step: "1", required: true },
  { name: "total_claim_amount", label: "Claim amount", type: "number", min: "0.01", step: "0.01", required: true },
  { name: "collision_type", label: "Collision type" },
  { name: "incident_severity", label: "Incident severity" },
  { name: "authorities_contacted", label: "Authorities contacted" },
  { name: "incident_state", label: "State" },
  { name: "incident_city", label: "City" },
  { name: "incident_hour_of_the_day", label: "Incident hour (0–23)", type: "number", min: "0", max: "23", step: "1" },
];
export function SubmitClaim() {
  const navigate = useNavigate();
  const { session } = useSession();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const pending = useRef(false);
  const update = (name: FormKey, value: string) => setForm((current) => ({ ...current, [name]: value }));
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending.current || !session) return;
    if ([form.policy_id, form.incident_type, form.incident_location, form.claim_description].some((value) => !value.trim())) {
      setError("Please complete all required fields."); return;
    }
    pending.current = true; setSubmitting(true); setError("");
    const nullable = (value: string) => value.trim() || null;
    const boolean = (value: string) => value === "" ? null : value === "yes";
    const payload: ClaimCreatePayload = {
      customer_id: session.userId, policy_id: form.policy_id.trim(), incident_type: form.incident_type.trim(),
      incident_date: form.incident_date, incident_location: form.incident_location.trim(),
      number_of_vehicles_involved: Number(form.number_of_vehicles_involved), bodily_injuries: Number(form.bodily_injuries),
      witnesses: Number(form.witnesses), total_claim_amount: form.total_claim_amount,
      claim_description: form.claim_description.trim(), collision_type: nullable(form.collision_type),
      incident_severity: nullable(form.incident_severity), authorities_contacted: nullable(form.authorities_contacted),
      incident_state: nullable(form.incident_state), incident_city: nullable(form.incident_city),
      incident_hour_of_the_day: form.incident_hour_of_the_day === "" ? null : Number(form.incident_hour_of_the_day),
      property_damage: boolean(form.property_damage), police_report_available: boolean(form.police_report_available),
    };
    try {
      const claim = await api.createClaim(payload);
      navigate(`/client/claims/${encodeURIComponent(claim.claim_id)}`, { state: { submitted: true }, replace: true });
    } catch (err) { setError(err instanceof Error ? err.message : "The claim could not be submitted."); }
    finally { pending.current = false; setSubmitting(false); }
  }
  return <>
    <PageHeader eyebrow="New claim" title="Tell us what happened."
      description="Share the incident details below. Keep your description factual and include what you know today."
      action={<Link to="/client"><Button><ArrowLeft size={17} />Back</Button></Link>} />
    <form onSubmit={submit} className="grid gap-6 lg:grid-cols-[1fr_0.65fr]">
      <Card className="space-y-6">
        <div className="flex items-center gap-3 border-b border-line pb-5"><span className="section-icon"><FilePlus2 size={18} /></span>
          <div><h2 className="font-display text-lg font-semibold">Incident details</h2><p className="text-sm text-muted">The basics help us route your claim.</p></div></div>
        <div className="grid gap-5 sm:grid-cols-2">
          {fields.map(({ name, label, required, ...props }) => <Field key={name} label={label} hint={required ? "Required" : "Optional"}>
            <Input {...props} required={required} value={form[name]} onChange={(e) => update(name, e.target.value)} />
          </Field>)}
          {([['property_damage', 'Property damage'], ['police_report_available', 'Police report available']] as [FormKey, string][]).map(([name, label]) => <Field key={name} label={label} hint="Optional">
            <Select value={form[name]} onChange={(e) => update(name, e.target.value)}><option value="">Unknown / not provided</option><option value="yes">Yes</option><option value="no">No</option></Select>
          </Field>)}
        </div>
      </Card>
      <div className="space-y-6">
        <Card><Field label="What happened?" hint="Required"><Textarea required value={form.claim_description} onChange={(e) => update("claim_description", e.target.value)} placeholder="Describe the incident, damage, and what happened next..." /></Field></Card>
        {error && <ErrorState message={error} />}
        <Card className="bg-ink text-white"><p className="eyebrow text-mint">Ready to submit?</p>
          <p className="mt-3 text-sm leading-6 text-white/60">Your report will be stored with <span className="font-mono text-white/80">{session?.userId}</span> as the customer.</p>
          <Button disabled={submitting} type="submit" className="mt-6 w-full bg-mint text-ink hover:bg-white">{submitting ? "Submitting..." : "Submit claim"}<ArrowRight size={17} /></Button>
        </Card>
      </div>
    </form>
  </>;
}
