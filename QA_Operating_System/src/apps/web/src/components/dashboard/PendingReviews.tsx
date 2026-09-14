'use client'

// Module 3 (Review Gate) panel. Was a one-line empty stub before the Aug
// 2026 Module 3 wiring pass; now a real component calling the real
// GET/POST /requirements/{id}/tests[/*/review] routes in services/api/main.py.
// No optimistic UI: after every Approve/Reject click, the list is re-fetched
// from the KG via listRequirementTests() rather than trusting the POST
// response alone -- what's shown is always what the server has, not what the
// button click predicted.

import React, { useCallback, useEffect, useState } from 'react'
import { api, ApiError, TestCaseWithReview } from '../../lib/api'

interface PendingReviewsProps {
  requirementId: string | null
  tenantId: string | null
  /** Bump this after a successful generate-tests call to force a re-fetch. */
  refreshToken: number
}

export function PendingReviews({ requirementId, tenantId, refreshToken }: PendingReviewsProps) {
  const [testCases, setTestCases] = useState<TestCaseWithReview[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reviewerId, setReviewerId] = useState('qa-reviewer')
  const [submittingId, setSubmittingId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!requirementId || !tenantId) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.listRequirementTests(requirementId, tenantId)
      setTestCases(result.test_cases)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error loading test cases.')
    } finally {
      setLoading(false)
    }
  }, [requirementId, tenantId])

  useEffect(() => {
    refresh()
    // refreshToken deliberately included so a fresh generate-tests run
    // re-fetches even though requirementId/tenantId may be unchanged.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requirementId, tenantId, refreshToken])

  async function handleDecision(testCaseId: string, decision: 'approved' | 'rejected') {
    if (!requirementId || !tenantId) return
    setSubmittingId(testCaseId)
    setError(null)
    try {
      await api.reviewTestCase(requirementId, testCaseId, tenantId, reviewerId || 'qa-reviewer', decision)
      // Re-fetch from the KG rather than locally mutating state -- the
      // panel always shows server-confirmed status, not a guess.
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error submitting review.')
    } finally {
      setSubmittingId(null)
    }
  }

  const hasRun = requirementId !== null && tenantId !== null

  return (
    <div className="mono-card p-8 flex flex-col gap-6">
      <div className="flex items-baseline justify-between border-b-2 border-black pb-2">
        <h2 className="text-2xl font-black uppercase">Pending Review</h2>
        <span className="text-[10px] font-mono font-black uppercase text-black/50">Live &mdash; Module 3</span>
      </div>

      {!hasRun && (
        <p className="text-sm font-mono text-black/50">
          Run the pipeline above to generate test cases for review.
        </p>
      )}

      {hasRun && (
        <div className="flex items-center gap-3">
          <label className="text-xs font-black uppercase tracking-widest text-black/60">Reviewer ID</label>
          <input
            className="border-2 border-black px-2 py-1 font-mono text-sm flex-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            placeholder="e.g. jane-qa-lead"
          />
        </div>
      )}

      {loading && !testCases && (
        <p className="text-sm font-mono text-black/50">Loading test cases&hellip;</p>
      )}

      {error && (
        <div className="border-2 border-black bg-black text-white p-3 font-mono text-sm font-bold">
          {error}
        </div>
      )}

      {hasRun && testCases && testCases.length === 0 && (
        <p className="text-sm font-mono text-black/50">
          No test cases yet for this requirement &mdash; generate tests first.
        </p>
      )}

      {testCases && testCases.length > 0 && (
        <div className="flex flex-col gap-0 border-2 border-black bg-white">
          {testCases.map((tc) => {
            const isPending = tc.status === 'draft'
            const isSubmitting = submittingId === tc.id
            return (
              <div key={tc.id} className="p-4 border-b-2 border-black last:border-b-0 flex flex-col gap-2">
                <div className="flex justify-between items-center gap-3">
                  <h3 className="font-bold uppercase tracking-wide text-sm">{tc.title}</h3>
                  <StatusBadge status={tc.status} />
                </div>
                <p className="text-xs text-black/60 font-mono">{tc.description}</p>
                <p className="text-xs"><span className="font-bold uppercase">Expects:</span> {tc.expected_result}</p>

                {isPending ? (
                  <div className="flex gap-2 mt-1">
                    <button
                      onClick={() => handleDecision(tc.id, 'approved')}
                      disabled={isSubmitting}
                      className="flex-1 border-2 border-black bg-black text-white font-black uppercase tracking-widest text-xs py-2 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? 'Submitting\u2026' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleDecision(tc.id, 'rejected')}
                      disabled={isSubmitting}
                      className="flex-1 border-2 border-black bg-white text-black font-black uppercase tracking-widest text-xs py-2 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? 'Submitting\u2026' : 'Reject'}
                    </button>
                  </div>
                ) : (
                  <div className="text-[10px] font-mono font-bold uppercase text-black/60 mt-1">
                    {tc.status} by {tc.reviewer_id}
                    {tc.review_note ? ` \u2014 "${tc.review_note}"` : ''}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    draft: 'bg-gray-200 text-black',
    approved: 'bg-black text-white',
    rejected: 'bg-white text-black border-2 border-black',
  }
  return (
    <span className={`px-2 py-0.5 text-[10px] font-black uppercase shrink-0 ${styles[status] || styles.draft}`}>
      {status}
    </span>
  )
}
