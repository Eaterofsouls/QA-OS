'use client'

// Real "Cost" readout for a requirement's LLM calls, backed by
// GET /requirements/{id}/cost (services/api/main.py) which reads back
// exactly what CostLedger.record_call() logged in
// packages/llm-gateway-client/ledger.py for every real /assess and
// /generate-tests call. Nothing here is computed or estimated client-side
// -- if the server says a number is unknown (null), this renders
// "usage unknown", never a guess.

import React, { useEffect, useState } from 'react'
import { api, ApiError, RequirementCostResponse } from '../../lib/api'

interface CostReadoutProps {
  requirementId: string | null
  tenantId: string | null
  /** Bump this after each real LLM call completes to force a re-fetch. */
  refreshToken: number
}

export function CostReadout({ requirementId, tenantId, refreshToken }: CostReadoutProps) {
  const [cost, setCost] = useState<RequirementCostResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!requirementId || !tenantId) {
      setCost(null)
      return
    }
    let cancelled = false
    api
      .getRequirementCost(requirementId, tenantId)
      .then((result) => {
        if (!cancelled) setCost(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load cost.')
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requirementId, tenantId, refreshToken])

  if (!requirementId || !tenantId) return null
  if (error) return null // non-critical readout -- fail quiet, don't block the panel
  if (!cost || cost.entries.length === 0) return null

  const tokensKnown = cost.total_prompt_tokens !== null && cost.total_completion_tokens !== null
  const totalTokens = tokensKnown
    ? (cost.total_prompt_tokens as number) + (cost.total_completion_tokens as number)
    : null
  const costKnown = cost.total_estimated_cost_usd !== null

  return (
    <span
      className="text-[10px] font-mono font-black uppercase text-black/50 whitespace-nowrap"
      title={
        cost.entries.some((e) => !e.usage_reported)
          ? 'One or more calls did not report usage -- shown as unknown, not estimated.'
          : cost.entries[0]?.cost_basis || undefined
      }
    >
      Cost:{' '}
      {totalTokens !== null ? `${totalTokens.toLocaleString()} tokens` : 'tokens unknown'}
      {' \u00b7 '}
      {costKnown ? `$${(cost.total_estimated_cost_usd as number).toFixed(4)}` : 'cost unknown'}
    </span>
  )
}
