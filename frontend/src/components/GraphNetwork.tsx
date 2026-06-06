import { useEffect, useRef } from 'react'
import { Network, DataSet } from 'vis-network/standalone'

interface GraphNetworkProps {
    nodes: any[]
    edges: any[]
}

export default function GraphNetwork({ nodes, edges }: GraphNetworkProps) {
    const containerRef = useRef<HTMLDivElement>(null)
    const networkRef = useRef<Network | null>(null)

    useEffect(() => {
        if (!containerRef.current || nodes.length === 0) return

        const nodeSet = new DataSet(nodes)
        const edgeSet = new DataSet(edges)

        const options = {
            nodes: {
                shape: 'dot',
                font: { size: 11, face: 'Inter, sans-serif', color: '#1F2937', strokeWidth: 3, strokeColor: '#ffffff' },
                borderWidth: 2,
                shadow: { enabled: true, color: 'rgba(0,0,0,0.1)', size: 4, x: 2, y: 2 },
            },
            edges: {
                width: 1.5,
                font: { size: 9, align: 'middle', color: '#6B7280', background: 'rgba(255,255,255,0.9)', strokeWidth: 2, strokeColor: '#ffffff' },
                smooth: { enabled: true, type: 'continuous', roundness: 0.2 },
                arrows: { to: { enabled: true, scaleFactor: 0.6 } },
                color: { inherit: false, color: '#CBD5E1', highlight: '#3B82F6', hover: '#3B82F6' },
            },
            groups: {
                contract: {
                    color: { background: '#3B82F6', border: '#2563EB', highlight: { background: '#60A5FA', border: '#2563EB' } },
                    font: { color: '#FFFFFF', size: 12, strokeWidth: 0 },
                    shape: 'box',
                    margin: 10,
                    borderRadius: 10,
                    widthConstraint: { maximum: 160 },
                },
                clause: {
                    color: { background: '#F3F4F6', border: '#9CA3AF', highlight: { background: '#E5E7EB', border: '#6B7280' } },
                    font: { size: 10, color: '#4B5563', strokeWidth: 2, strokeColor: '#ffffff' },
                    shape: 'dot',
                    size: 8,
                },

                rule_ok: {
                    color: { background: '#22C55E', border: '#16A34A', highlight: { background: '#4ADE80', border: '#16A34A' } },
                    font: { color: '#FFFFFF', size: 10, strokeWidth: 0 },
                    shape: 'box',
                    margin: 6,
                    borderRadius: 6,
                    widthConstraint: { maximum: 140 },
                },
                statute_risk: {
                    color: { background: '#F59E0B', border: '#D97706', highlight: { background: '#FBBF24', border: '#D97706' } },
                    font: { color: '#FFFFFF', size: 10, strokeWidth: 0 },
                    shape: 'diamond',
                    size: 12,
                },
                statute_ok: {
                    color: { background: '#6366F1', border: '#4F46E5', highlight: { background: '#818CF8', border: '#4F46E5' } },
                    font: { color: '#FFFFFF', size: 10, strokeWidth: 0 },
                    shape: 'diamond',
                    size: 12,
                },
                regulation: {
                    color: { background: '#EC4899', border: '#DB2777', highlight: { background: '#F472B6', border: '#DB2777' } },
                    font: { color: '#FFFFFF', size: 10, strokeWidth: 0 },
                    shape: 'hexagon',
                    size: 14,
                },
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -4000,
                    centralGravity: 0.2,
                    springLength: 140,
                    springConstant: 0.03,
                    damping: 0.08,
                    avoidOverlap: 0.3,
                },
                stabilization: { iterations: 200, enabled: true },
                adaptiveTimestep: true,
            },
            interaction: {
                hover: true,
                tooltipDelay: 150,
                zoomView: true,
                dragView: true,
                dragNodes: true,
                hideEdgesOnDrag: false,
                hideNodesOnDrag: false,
            },
            layout: {
                randomSeed: 42,
                improvedLayout: true,
            },
        }

        networkRef.current = new Network(containerRef.current, { nodes: nodeSet, edges: edgeSet }, options)

        return () => {
            if (networkRef.current) {
                networkRef.current.destroy()
                networkRef.current = null
            }
        }
    }, [nodes, edges])

    return (
        <div
            ref={containerRef}
            style={{ width: '100%', height: '700px', background: '#FAFBFC' }}
            className="rounded-xl border border-gray-200"
        />
    )
}
