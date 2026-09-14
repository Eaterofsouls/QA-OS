'use client'

import React, { useState } from 'react'
import { api, ApiError, RiskAssessmentOutput, TestGenerationOutput } from '../lib/api'
import { PendingReviews } from '../components/dashboard/PendingReviews'
import { CostReadout } from '../components/dashboard/CostReadout'

type RunState = 'idle' | 'assessing' | 'generating' | 'done' | 'error'

export default function CommandCenter() {
  const [requirementText, setRequirementText] = useState(
    'Users must be able to log in via OAuth2, including token refresh and session expiry handling.'
  )
  const [state, setState] = useState<RunState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [risk, setRisk] = useState<RiskAssessmentOutput | null>(null)
  const [tests, setTests] = useState<TestGenerationOutput | null>(null)

  // Lifted so the Pending Review panel (Module 3) can call
  // GET/POST /requirements/{id}/tests[/*/review] against the same
  // requirement + tenant this run just created.
  const [activeRequirementId, setActiveRequirementId] = useState<string | null>(null)
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null)
  const [reviewRefreshToken, setReviewRefreshToken] = useState(0)

  async function runVerticalSlice() {
    setError(null)
    setRisk(null)
    setTests(null)

    // Client-generated ids for this run -- a real system would issue these
    // from wherever the requirement originates (Jira, a doc, etc).
    const tenantId = crypto.randomUUID()
    const requirementId = `req-${Date.now()}`

    try {
      setState('assessing')
      const riskResult = await api.assessRequirement(requirementId, tenantId, requirementText)
      setRisk(riskResult)

      setState('generating')
      const testsResult = await api.generateTests(requirementId, tenantId)
      setTests(testsResult)

      // Only now do we point the Pending Review panel at this run -- it
      // reads test cases back from the KG itself rather than being handed
      // testsResult directly, same "don't trust client state" pattern the
      // backend already uses for the risk assessment in generate-tests.
      setActiveRequirementId(requirementId)
      setActiveTenantId(tenantId)
      setReviewRefreshToken((n) => n + 1)

      setState('done')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error running the pipeline.')
      setState('error')
    }
  }

  const isRunning = state === 'assessing' || state === 'generating'

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-10">
      <header className="flex justify-between items-center border-b-4 border-black pb-6">
        <div>
          <h1 className="text-4xl font-black uppercase tracking-tighter">Command Center</h1>
          <p className="text-black/70 mt-2 font-mono uppercase text-sm font-bold tracking-widest">Live Pipeline Tracker & Telemetry</p>
        </div>
        <div className="flex items-center gap-3 border-2 border-black px-4 py-2 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
          <div className="w-3 h-3 bg-black animate-pulse"></div>
          <span className="text-sm font-black uppercase tracking-widest">System Online</span>
        </div>
      </header>

      <div>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-lg font-black uppercase tracking-widest">Module Status</h2>
          <span className="text-xs font-mono font-bold uppercase text-black/40 tracking-widest">Demo layout &mdash; not wired to live state</span>
        </div>
        <div className="grid grid-cols-3 gap-8">
          <ModuleCard number={1} name="Risk Assessor" status={state === 'assessing' ? 'running' : 'idle'} />
          <ModuleCard number={2} name="Test Suite Gen" status={state === 'generating' ? 'running' : 'idle'} />
          <ModuleCard number={3} name="Review Gate" status="waiting" />
          <ModuleCard number={4} name="Orchestrator" status="idle" />
          <ModuleCard number={5} name="Defect Triage" status="idle" />
          <ModuleCard number={6} name="Readiness" status="idle" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8 mt-4">
        {/* REAL panel: calls the actual FastAPI routes wired in services/api/main.py */}
        <div className="mono-card p-8 flex flex-col gap-6">
          <div className="flex items-baseline justify-between border-b-2 border-black pb-2 gap-3">
            <h2 className="text-2xl font-black uppercase">Run Requirement Pipeline</h2>
            <div className="flex items-center gap-3 shrink-0">
              <CostReadout
                requirementId={activeRequirementId}
                tenantId={activeTenantId}
                refreshToken={reviewRefreshToken}
              />
              <span className="text-[10px] font-mono font-black uppercase text-black/50">Live &mdash; Modules 1+2</span>
            </div>
          </div>

          <textarea
            className="border-2 border-black p-3 font-mono text-sm min-h-[100px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
            value={requirementText}
            onChange={(e) => setRequirementText(e.target.value)}
            disabled={isRunning}
          />

          <button
            onClick={runVerticalSlice}
            disabled={isRunning || requirementText.trim().length === 0}
            className="border-2 border-black bg-black text-white font-black uppercase tracking-widest py-3 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:translate-x-0 disabled:hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
          >
            {state === 'assessing' && 'Assessing risk\u2026'}
            {state === 'generating' && 'Generating tests\u2026'}
            {(state === 'idle' || state === 'done' || state === 'error') && 'Assess & Generate Tests'}
          </button>

          {error && (
            <div className="border-2 border-black bg-black text-white p-3 font-mono text-sm font-bold">
              {error}
              {error.toLowerCase().includes('gateway') && (
                <div className="mt-2 font-normal text-white/80">
                  This means the LLM call itself failed &mdash; set LITELLM_BASE_URL / LITELLM_API_KEY
                  (or run <code>docker-compose up litellm</code>) and try again.
                </div>
              )}
            </div>
          )}

          {risk && (
            <div className="border-2 border-black p-4 bg-gray-50 flex flex-col gap-2">
              <h3 className="font-black uppercase text-sm tracking-widest">Risk Assessment</h3>
              <div className="flex items-center gap-3">
                <span className="px-2 py-1 bg-black text-white text-xs font-black uppercase">{risk.risk_level}</span>
                <span className="font-mono text-xs font-bold">score {risk.risk_score.toFixed(2)}</span>
                <span className="font-mono text-xs text-black/50">confidence {risk.confidence.toFixed(2)}</span>
              </div>
              <p className="text-sm">{risk.risk_rationale}</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {risk.risk_factors.map((f) => (
                  <span key={f} className="text-[10px] font-mono font-bold border border-black px-2 py-0.5 uppercase">{f}</span>
                ))}
              </div>
              {risk.retrieval && risk.retrieval.similar_requirements.length > 0 && (
                <div
                  className="mt-2 border-t-2 border-black/10 pt-2 text-xs font-mono"
                  title={risk.retrieval.similar_requirements
                    .map(
                      (m) =>
                        `"${m.requirement_text}" -- risk_level ${m.risk_level}, ${
                          m.review_decision ?? 'not yet reviewed'
                        } (similarity ${m.similarity.toFixed(2)})`,
                    )
                    .join('\n')}
                >
                  <span className="font-black uppercase">
                    Informed by {risk.retrieval.similar_requirements.length} similar past requirement
                    {risk.retrieval.similar_requirements.length === 1 ? '' : 's'}
                  </span>
                  <span className="text-black/50">
                    {' '}
                    (retrieval-augmented prompting, threshold {risk.retrieval.similarity_threshold.toFixed(2)}) &mdash; hover to see them
                  </span>
                </div>
              )}
              {activeRequirementId && activeTenantId && (
                <a
                  href={`/graph?requirement_id=${encodeURIComponent(activeRequirementId)}&tenant_id=${encodeURIComponent(activeTenantId)}`}
                  className="mt-1 inline-flex w-fit items-center gap-1 text-xs font-black uppercase tracking-widest underline underline-offset-2 hover:no-underline"
                >
                  View Graph &rarr;
                </a>
              )}
            </div>
          )}
        </div>

        <div className="mono-card p-8 flex flex-col gap-6">
          <div className="flex items-baseline justify-between border-b-2 border-black pb-2 gap-3">
            <h2 className="text-2xl font-black uppercase">Generated Tests</h2>
            <div className="flex items-center gap-3 shrink-0">
              <CostReadout
                requirementId={activeRequirementId}
                tenantId={activeTenantId}
                refreshToken={reviewRefreshToken}
              />
              <span className="text-[10px] font-mono font-black uppercase text-black/50">Live &mdash; Module 2</span>
            </div>
          </div>

          {!tests && (
            <p className="text-sm font-mono text-black/50">
              Run the pipeline on the left to see real generated test cases here.
            </p>
          )}

          {tests && (
            <div className="flex flex-col gap-0 border-2 border-black bg-white">
              {tests.test_cases.map((tc, i) => (
                <div key={i} className="p-4 border-b-2 border-black last:border-b-0">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold uppercase tracking-wide text-sm">{tc.title}</h3>
                    <span className="px-2 py-0.5 text-[10px] font-black bg-black text-white uppercase">{tc.test_type}</span>
                  </div>
                  <p className="text-xs text-black/60 font-mono mt-1">{tc.description}</p>
                  <p className="text-xs mt-2"><span className="font-bold uppercase">Expects:</span> {tc.expected_result}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <PendingReviews
        requirementId={activeRequirementId}
        tenantId={activeTenantId}
        refreshToken={reviewRefreshToken}
      />

      {/* Explicitly demo/mock content -- these connectors are not wired to
         anything real yet (see gap report A.2). The review queue above this
         comment used to live here too, as PendingReviews.tsx, now real. */}
      <div className="mono-card p-8 flex flex-col gap-6 border-dashed">
        <div className="flex items-baseline justify-between border-b-2 border-black pb-2">
          <h2 className="text-2xl font-black uppercase">Live Event Log</h2>
          <span className="text-[10px] font-mono font-black uppercase text-black/40">Demo data &mdash; connectors not yet wired</span>
        </div>
        <div className="flex flex-col gap-0 border-2 border-black bg-white">
          <EventRow tool="Jira" event="Ticket Created" time="Just now" />
          <EventRow tool="GitHub" event="PR Opened" time="2m ago" />
          <EventRow tool="Play" event="Suite Passed" time="15m ago" />
        </div>
      </div>
    </div>
  )
}

function ModuleCard({ number, name, status }: { number: number, name: string, status: string }) {
  const isRunning = status === 'running';
  const isWaiting = status === 'waiting';
  
  let statusColor = "bg-white text-black";
  let statusText = "IDLE";
  let additionalClasses = "";
  
  if (isRunning) {
    statusColor = "bg-black text-white";
    statusText = "RUNNING";
  } else if (isWaiting) {
    statusColor = "bg-gray-200 text-black";
    statusText = "WAITING";
    additionalClasses = "border-dashed";
  }
  
  return (
    <div className={`mono-card p-6 flex flex-col gap-4 transition-all duration-200 hover:-translate-y-1 hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] ${additionalClasses}`}>
      <div className="flex justify-between items-start">
        <div className="w-12 h-12 border-2 border-black bg-black text-white flex items-center justify-center font-black text-2xl">M{number}</div>
        <div className={`px-3 py-1 border-2 border-black text-xs font-black uppercase tracking-widest ${statusColor} flex items-center gap-2`}>
          {isRunning && <div className="w-2 h-2 bg-white animate-ping"></div>}
          {statusText}
        </div>
      </div>
      <h3 className="font-black text-2xl uppercase tracking-tighter mt-2">{name}</h3>
      <div className="mt-auto pt-4 flex justify-between text-xs font-bold text-black/60 border-t-2 border-black/20 uppercase tracking-widest">
        <span>{status === 'idle' || status === 'waiting' ? '\u2014' : 'LIVE'}</span>
      </div>
    </div>
  )
}

function EventRow({ tool, event, time }: { tool: string, event: string, time: string }) {
  return (
    <div className="flex items-center py-4 px-5 border-b-2 border-black last:border-b-0 hover:bg-gray-100 transition-colors">
      <div className="w-6 flex justify-center">
        <div className="w-3 h-3 border-2 border-black bg-black"></div>
      </div>
      <div className="flex-1 flex gap-4 items-center ml-4">
        <span className="font-black uppercase tracking-widest w-20">{tool}</span>
        <span className="font-mono font-bold text-sm">{event}</span>
      </div>
      <div className="text-xs font-black text-black/50 uppercase tracking-widest">{time}</div>
    </div>
  )
}
