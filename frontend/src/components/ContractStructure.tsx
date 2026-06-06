import { useState } from 'react'
import { ChevronRight, ChevronDown, FileText, Search, TreePine, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useContractTreeQuery } from '../hooks/useQueries'

interface TreeNode {
    title: string
    node_id: string
    line_num: number
    text?: string
    summary?: string
    nodes?: TreeNode[]
}

function TreeNodeItem({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
    const [expanded, setExpanded] = useState(depth < 2)
    const hasChildren = node.nodes && node.nodes.length > 0

    return (
        <div className="select-none">
            <button
                onClick={() => hasChildren && setExpanded(!expanded)}
                className={`flex items-center gap-1 w-full text-left py-1 px-2 rounded hover:bg-gray-50 transition-colors ${
                    hasChildren ? 'cursor-pointer' : 'cursor-default'
                }`}
                style={{ paddingLeft: `${depth * 16 + 8}px` }}
            >
                {hasChildren ? (
                    expanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                    ) : (
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                    )
                ) : (
                    <span className="w-4" />
                )}
                <FileText className="w-4 h-4 text-primary-light" />
                <span className="text-sm font-medium text-gray-800">{node.title}</span>
                {node.node_id && (
                    <span className="text-xs text-gray-400 ml-1">#{node.node_id}</span>
                )}
            </button>

            <AnimatePresence>
                {expanded && hasChildren && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        {node.nodes!.map((child, i) => (
                            <TreeNodeItem key={child.node_id || i} node={child} depth={depth + 1} />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {expanded && node.text && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mx-4 my-1 p-3 bg-gray-50 rounded text-sm text-gray-600 leading-relaxed"
                    style={{ marginLeft: `${depth * 16 + 32}px` }}
                >
                    {node.summary && (
                        <p className="text-xs font-medium text-primary mb-1">{node.summary}</p>
                    )}
                    <p className="line-clamp-6">{node.text}</p>
                </motion.div>
            )}
        </div>
    )
}

export default function ContractStructure({
    structure,
    doc_name,
    node_count,
    loading,
    error,
    contractId,
}: {
    structure: TreeNode[]
    doc_name: string
    node_count: number
    loading: boolean
    error: string | null
    contractId?: string
}) {
    const [search, setSearch] = useState('')
    const [queryResults, setQueryResults] = useState<any[] | null>(null)
    const treeQuery = useContractTreeQuery(contractId)

    if (loading) {
        return (
            <div className="p-8 space-y-4">
                <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="space-y-2">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" style={{ marginLeft: `${i * 12}px` }} />
                    ))}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8 text-center">
                <TreePine className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">{error}</p>
            </div>
        )
    }

    if (!structure || structure.length === 0) {
        return (
            <div className="p-8 text-center">
                <TreePine className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No document structure available.</p>
                <p className="text-sm text-gray-400 mt-1">Structure is generated during contract upload.</p>
            </div>
        )
    }

    const handleSearch = async (val: string) => {
        setSearch(val)
        if (!val.trim() || val.length < 3) {
            setQueryResults(null)
            return
        }
        try {
            const res = await treeQuery.mutateAsync(val)
            setQueryResults(res.results || [])
        } catch {
            setQueryResults([])
        }
    }

    const filtered = search && !queryResults
        ? structure.filter((n) => n.title.toLowerCase().includes(search.toLowerCase()))
        : structure

    return (
        <div className="p-6">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">Document Structure</h3>
                    <p className="text-sm text-gray-500">
                        {doc_name} · {node_count} sections
                    </p>
                </div>
            </div>

            <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search sections (min 3 chars)..."
                    value={search}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                {treeQuery.isPending && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-500 animate-spin" />
                )}
            </div>

            {queryResults && search.length >= 3 && (
                <div className="mb-4 bg-blue-50 rounded-lg p-3">
                    <p className="text-xs font-medium text-blue-700 mb-2">
                        {queryResults.length} match{queryResults.length !== 1 ? 'es' : ''} for "{search}"
                    </p>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                        {queryResults.map((r: any, i: number) => (
                            <div key={i} className="bg-white rounded-md p-2.5 border border-blue-100">
                                <p className="text-sm font-medium text-gray-800">{r.title}</p>
                                <p className="text-xs text-gray-500 mt-0.5">{r.path}</p>
                                {r.text_preview && (
                                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">{r.text_preview}</p>
                                )}
                                <div className="flex items-center gap-2 mt-1.5">
                                    <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                                        Score: {(r.score * 100).toFixed(0)}%
                                    </span>
                                    {r.line_num && (
                                        <span className="text-[10px] text-gray-400">Line {r.line_num}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="border border-gray-100 rounded-lg overflow-hidden">
                {filtered.map((node, i) => (
                    <TreeNodeItem key={node.node_id || i} node={node} />
                ))}
            </div>
        </div>
    )
}
