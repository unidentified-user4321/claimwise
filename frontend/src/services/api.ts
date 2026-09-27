import type {
  ApiErrorShape,
  Claim,
  SimilarClaimsResponse,
  ClaimAnalysis,
  ClaimCreatePayload,
  ClaimFilters,
  ClaimUpdate,
  HistoryEvent,
  ReviewAction,
  ReviewActionResponse,
  NotImplementedResponse,
  AuthUser,
  StoredClaimAnalysis,
} from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");

let getSessionToken: (() => Promise<string | null>) | undefined;
export function setTokenGetter(getter?: () => Promise<string | null>) { getSessionToken = getter; }

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  const headers = new Headers(options.headers);
  if (options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const sentToken = await getSessionToken?.();
  if (sentToken) headers.set("Authorization", `Bearer ${sentToken}`);
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("The backend could not be reached. Check that the API is running.", 0);
  }

  if (!response.ok) {
    let payload: ApiErrorShape = {};
    try {
      const parsed: unknown = await response.json();
      if (parsed && typeof parsed === "object") payload = parsed as ApiErrorShape;
    } catch {
      // Preserve the HTTP status even when the backend does not return JSON.
    }
    const detail = typeof payload.detail === "string"
      ? payload.detail
      : Array.isArray(payload.detail)
        ? payload.detail.map((item) => `${item.loc?.join(".") ?? "Request"}: ${item.msg}`).join("; ")
        : undefined;
    const fallback = response.status === 429
      ? "Analysis quota or rate limit reached. Please try again later."
      : `Request failed (${response.status})`;
    throw new ApiError(payload.error?.message ?? detail ?? fallback, response.status,
      payload.error?.details ?? payload.detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function claimPath(claimId: string): string {
  return `/claims/${encodeURIComponent(claimId)}`;
}

export const api = {
  linkCustomer: (customer_id: string) =>
    request<AuthUser>("/auth/link", { method: "POST", body: JSON.stringify({ customer_id }) }),
  me: () => request<AuthUser>("/auth/me"),
  listClaims: (filters: ClaimFilters = {}): Promise<Claim[]> => {
    const params = new URLSearchParams();
    if (filters.status !== undefined) params.set("status", filters.status);
    if (filters.customer_id !== undefined) params.set("customer_id", filters.customer_id);
    if (filters.limit !== undefined) params.set("limit", String(filters.limit));
    const query = params.toString();
    return request<Claim[]>(`/claims${query ? `?${query}` : ""}`);
  },
  getClaim: (claimId: string) => request<Claim>(claimPath(claimId)),
  getSimilarClaims: (claimId: string) =>
    request<SimilarClaimsResponse>(`${claimPath(claimId)}/similar`),
  createClaim: (payload: ClaimCreatePayload) =>
    request<Claim>("/claims", { method: "POST", body: JSON.stringify(payload) }),
  updateClaim: (claimId: string, payload: ClaimUpdate) =>
    request<Claim>(claimPath(claimId), { method: "PATCH", body: JSON.stringify(payload) }),
  getClaimAnalysis: (claimId: string) =>
    request<StoredClaimAnalysis>(`${claimPath(claimId)}/analysis`),
  analyzeClaim: (claimId: string) =>
    request<ClaimAnalysis>(`${claimPath(claimId)}/analyze`, { method: "POST" }),
  getHistory: (claimId: string) =>
    request<HistoryEvent[]>(`${claimPath(claimId)}/history`),
  reviewClaim: (claimId: string, action: ReviewAction, note: string | null) =>
    request<ReviewActionResponse>(`${claimPath(claimId)}/review-action`, {
      method: "POST", body: JSON.stringify({ action, note }),
    }),
  updateStatus: (claimId: string, _status: string, _employeeId: string, _comment?: string) =>
    request<NotImplementedResponse>(`${claimPath(claimId)}/status`, { method: "PATCH" }),
};
