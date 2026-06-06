import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Fingerprint, RefreshCw, AlertTriangle, CheckCircle, Layers, ArrowRight, FileText } from 'lucide-react'
import { useFingerprintAnalyze, useContracts } from '../hooks/useQueries'

function SimilarityBar({ value }: { value: number }) {
    let color = 'bg-green-500'
    if (value < 0.5) color = 'bg-gray-400'
    else if (value < 0.7) color = 'bg-yellow-500'
    else if (value < 0.85) color = 'bg-orange-500'
    else color = 'bg-red-500'
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${value * 100}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className={`h-full rounded-full ${color}`}
                />
            </div>
            <span className="text-sm font-medium w-12 text-right">{Math.round(value * 100)}%</span>
        </div>
    )
}

export default function FingerprintPage() {
    const [threshold, setThreshold] = useState(0.65)
    const [result, setResult] = useState<any>(null)
    const { data: contracts } = useContracts()
    const analyze = useFingerprintAnalyze()

    const handleAnalyze = async () => {
        const data = await analyze.mutateAsync({ threshold })
        setResult(data)
    }

    const totalContracts = contracts?.length ?? 0

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Fingerprint className="text-primary" size={28} />
                        Contract Fingerprint
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        MinHash + Jaccard similarity — detect duplicates and contract families without AI
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-gray-200">
                        <span className="text-sm text-gray-500">Threshold</span>
                        <input
                            type="range"
                            min={0.3}
                            max={0.95}
                            step={0.05}
                            value={threshold}
                            onChange={(e) => setThreshold(parseFloat(e.target.value))}
                            className="w-24 accent-primary"
                        />
                        <span className="text-sm font-medium w-10">{Math.round(threshold * 100)}%</span>
                    </div>
                    <button
                        onClick={handleAnalyze}
                        disabled={analyze.isPending || totalContracts < 2}
                        className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                    >
                        {analyze.isPending ? (
                            <RefreshCw size={18} className="animate-spin" />
                        ) : (
                            <Fingerprint size={18} />
                        )}
                        {analyze.isPending ? 'Analyzing...' : 'Run Analysis'}
                    </button>
                </div>
            </div>

            {/* Stats cards */}
            {result && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-4 gap-4"
                >
                    <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-500">Contracts Analyzed</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{result.contracts_analyzed}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-500">Similar Pairs</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{result.similar_pairs.length}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-500">Families Found</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{result.clusters.length}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-500">Threshold</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{Math.round(result.threshold * 100)}%</p>
                    </div>
                </motion.div>
            )}

            {/* Results */}
            <AnimatePresence>
                {result && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-6"
                    >
                        {/* Similar Pairs */}
                        {result.similar_pairs.length > 0 && (
                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                                <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
                                    <AlertTriangle size={18} className="text-orange-500" />
                                    <h2 className="font-semibold text-gray-900">Similar Contract Pairs</h2>
                                    <span className="ml-auto text-sm text-gray-500">
                                        {result.similar_pairs.length} pairs above threshold
                                    </span>
                                </div>
                                <div className="divide-y divide-gray-50">
                                    {result.similar_pairs.map((pair: any, i: number) => (
                                        <motion.div
                                            key={`${pair.contract_a_id}-${pair.contract_b_id}`}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="px-5 py-4 hover:bg-gray-50/50 transition-colors"
                                        >
                                            <div className="flex items-center gap-4 mb-2">
                                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                                    <FileText size={16} className="text-gray-400 shrink-0" />
                                                    <span className="text-sm font-medium text-gray-900 truncate">{pair.contract_a_title}</span>
                                                </div>
                                                <ArrowRight size={14} className="text-gray-300 shrink-0" />
                                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                                    <FileText size={16} className="text-gray-400 shrink-0" />
                                                    <span className="text-sm font-medium text-gray-900 truncate">{pair.contract_b_title}</span>
                                                </div>
                                            </div>
                                            <SimilarityBar value={pair.similarity} />
                                            <div className="flex items-center gap-2 mt-1.5">
                                                {pair.similarity >= 0.85 ? (
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600 font-medium">Near Duplicate</span>
                                                ) : pair.similarity >= 0.7 ? (
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 font-medium">High Similarity</span>
                                                ) : (
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-50 text-yellow-600 font-medium">Moderate Similarity</span>
                                                )}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Clusters / Families */}
                        {result.clusters.length > 0 && (
                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                                <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
                                    <Layers size={18} className="text-primary" />
                                    <h2 className="font-semibold text-gray-900">Contract Families</h2>
                                    <span className="ml-auto text-sm text-gray-500">
                                        {result.clusters.length} clusters
                                    </span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-5">
                                    {result.clusters.map((cluster: any, i: number) => (
                                        <motion.div
                                            key={cluster.cluster_id}
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: i * 0.08 }}
                                            className="border border-gray-100 rounded-lg p-4 hover:shadow-md transition-shadow"
                                        >
                                            <div className="flex items-start justify-between mb-2">
                                                <h3 className="font-medium text-gray-900 text-sm line-clamp-1">{cluster.representative_title}</h3>
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                                                    {cluster.size} contracts
                                                </span>
                                            </div>
                                            <SimilarityBar value={cluster.avg_similarity} />
                                            <p className="text-xs text-gray-400 mt-1.5">
                                                Avg intra-family similarity
                                            </p>
                                            {cluster.size > 1 && (
                                                <div className="mt-2 flex flex-wrap gap-1">
                                                    {cluster.contract_ids.slice(0, 3).map((id: string) => {
                                                        const c = contracts?.find((x: any) => x.id === id)
                                                        return (
                                                            <span key={id} className="text-xs px-2 py-0.5 rounded bg-gray-50 text-gray-600 truncate max-w-[120px]">
                                                                {c?.title || id.slice(0, 8)}
                                                            </span>
                                                        )
                                                    })}
                                                    {cluster.size > 3 && (
                                                        <span className="text-xs px-2 py-0.5 rounded bg-gray-50 text-gray-400">
                                                            +{cluster.size - 3}
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Empty state if no results */}
                        {result.similar_pairs.length === 0 && result.clusters.every((c: any) => c.size === 1) && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="bg-white rounded-xl border border-gray-100 p-12 text-center"
                            >
                                <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900">No Similar Contracts Found</h3>
                                <p className="text-sm text-gray-500 mt-1">
                                    All contracts in the portfolio are sufficiently unique at {Math.round(result.threshold * 100)}% threshold.
                                </p>
                            </motion.div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Initial state */}
            {!result && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white rounded-xl border border-gray-100 p-12 text-center"
                >
                    <Fingerprint size={48} className="mx-auto text-primary/30 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900">Analyze Contract Portfolio</h3>
                    <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
                        Run MinHash fingerprinting to detect duplicate contracts, near-duplicates, and contract families across your portfolio.
                    </p>
                    <div className="mt-4 flex justify-center gap-4 text-sm text-gray-400">
                        <span>{totalContracts} contracts available</span>
                        <span>•</span>
                        <span>128-bit MinHash signature</span>
                        <span>•</span>
                        <span>LSH bucketing</span>
                    </div>
                </motion.div>
            )}
        </div>
    )
}
