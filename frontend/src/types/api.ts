export type Role = "client" | "employee";

export interface SimilarClaimsResponse {
  claim_id: string;
  similar_claims: {
    claim_id: string;
    similarity_score: number;
    description_similarity: number;
    reasons: string[];
  }[];
}

export interface Claim {
  claim_id: string;
  customer_id: string;
  policy_id: string;
  incident_date: string;
  incident_type: string;
  collision_type: string | null;
  incident_severity: string | null;
  authorities_contacted: string | null;
  incident_state: string | null;
  incident_city: string | null;
  incident_hour_of_the_day: number | null;
  incident_location: string;
  number_of_vehicles_involved: number;
  property_damage: boolean | null;
  bodily_injuries: number;
  witnesses: number;
  police_report_available: boolean | null;
  total_claim_amount: string;
  claim_description: string;
  status: string;
  created_at: string;
}

export interface ClaimFilters {
  status?: string;
  customer_id?: string;
  limit?: number;
}

// Matches ClaimCreate in backend/app/schemas.py. Dates are YYYY-MM-DD.
// Counts must be nonnegative integers; hour is 0–23; amount must be positive.
export interface ClaimCreatePayload {
  customer_id: string;
  policy_id: string;
  incident_date: string;
  incident_type: string;
  collision_type?: string | null;
  incident_severity?: string | null;
  authorities_contacted?: string | null;
  incident_state?: string | null;
  incident_city?: string | null;
  incident_hour_of_the_day?: number | null;
  incident_location: string;
  number_of_vehicles_involved: number;
  property_damage?: boolean | null;
  bodily_injuries: number;
  witnesses: number;
  police_report_available?: boolean | null;
  total_claim_amount: string | number;
  claim_description: string;
}

// ClaimPatch accepts null for every field; the current backend ignores null updates.
export type ClaimUpdate = {
  [K in keyof ClaimCreatePayload]?: ClaimCreatePayload[K] | null;
} & { status?: string | null };

export interface FraudAnalysis {
  prediction: number;
  probability: number;
}

export interface NlpAnalysis {
  submitted_incident_type: string;
  predicted_incident_type: string;
  confidence: number;
  incident_type_match: boolean;
}

export interface PolicyChecks {
  policy_active: boolean;
  incident_within_policy_period: boolean;
  within_coverage_limit: boolean;
  vehicle_matches_policy: boolean;
  claim_amount: number;
  coverage_limit: number;
  deductible: number;
  amount_after_deductible: number;
  issues: string[];
}

export interface CoverageAnalysis {
  status: string;
  reasoning: string;
}

export interface PolicyRequirement {
  requirement: string;
  status: string;
  reasoning: string;
}

export interface PolicyDiscrepancy {
  issue: string;
  significance: string;
}

export interface RetrievedPolicyChunk {
  product_code: string | null;
  source: string | null;
  chunk_index: number | null;
}

export interface PolicyAnalysis {
  summary: string;
  // The backend's invalid-JSON fallback omits these sections and includes raw_response.
  coverage_analysis?: CoverageAnalysis;
  policy_requirements?: PolicyRequirement[];
  discrepancies?: PolicyDiscrepancy[];
  missing_information?: string[];
  risk_indicators?: string[];
  recommended_review?: string;
  retrieved_policy_chunks: RetrievedPolicyChunk[];
  raw_response?: string;
}

export interface ClaimAnalysis {
  // POST /analyze omits stored-record metadata; GET /analysis includes it.
  analysis_id?: string;
  claim_id: string;
  fraud_analysis: FraudAnalysis;
  nlp_analysis: NlpAnalysis;
  policy_checks: PolicyChecks;
  policy_analysis: PolicyAnalysis;
  created_at?: string;
}

export interface StoredClaimAnalysis extends ClaimAnalysis {
  analysis_id: string;
  created_at: string;
}

// These routes currently return a placeholder, not claims or history events.
export interface NotImplementedResponse {
  detail: string;
}

export type ReviewAction = "start_review" | "approve" | "reject" | "request_information" | "investigate" | "close";

export interface ReviewActionResponse {
  claim_id: string;
  action: ReviewAction;
  old_status: string;
  new_status: string;
  history_id: number;
}

export interface HistoryEvent {
  history_id: number;
  claim_id: string;
  action: string;
  old_status: string | null;
  new_status: string;
  note: string | null;
  actor_type: string;
  actor_id: string | null;
  created_at: string;
}

export interface ApiErrorShape {
  error?: { code?: string; message?: string; details?: unknown };
  detail?: string | Array<{ loc?: (string | number)[]; msg: string; type?: string }>;
}
