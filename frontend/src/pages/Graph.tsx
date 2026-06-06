import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Share2, RefreshCw, AlertTriangle, Search, Gavel,
    Scale, ShieldCheck, BookOpen, ChevronRight, FileText,
    AlertOctagon, CheckCircle, X
} from 'lucide-react'
import { useGraphPillars, useGraphImpact, useRescanPlaybook, useGraphNetwork } from '../hooks/useQueries'
import GraphNetwork from '../components/GraphNetwork'

type Pillar = 'playbook' | 'statutes' | 'regulations'

const PILLAR_CONFIG = {
    playbook: {
        label: 'Playbook',
        icon: ShieldCheck,
        color: 'blue',
        bg: 'bg-blue-50',
        text: 'text-blue-700',
        border: 'border-blue-200',
        badge: 'bg-blue-100 text-blue-700',
        dot: 'bg-blue-500',
    },
    statutes: {
        label: 'Law',
        icon: Gavel,
        color: 'green',
        bg: 'bg-green-50',
        text: 'text-green-700',
        border: 'border-green-200',
        badge: 'bg-green-100 text-green-700',
        dot: 'bg-green-500',
    },
    regulations: {
        label: 'Regulatory',
        icon: Scale,
        color: 'red',
        bg: 'bg-red-50',
        text: 'text-red-700',
        border: 'border-red-200',
        badge: 'bg-red-100 text-red-700',
        dot: 'bg-red-500',
    },
}

function ImpactPanel({ data, pillar, onClose }: { data: any; pillar: Pillar; onClose: () => void }) {
    const cfg = PILLAR_CONFIG[pillar]

    return (
        <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden"
        >
            <div className={`px-5 py-4 border-b ${cfg.border} ${cfg.bg} flex items-center justify-between`}>
                <div className="flex items-center gap-2">
                    <cfg.icon size={18} className={cfg.text} />
                    <h3 className={`font-semibold ${cfg.text}`}>
                        {pillar === 'playbook' && data.rule_name}
                        {pillar === 'statutes' && `${data.statute_act} ${data.section_number}`}
                        {pillar === 'regulations' && data.title}
                    </h3>
                </div>
                <button onClick={onClose} className="p-1 hover:bg-black/5 rounded">
                    <X size={16} className="text-gray-400" />
                </button>
            </div>

            <div className="p-5 space-y-4 max-h-[500px] overflow-y-auto">
                {/* Meta */}
                <div className="flex items-center gap-2 text-xs">
                    <span className={`px-2 py-0.5 rounded-full font-medium ${cfg.badge}`}>
                        {cfg.label}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-500">
                        {pillar === 'playbook' && `${data.contracts_scanned} contracts scanned`}
                        {pillar === 'statutes' && `${data.contracts_governed} contracts governed`}
                        {pillar === 'regulations' && `${data.contracts_affected} contracts affected`}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-500">SQL-powered</span>
                </div>

                {/* Results */}
                {pillar === 'playbook' && (
                    <div className="space-y-3">
                        {data.violations?.length === 0 ? (
                            <div className="text-center py-6">
                                <CheckCircle size={32} className="mx-auto text-green-500 mb-2" />
                                <p className="text-sm text-gray-600">No violations found</p>
                                <p className="text-xs text-gray-400">All contracts comply with this rule</p>
                            </div>
                        ) : (
                            data.violations?.map((v: any, i: number) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="border border-gray-100 rounded-lg p-3 hover:shadow-sm transition-shadow"
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-gray-900 truncate">{v.title}</p>
                                            <p className="text-xs text-gray-500 mt-0.5">{v.reason}</p>
                                            {v.clause_text && (
                                                <p className="text-xs text-gray-400 mt-1 line-clamp-2 italic">"{v.clause_text}"</p>
                                            )}
                                        </div>
                                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0 ${
                                            v.severity === 'critical' ? 'bg-red-100 text-red-600' :
                                            v.severity === 'high' ? 'bg-orange-100 text-orange-600' :
                                            'bg-yellow-100 text-yellow-600'
                                        }`}>
                                            {v.severity}
                                        </span>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                )}

                {pillar === 'statutes' && (
                    <div className="space-y-3">
                        {data.contracts?.map((c: any, i: number) => (
                            <motion.div
                                key={c.contract_id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="border border-gray-100 rounded-lg p-3"
                            >
                                <p className="text-sm font-medium text-gray-900">{c.title}</p>
                                <div className="mt-2 space-y-1.5">
                                    {c.clauses.map((cl: any, j: number) => (
                                        <div key={j} className="text-xs bg-gray-50 rounded px-2 py-1.5">
                                            <span className="font-medium text-gray-700">{cl.clause_type}</span>
                                            <span className="text-gray-400 mx-1">•</span>
                                            <span className="text-gray-500">Enforceability: {cl.enforceability_score}</span>
                                            <p className="text-gray-400 mt-0.5 line-clamp-1">{cl.clause_text}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {pillar === 'regulations' && (
                    <div className="space-y-3">
                        {data.contracts?.map((c: any, i: number) => (
                            <motion.div
                                key={c.contract_id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="border border-gray-100 rounded-lg p-3"
                            >
                                <p className="text-sm font-medium text-gray-900">{c.title}</p>
                                <div className="mt-2 space-y-1.5">
                                    {c.clauses.map((cl: any, j: number) => (
                                        <div key={j} className="text-xs bg-gray-50 rounded px-2 py-1.5">
                                            <span className="font-medium text-gray-700">{cl.clause_type}</span>
                                            <p className="text-gray-400 mt-0.5 line-clamp-1">{cl.clause_text}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </motion.div>
    )
}

export default function GraphPage() {
    const [activePillar, setActivePillar] = useState<Pillar>('playbook')
    const [selectedId, setSelectedId] = useState<string | null>(null)
    const [search, setSearch] = useState('')
    const [viewMode, setViewMode] = useState<'list' | 'network'>('list')
    const [networkPillar, setNetworkPillar] = useState<string>('all')

    const { data: pillars, isLoading } = useGraphPillars(activePillar)
    const { data: impactData } = useGraphImpact(activePillar, selectedId || undefined)
    const { data: networkData, isLoading: networkLoading } = useGraphNetwork(networkPillar)
    const rescan = useRescanPlaybook()

    const cfg = PILLAR_CONFIG[activePillar]

    const filtered = (pillars || []).filter((p: any) => {
        const text = activePillar === 'playbook' ? p.rule_name :
            activePillar === 'statutes' ? p.statute_act :
            p.title
        return text?.toLowerCase().includes(search.toLowerCase())
    })

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Share2 className="text-primary" size={28} />
                        3-Pillar Impact Engine
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Playbook + Law + Regulatory impact — powered by deterministic SQL
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`px-3 py-2 text-sm font-medium transition-colors ${viewMode === 'list' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                        >
                            List View
                        </button>
                        <button
                            onClick={() => setViewMode('network')}
                            className={`px-3 py-2 text-sm font-medium transition-colors ${viewMode === 'network' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                        >
                            Network Graph
                        </button>
                    </div>
                    {viewMode === 'list' && (
                        <button
                            onClick={() => rescan.mutate()}
                            disabled={rescan.isPending}
                            className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                        >
                            {rescan.isPending ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                            {rescan.isPending ? 'Scanning...' : 'Re-scan Portfolio'}
                        </button>
                    )}
                </div>
            </div>

            {/* Pillar Tabs */}
            <div className="flex items-center gap-2">
                {(Object.keys(PILLAR_CONFIG) as Pillar[]).map((p) => {
                    const c = PILLAR_CONFIG[p]
                    const isActive = activePillar === p
                    return (
                        <button
                            key={p}
                            onClick={() => { setActivePillar(p); setSelectedId(null); setSearch('') }}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                                isActive
                                    ? `${c.bg} ${c.text} border ${c.border} shadow-sm`
                                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                            }`}
                        >
                            <c.icon size={16} />
                            {c.label}
                            {isActive && <ChevronRight size={14} />}
                        </button>
                    )
                })}
            </div>

            {viewMode === 'list' && (
                <>
                {/* Main Content */}
                <div className="grid grid-cols-12 gap-6">
                    {/* Left: Pillar Items List */}
                    <div className="col-span-4 bg-white rounded-xl border border-gray-200 overflow-hidden">
                        <div className={`px-4 py-3 border-b ${cfg.border} ${cfg.bg}`}>
                            <div className="relative">
                                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder={`Search ${cfg.label}...`}
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="w-full pl-8 pr-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                />
                            </div>
                        </div>

                        <div className="divide-y divide-gray-50 max-h-[560px] overflow-y-auto">
                            {isLoading ? (
                                <div className="p-8 space-y-3">
                                    {[1, 2, 3].map(i => (
                                        <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
                                    ))}
                                </div>
                            ) : filtered.length === 0 ? (
                                <div className="p-8 text-center text-sm text-gray-400">
                                    <BookOpen size={24} className="mx-auto mb-2 text-gray-300" />
                                    No {cfg.label} items found
                                </div>
                            ) : (
                                filtered.map((item: any) => {
                                    const id = item.id
                                    const isSelected = selectedId === id
                                    const title = activePillar === 'playbook' ? item.rule_name :
                                        activePillar === 'statutes' ? `${item.statute_act} ${item.section_number}` :
                                        item.title
                                    const subtitle = activePillar === 'playbook' ? `${item.condition} ${item.threshold_value}` :
                                        activePillar === 'statutes' ? `Clause: ${item.clause_type}` :
                                        `Affects: ${(item.affected_clause_types || []).join(', ')}`

                                    return (
                                        <button
                                            key={id}
                                            onClick={() => setSelectedId(isSelected ? null : id)}
                                            className={`w-full text-left px-4 py-3 transition-colors ${
                                                isSelected ? `${cfg.bg} border-l-4 ${cfg.border.replace('border-', 'border-l-')}` : 'hover:bg-gray-50 border-l-4 border-transparent'
                                            }`}
                                        >
                                            <div className="flex items-start justify-between gap-2">
                                                <div className="flex-1 min-w-0">
                                                    <p className={`text-sm font-medium truncate ${isSelected ? cfg.text : 'text-gray-900'}`}>
                                                        {title}
                                                    </p>
                                                    <p className="text-xs text-gray-400 mt-0.5 truncate">{subtitle}</p>
                                                </div>
                                                {activePillar === 'playbook' && (
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full shrink-0 ${
                                                        item.severity === 'critical' ? 'bg-red-100 text-red-600' :
                                                        item.severity === 'high' ? 'bg-orange-100 text-orange-600' :
                                                        'bg-yellow-100 text-yellow-600'
                                                    }`}>
                                                        {item.severity}
                                                    </span>
                                                )}
                                                {activePillar === 'statutes' && (
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-600 shrink-0">
                                                        {item.enforceability_score}
                                                    </span>
                                                )}
                                            </div>
                                        </button>
                                    )
                                })
                            )}
                        </div>
                    </div>

                    {/* Right: Impact Panel or Empty State */}
                    <div className="col-span-8">
                        <AnimatePresence mode="wait">
                            {selectedId && impactData ? (
                                <ImpactPanel
                                    key={selectedId}
                                    data={impactData}
                                    pillar={activePillar}
                                    onClose={() => setSelectedId(null)}
                                />
                            ) : (
                                <motion.div
                                    key="empty"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="bg-white rounded-xl border border-gray-200 p-12 text-center h-full flex flex-col items-center justify-center min-h-[400px]"
                                >
                                    <div className={`w-16 h-16 rounded-full ${cfg.bg} flex items-center justify-center mb-4`}>
                                        <cfg.icon size={28} className={cfg.text} />
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                        {cfg.label} Impact Analysis
                                    </h3>
                                    <p className="text-sm text-gray-500 max-w-md">
                                        Select a {cfg.label.toLowerCase()} item from the sidebar to see which contracts are affected.
                                        All queries run in PostgreSQL — no Neo4j required.
                                    </p>

                                    <div className="mt-6 flex items-center gap-4 text-xs text-gray-400">
                                        <span className="flex items-center gap-1">
                                            <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                                            {cfg.label} node
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <div className="w-2 h-2 rounded-full bg-gray-400" />
                                            Contract
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <div className="w-2 h-2 rounded-full bg-yellow-400" />
                                            Clause
                                        </span>
                                    </div>

                                    {/* Stats cards */}
                                    <div className="grid grid-cols-3 gap-4 mt-8 w-full max-w-lg">
                                        <div className="bg-gray-50 rounded-lg p-4 text-center">
                                            <p className="text-2xl font-bold text-gray-900">
                                                {pillars?.length || 0}
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">{cfg.label} Rules</p>
                                        </div>
                                        <div className="bg-gray-50 rounded-lg p-4 text-center">
                                            <p className="text-2xl font-bold text-gray-900">—</p>
                                            <p className="text-xs text-gray-500 mt-1">Select an item</p>
                                        </div>
                                        <div className="bg-gray-50 rounded-lg p-4 text-center">
                                            <p className="text-2xl font-bold text-gray-900">—</p>
                                            <p className="text-xs text-gray-500 mt-1">to see impact</p>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
                </>
            )}

            {viewMode === 'network' && (
                <div className="space-y-4">
                    {/* Network Pillar Filter */}
                    <div className="flex items-center gap-2">
                        {[
                            { key: 'all', label: 'All Pillars', count: networkData?.stats ? (networkData.stats.contracts + networkData.stats.clauses + networkData.stats.rules + networkData.stats.statutes + networkData.stats.regulations) : 0 },
                            { key: 'playbook', label: 'Playbook', count: networkData?.stats?.rules || 0 },
                            { key: 'law', label: 'Law', count: networkData?.stats?.statutes || 0 },
                            { key: 'regulatory', label: 'Regulatory', count: networkData?.stats?.regulations || 0 },
                        ].map(p => (
                            <button
                                key={p.key}
                                onClick={() => setNetworkPillar(p.key)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                                    networkPillar === p.key
                                        ? 'bg-primary text-white shadow-sm'
                                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                                }`}
                            >
                                {p.label}
                                <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${networkPillar === p.key ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'}`}>
                                    {p.count}
                                </span>
                            </button>
                        ))}
                    </div>

                    {networkLoading ? (
                        <div className="h-[700px] bg-gray-100 rounded-xl border border-gray-200 animate-pulse flex items-center justify-center">
                            <p className="text-gray-400 text-sm">Building network graph...</p>
                        </div>
                    ) : networkData?.nodes?.length ? (
                        <>
                            <GraphNetwork nodes={networkData.nodes} edges={networkData.edges} />
                            {/* Floating Legend */}
                            <div className="flex flex-wrap items-center gap-3 text-xs bg-white rounded-lg border border-gray-200 p-3">
                                <span className="font-medium text-gray-700 mr-1">Legend:</span>
                                <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-blue-500" /> Contract</span>
                                {networkPillar !== 'regulatory' && (
                                    <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-gray-400" /> Clause</span>
                                )}
                                {networkPillar !== 'law' && networkPillar !== 'regulatory' && (
                                    <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-green-500" /> Playbook Rule</span>
                                )}
                                {networkPillar !== 'playbook' && networkPillar !== 'regulatory' && (
                                    <>
                                    <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-amber-500" /> Statute Risk</span>
                                    <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-indigo-500" /> Statute OK</span>
                                    </>
                                )}
                                {networkPillar !== 'playbook' && networkPillar !== 'law' && (
                                    <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-pink-500" /> Regulation</span>
                                )}
                            </div>
                            {/* Stats */}
                            <div className="grid grid-cols-5 gap-3">
                                {[
                                    { label: 'Contracts', value: networkData.stats.contracts, color: 'bg-blue-50 text-blue-700' },
                                    ...(networkPillar !== 'regulatory' ? [{ label: 'Clauses', value: networkData.stats.clauses, color: 'bg-gray-50 text-gray-700' }] : []),
                                    ...(networkPillar !== 'law' && networkPillar !== 'regulatory' ? [{ label: 'Rules', value: networkData.stats.rules, color: 'bg-green-50 text-green-700' }] : []),
                                    ...(networkPillar !== 'playbook' && networkPillar !== 'regulatory' ? [{ label: 'Statutes', value: networkData.stats.statutes, color: 'bg-amber-50 text-amber-700' }] : []),
                                    ...(networkPillar !== 'playbook' && networkPillar !== 'law' ? [{ label: 'Regulations', value: networkData.stats.regulations, color: 'bg-pink-50 text-pink-700' }] : []),
                                ].map(s => (
                                    <div key={s.label} className={`${s.color.split(' ')[0]} rounded-lg p-3 text-center border border-gray-100`}>
                                        <p className="text-xl font-bold">{s.value}</p>
                                        <p className={`text-xs mt-0.5 ${s.color.split(' ')[1]}`}>{s.label}</p>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div className="h-[700px] bg-gray-50 rounded-xl border border-gray-200 flex items-center justify-center">
                            <p className="text-gray-400 text-sm">No network data available</p>
                        </div>
                    )}
                </div>
            )}

            {/* Neo4j note */}
            <div className="bg-gray-50 rounded-lg p-4 flex items-start gap-3 text-sm">
                <AlertOctagon size={16} className="text-gray-400 mt-0.5 shrink-0" />
                <div>
                    <p className="font-medium text-gray-700">Neo4j Graph Layer (Optional)</p>
                    <p className="text-gray-500 mt-0.5">
                        The 3-Pillar Impact Engine runs entirely on PostgreSQL. Neo4j is available as an optional graph visualization layer.
                        If Neo4j is running, you can also explore contract networks at <code>/graph/contracts/&#123;id&#125;/network</code>.
                    </p>
                </div>
            </div>
        </div>
    )
}
