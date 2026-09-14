// Real client for the API routes wired up in services/api/main.py. No mock
// JSON -- every call here hits a live endpoint and returns (or throws) the
// actual response.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// One real past requirement that was pulled in as few-shot context before
// this assessment was made, plus its real stored outcome. Backed by
// TF-IDF cosine similarity over stored requirement text (see
// packages/kg-client/similarity.py) -- NOT a vector-embedding search and
// NOT model fine-tuning/training. review_decision is null when Module 3
// hasn't reviewed that past requirement's tests yet -- never guessed.
export interface SimilarRequirementMatch {
  requirement_id: string
  requirement_text: string
  similarity: number
  risk_level: string
  review_decision: 'approved' | 'rejected' | null
}

// What retrieval-based memory actually did for one /assess call. An empty
// similar_requirements list is the honest, common case (e.g. the first
// requirement ever assessed for a tenant) -- not an error.
export interface RetrievalContext {
  similarity_threshold: number
  similar_requirements: SimilarRequirementMatch[]
}

export interface RiskAssessmentOutput {
  requirement_id: string
  risk_score: number
  risk_level: string
  risk_rationale: string
  risk_factors: string[]
  confidence: number
  citation_ids: string[]
  // Only present on the real /assess response (services/api/main.py's
  // AssessResponse) -- optional here so this interface still matches the
  // bare RiskAssessmentOutput shape used internally (e.g. inside
  // TestGenerationInput's risk_assessment) where retrieval isn't relevant.
  retrieval?: RetrievalContext
}

export interface GeneratedTestCase {
  title: string
  description: string
  steps: string[]
  expected_result: string
  test_type: string
  priority: string
}

export interface TestGenerationOutput {
  requirement_id: string
  test_cases: GeneratedTestCase[]
  generation_confidence: number
}

// A test case as read back from the KG via GET /requirements/{id}/tests --
// includes the KG-assigned id (which TestGenerationOutput above does not
// carry) plus its current human review status.
export interface TestCaseWithReview {
  id: string
  title: string
  description: string
  steps: string[]
  expected_result: string
  test_type: string
  priority: string
  status: 'draft' | 'approved' | 'rejected' | string
  reviewer_id: string | null
  review_note: string | null
}

export interface RequirementTestsResponse {
  requirement_id: string
  test_cases: TestCaseWithReview[]
}

export interface TestCaseReviewResponse {
  test_case_id: string
  requirement_id: string
  status: string
  reviewer_id: string
  note: string | null
  review_request_id: string
}

// One real logged entry from CostLedger (packages/llm-gateway-client/ledger.py)
// -- one per real LLM call made through extraction/backbone.py. Token counts
// and estimated_cost_usd are null (not 0) whenever the provider response
// didn't report usage, or the model isn't in the hardcoded pricing table --
// this UI must render that as "unknown", never as a guessed number.
export interface CostLedgerEntry {
  id: string
  tenant_id: string
  requirement_id: string | null
  model: string
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  usage_reported: boolean
  estimated_cost_usd: number | null
  cost_basis: string | null
  timestamp: string
}

export interface RequirementCostResponse {
  requirement_id: string
  entries: CostLedgerEntry[]
  total_prompt_tokens: number | null
  total_completion_tokens: number | null
  total_estimated_cost_usd: number | null
}

// One real KG node (GET /requirements/{id}/graph) -- `properties` is the
// full, unfiltered dict actually stored for that node (tenant_id included),
// so the graph page's node-click panel can show exactly what's real.
export interface GraphNode {
  id: string
  label: string
  properties: Record<string, unknown>
}

// There is no real edge store yet (see kg-client/stub.py) -- `type` is the
// server's inference of which foreign-key-style field matched, not a
// hardcoded per-label guess. See services/api/main.py's get_requirement_graph.
export interface GraphEdge {
  source: string
  target: string
  type: string
}

export interface RequirementGraphResponse {
  requirement_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (err) {
    // The API being unreachable (not running, wrong NEXT_PUBLIC_API_URL) is
    // a distinct, common case worth a clear message rather than a generic
    // "fetch failed".
    throw new ApiError(
      `Could not reach the API at ${API_BASE}. Is services/api running (uv run uvicorn main:app)?`,
      0,
    )
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(body.detail || `Request failed with status ${res.status}`, res.status)
  }
  return res.json()
}

async function get<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, { method: 'GET' })
  } catch (err) {
    throw new ApiError(
      `Could not reach the API at ${API_BASE}. Is services/api running (uv run uvicorn main:app)?`,
      0,
    )
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(body.detail || `Request failed with status ${res.status}`, res.status)
  }
  return res.json()
}

export const api = {
  /** POST /requirements/{id}/assess -- Module 1, real LLM call, real KG persist. */
  assessRequirement(
    requirementId: string,
    tenantId: string,
    requirementText: string,
    sourceTool: string = 'manual',
  ): Promise<RiskAssessmentOutput> {
    return post(`/requirements/${encodeURIComponent(requirementId)}/assess`, {
      tenant_id: tenantId,
      requirement_text: requirementText,
      source_tool: sourceTool,
    })
  },

  /** POST /requirements/{id}/generate-tests -- Module 2, reads the risk
   *  assessment back out of the KG (not resent from the client). */
  generateTests(requirementId: string, tenantId: string): Promise<TestGenerationOutput> {
    return post(`/requirements/${encodeURIComponent(requirementId)}/generate-tests`, {
      tenant_id: tenantId,
    })
  },

  /** GET /requirements/{id}/tests -- reads generated test cases + their
   *  current review status back out of the KG (not client-side state). */
  listRequirementTests(requirementId: string, tenantId: string): Promise<RequirementTestsResponse> {
    const qs = new URLSearchParams({ tenant_id: tenantId })
    return get(`/requirements/${encodeURIComponent(requirementId)}/tests?${qs.toString()}`)
  },

  /** GET /requirements/{id}/cost -- real logged token/cost entries from
   *  CostLedger for every real LLM call made while assessing/generating
   *  tests for this requirement. Not computed client-side -- this is a
   *  direct read of what the server actually logged. */
  getRequirementCost(requirementId: string, tenantId: string): Promise<RequirementCostResponse> {
    const qs = new URLSearchParams({ tenant_id: tenantId })
    return get(`/requirements/${encodeURIComponent(requirementId)}/cost?${qs.toString()}`)
  },

  /** GET /requirements/{id}/graph -- real nodes + edges for one requirement,
   *  read live from the KG (Requirement, its RiskAssessment, its TestCases,
   *  each with real stored properties). Not a static/sample graph. */
  getRequirementGraph(requirementId: string, tenantId: string): Promise<RequirementGraphResponse> {
    const qs = new URLSearchParams({ tenant_id: tenantId })
    return get(`/requirements/${encodeURIComponent(requirementId)}/graph?${qs.toString()}`)
  },

  /** POST /requirements/{id}/tests/{test_case_id}/review -- Module 3
   *  (HumanReviewGate). Persists the decision to the KG; callers should
   *  re-read via listRequirementTests() rather than trust this response
   *  alone as the source of truth for UI state. */
  reviewTestCase(
    requirementId: string,
    testCaseId: string,
    tenantId: string,
    reviewerId: string,
    decision: 'approved' | 'rejected',
    note?: string,
  ): Promise<TestCaseReviewResponse> {
    return post(
      `/requirements/${encodeURIComponent(requirementId)}/tests/${encodeURIComponent(testCaseId)}/review`,
      {
        tenant_id: tenantId,
        reviewer_id: reviewerId,
        decision,
        note: note && note.trim().length > 0 ? note : null,
      },
    )
  },
}
