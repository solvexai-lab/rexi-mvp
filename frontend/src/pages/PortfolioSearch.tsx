import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, FileText, ArrowRight, Sparkles, Loader2, MessageSquare } from 'lucide-react'
import { usePortfolioSearch, ORG_ID } from '../hooks/useQueries'
import { apiFetch } from '../lib/api'
import { showToast } from '../hooks/useToast'

export default function PortfolioSearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<any>(null)
    const [chatAnswer, setChatAnswer] = useState('')
    const [chatLoading, setChatLoading] = useState(false)
    const search = usePortfolioSearch()

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return
        const data = await search.mutateAsync({ query: query.trim(), topK: 8 })
        setResults(data)
        setChatAnswer('')
    }

    const handleChat = async () => {
        if (!query.trim()) return
        setChatLoading(true)
        setChatAnswer('')
        try {
            const res = await apiFetch('/chat/portfolio/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: query.trim(), org_id: ORG_ID }),
            })
            const data = await res.json()
            setChatAnswer(data.answer || '')
        } catch {
            showToast('Failed to get answer', 'error')
        }
        setChatLoading(false)
    }

    return (
        <div className="p-6 max-w-5xl mx-auto space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900 flex items-center justify-center gap-2">
                    <Search className="text-primary" size={28} />
                    Portfolio Search
                </h1>
                <p className="text-sm text-gray-500">
                    Semantic search + AI chat across all contracts
                </p>
            </div>

            {/* Search bar */}
            <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto">
                <div className="relative">
                    <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. 'liability cap exceeds 2 crore' or '90-day termination notice'"
                        className="w-full pl-12 pr-28 py-4 bg-white border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-sm"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                        <button
                            type="button"
                            onClick={handleChat}
                            disabled={chatLoading || !query.trim()}
                            className="bg-blue-600 text-white p-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            title="Ask AI"
                        >
                            {chatLoading ? <Loader2 size={18} className="animate-spin" /> : <MessageSquare size={18} />}
                        </button>
                        <button
                            type="submit"
                            disabled={search.isPending || !query.trim()}
                            className="bg-primary text-white p-2.5 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                        >
                            {search.isPending ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
                        </button>
                    </div>
                </div>
            </form>

            <AnimatePresence mode="wait">
                {chatAnswer && (
                    <motion.div
                        key="chat"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="bg-blue-50 rounded-xl border border-blue-100 p-6"
                    >
                        <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
                            <Sparkles size={16} /> AI Portfolio Answer
                        </h3>
                        <p className="text-sm text-blue-900 whitespace-pre-wrap">{chatAnswer}</p>
                    </motion.div>
                )}

                {results && !chatAnswer && (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                    >
                        <div className="flex items-center justify-between">
                            <h2 className="font-semibold text-gray-900">
                                {results.results?.length || 0} matching clauses
                            </h2>
                            <span className="text-xs text-gray-400">Powered by {results.embedder || 'embeddings'}</span>
                        </div>

                        {results.results?.length === 0 ? (
                            <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
                                <FileText size={40} className="mx-auto mb-3 text-gray-300" />
                                <p className="text-gray-500">No matching clauses found</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {results.results.map((r: any, i: number) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow"
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-gray-700 leading-relaxed line-clamp-3">{r.chunk_text}</p>
                                                <div className="flex items-center gap-3 mt-3">
                                                    <span className="flex items-center gap-1 text-xs text-gray-500">
                                                        <FileText size={12} />
                                                        Contract {r.contract_id.slice(0, 8)}...
                                                    </span>
                                                    {r.page_number && (
                                                        <span className="text-xs text-gray-400">Page {r.page_number}</span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="shrink-0 text-right">
                                                <div className="text-lg font-bold text-primary">{Math.round(r.score * 100)}%</div>
                                                <div className="text-xs text-gray-400">match</div>
                                            </div>
                                        </div>
                                        {/* Score bar */}
                                        <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${r.score * 100}%` }}
                                                transition={{ duration: 0.6, delay: i * 0.05 }}
                                                className="h-full bg-primary rounded-full"
                                            />
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
