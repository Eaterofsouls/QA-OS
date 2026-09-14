'use client'

import React, { useCallback, useEffect, useMemo, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { api, ApiError, GraphNode, GraphEdge, RequirementGraphResponse } from '../../lib/api'

// Real, black-and-white, mono-card-matching node styling by KG label. No
// sample/placeholder graph -- every node/edge rendered here comes straight
// out of GET /requirements/{id}/graph, which reads the real KG.
const NODE_STYLE_BASE: React.CSSProperties = {
  border: '2px solid #000',
  borderRadius: 0,
  fontFamily: 'ui-monospace, monospace',
  fontWeight: 800,
  textTransform: 'uppercase',
  fontSize: 11,
  letterSpacing: '0.05em',
  padding: '10px 14px',
  boxShadow: '3px 3px 0px 0px rgba(0,0,0,1)',
}

const LABEL_STYLES: Record<string, React.CSSProperties> = {
  Requirement: { ...NODE_STYLE_BASE, background: '#000', color: '#fff' },
  RiskAssessment: { ...NODE_STYLE_BASE, background: '#fff', color: '#000', borderStyle: 'solid' },
  TestCase: { ...NODE_STYLE_BASE, background: '#f3f3f3', color: '#000' },
}

function styleForLabel(label: string): React.CSSProperties {
  return LABEL_STYLES[label] ?? { ...NODE_STYLE_BASE, background: '#fff', color: '#000', borderStyle: 'dashed' }
}

function shortLabel(node: GraphNode): string {
  const p = node.properties
  if (node.label === 'Requirement') return `Requirement\n${String(p.text ?? '').slice(0, 28)}...`
  if (node.label === 'RiskAssessment') return `Risk: ${String(p.risk_level ?? '?')}`
  if (node.label === 'TestCase') return `Test: ${String(p.title ?? node.id).slice(0, 24)}`
  return node.label
}

// Simple deterministic layout: Requirement on the left, everything else
// arranged in a column to its right, grouped by label so RiskAssessment and
// TestCase nodes each get their own row-band. No layout library needed for
// a graph this small (one requirement's real neighborhood, not the whole KG).
function layout(graph: RequirementGraphResponse): { nodes: Node[]; edges: Edge[] } {
  const byLabel: Record<string, GraphNode[]> = {}
  for (const n of graph.nodes) {
    if (n.id === graph.requirement_id) continue
    byLabel[n.label] = byLabel[n.label] ?? []
    byLabel[n.label].push(n)
  }

  const nodes: Node[] = []
  const requirementNode = graph.nodes.find((n) => n.id === graph.requirement_id)
  if (requirementNode) {
    nodes.push({
      id: requirementNode.id,
      position: { x: 40, y: 220 },
      data: { label: shortLabel(requirementNode) },
      style: { ...styleForLabel('Requirement'), width: 220, whiteSpace: 'pre-line' },
    })
  }

  const labelOrder = Object.keys(byLabel).sort()
  let colX = 420
  for (const label of labelOrder) {
    const group = byLabel[label]
    group.forEach((n, i) => {
      nodes.push({
        id: n.id,
        position: { x: colX, y: 40 + i * 110 },
        data: { label: shortLabel(n) },
        style: { ...styleForLabel(label), width: 200 },
      })
    })
    colX += 320
  }

  const edges: Edge[] = graph.edges.map((e: GraphEdge) => ({
    id: `${e.source}->${e.target}`,
    source: e.source,
    target: e.target,
    label: e.type,
    labelStyle: { fontFamily: 'ui-monospace, monospace', fontWeight: 800, fontSize: 10 },
    style: { stroke: '#000', strokeWidth: 2 },
    labelBgStyle: { fill: '#fff' },
  }))

  return { nodes, edges }
}

export default function GraphExplorer() {
  return (
    <Suspense
      fallback={
        <div className="max-w-6xl mx-auto">
          <p className="font-mono text-sm text-black/50">Loading&hellip;</p>
        </div>
      }
    >
      <GraphExplorerInner />
    </Suspense>
  )
}

function GraphExplorerInner() {
  const searchParams = useSearchParams()

  const [requirementId, setRequirementId] = useState(searchParams.get('requirement_id') ?? '')
  const [tenantId, setTenantId] = useState(searchParams.get('tenant_id') ?? '')
  const [graph, setGraph] = useState<RequirementGraphResponse | null>(null)
  const [selected, setSelected] = useState<GraphNode | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (reqId: string, tid: string) => {
    if (!reqId.trim() || !tid.trim()) return
    setLoading(true)
    setError(null)
    setSelected(null)
    try {
      const result = await api.getRequirementGraph(reqId.trim(), tid.trim())
      setGraph(result)
    } catch (err) {
      setGraph(null)
      setError(err instanceof ApiError ? err.message : 'Unexpected error loading the graph.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-load if the page was opened with ?requirement_id=...&tenant_id=...
  // (e.g. linked from the Command Center after a real run).
  useEffect(() => {
    const qReq = searchParams.get('requirement_id')
    const qTenant = searchParams.get('tenant_id')
    if (qReq && qTenant) {
      load(qReq, qTenant)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const { nodes, edges } = useMemo(() => (graph ? layout(graph) : { nodes: [], edges: [] }), [graph])

  function onNodeClick(_: React.MouseEvent, node: Node) {
    const real = graph?.nodes.find((n) => n.id === node.id) ?? null
    setSelected(real)
  }

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-8">
      <header className="flex justify-between items-center border-b-4 border-black pb-6">
        <div>
          <h1 className="text-4xl font-black uppercase tracking-tighter">Graph Explorer</h1>
          <p className="text-black/70 mt-2 font-mono uppercase text-sm font-bold tracking-widest">
            Live Knowledge Graph &mdash; Real Nodes, Real Edges
          </p>
        </div>
      </header>

      <div className="mono-card p-6 flex flex-col gap-4">
        <div className="flex items-end gap-4 flex-wrap">
          <label className="flex flex-col gap-1 text-xs font-black uppercase tracking-widest">
            Requirement ID
            <input
              className="border-2 border-black px-3 py-2 font-mono text-sm min-w-[220px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
              value={requirementId}
              onChange={(e) => setRequirementId(e.target.value)}
              placeholder="req-1234567890"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-black uppercase tracking-widest">
            Tenant ID
            <input
              className="border-2 border-black px-3 py-2 font-mono text-sm min-w-[280px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              placeholder="00000000-0000-0000-0000-000000000000"
            />
          </label>
          <button
            onClick={() => load(requirementId, tenantId)}
            disabled={loading || !requirementId.trim() || !tenantId.trim()}
            className="border-2 border-black bg-black text-white font-black uppercase tracking-widest px-6 py-2 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading\u2026' : 'Load'}
          </button>
        </div>
        <p className="text-xs font-mono text-black/50">
          Get these from the Command Center after running a real pipeline &mdash; or open this
          page via the &ldquo;View Graph&rdquo; link it adds once a run completes.
        </p>

        {error && (
          <div className="border-2 border-black bg-black text-white p-3 font-mono text-sm font-bold">
            {error}
          </div>
        )}
      </div>

      {graph && (
        <div className="grid grid-cols-3 gap-8">
          <div className="col-span-2 mono-card" style={{ height: 520 }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={onNodeClick}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#00000022" gap={20} />
              <Controls />
              <MiniMap
                nodeColor={(n) => (n.id === graph.requirement_id ? '#000' : '#999')}
                maskColor="rgba(255,255,255,0.7)"
              />
            </ReactFlow>
          </div>

          <div className="mono-card p-6 flex flex-col gap-4">
            <h2 className="text-lg font-black uppercase tracking-widest border-b-2 border-black pb-2">
              Node Detail
            </h2>
            {!selected && (
              <p className="text-sm font-mono text-black/50">
                Click a node in the graph to see its real, stored properties here.
              </p>
            )}
            {selected && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-black text-white text-xs font-black uppercase">
                    {selected.label}
                  </span>
                  <span className="font-mono text-xs text-black/50">{selected.id}</span>
                </div>
                <dl className="flex flex-col gap-2">
                  {Object.entries(selected.properties)
                    .filter(([key]) => key !== 'tenant_id')
                    .map(([key, value]) => (
                      <div key={key} className="border-t-2 border-black/10 pt-2">
                        <dt className="text-[10px] font-black uppercase tracking-widest text-black/50">
                          {key}
                        </dt>
                        <dd className="text-sm font-mono break-words">
                          {Array.isArray(value) ? value.join(', ') : String(value)}
                        </dd>
                      </div>
                    ))}
                </dl>
              </div>
            )}
          </div>
        </div>
      )}

      {!graph && !loading && !error && (
        <div className="mono-card p-10 flex flex-col items-center justify-center gap-2 border-dashed">
          <p className="font-mono text-sm text-black/50 text-center">
            No graph loaded. Enter a Requirement ID and Tenant ID above, or arrive here from the
            Command Center after a real run.
          </p>
        </div>
      )}
    </div>
  )
}
