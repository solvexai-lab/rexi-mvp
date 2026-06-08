import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ClipboardList, CheckCircle, Clock, AlertTriangle, Loader2, CalendarDays, LayoutList, ArrowRight } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"

function SkeletonCard() {
    return <div className="bg-white rounded-xl border border-border p-6 animate-pulse">
        <div className="h-10 w-10 rounded-lg bg-gray-200 mb-3" />
        <div className="h-8 w-20 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-32 bg-gray-200 rounded" />
    </div>
}

/* ─── Timeline helpers ─── */
function parseDate(d: string | null): Date | null {
    if (!d) return null
    const parsed = new Date(d)
    return isNaN(parsed.getTime()) ? null : parsed
}

function formatDate(d: Date | null): string {
    if (!d) return '-'
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function daysBetween(a: Date, b: Date): number {
    return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24))
}

/* ─── Gantt Timeline Component ─── */
function TimelineView({ obligations, contracts }: { obligations: any[]; contracts: any[] }) {
    const { rows, minDate, maxDate, totalDays } = useMemo(() => {
        const withDates = obligations
            .map(o => ({ ...o, dateObj: parseDate(o.due_date) }))
            .filter(o => o.dateObj)
            .sort((a, b) => (a.dateObj!.getTime() - b.dateObj!.getTime()))

        if (withDates.length === 0) return { rows: [], minDate: null, maxDate: null, totalDays: 0 }

        const dates = withDates.map(o => o.dateObj!)
        const min = new Date(Math.min(...dates.map(d => d.getTime())))
        const max = new Date(Math.max(...dates.map(d => d.getTime())))
        // Add padding
        min.setDate(min.getDate() - 7)
        max.setDate(max.getDate() + 14)
        const days = daysBetween(min, max)

        return { rows: withDates, minDate: min, maxDate: max, totalDays: days }
    }, [obligations])

    if (!minDate || rows.length === 0) {
        return (
            <div className="bg-white rounded-xl border border-border p-12 text-center">
                <CalendarDays size={40} className="mx-auto text-gray-300 mb-3" />
                <p className="text-gray-500">No dated obligations to display</p>
            </div>
        )
    }

    const today = new Date()
    const todayOffset = daysBetween(minDate, today)
    const showToday = todayOffset >= 0 && todayOffset <= totalDays

    return (
        <div className="bg-white rounded-xl border border-border overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                    <CalendarDays size={18} className="text-primary" />
                    Obligation Timeline
                </h2>
                <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />Pending</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />Completed</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Overdue</span>
                </div>
            </div>
            <div className="p-5 overflow-x-auto">
                <div className="min-w-[600px]">
                    {/* Month headers */}
                    <div className="flex border-b border-gray-100 pb-2 mb-2">
                        <div className="w-48 shrink-0 text-xs font-medium text-gray-500 uppercase">Obligation</div>
                        <div className="flex-1 relative h-6">
                            {Array.from({ length: totalDays + 1 }, (_, i) => {
                                const d = new Date(minDate)
                                d.setDate(d.getDate() + i)
                                if (d.getDate() === 1 || i === 0) {
                                    const left = (i / totalDays) * 100
                                    return (
                                        <span key={i} className="absolute text-[10px] text-gray-400 -translate-x-1/2" style={{ left: `${left}%` }}>
                                            {d.toLocaleDateString('en-IN', { month: 'short' })}
                                        </span>
                                    )
                                }
                                return null
                            })}
                        </div>
                    </div>

                    {/* Today marker line */}
                    {showToday && (
                        <div className="flex mb-1">
                            <div className="w-48 shrink-0" />
                            <div className="flex-1 relative h-0">
                                <div
                                    className="absolute top-0 bottom-0 w-px bg-primary/40 border-l border-dashed border-primary"
                                    style={{ left: `${(todayOffset / totalDays) * 100}%` }}
                                >
                                    <span className="absolute -top-4 -translate-x-1/2 text-[10px] text-primary font-medium whitespace-nowrap">Today</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Rows */}
                    <div className="space-y-2">
                        {rows.map((o, i) => {
                            const offset = daysBetween(minDate, o.dateObj!)
                            const left = Math.max(0, Math.min(100, (offset / totalDays) * 100))
                            const color = o.status === 'completed' ? 'bg-green-500' : o.status === 'overdue' ? 'bg-red-500' : 'bg-yellow-500'
                            const contract = contracts?.find((c: any) => c.id === o.contract_id)
                            return (
                                <motion.div
                                    key={o.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="flex items-center group"
                                >
                                    <div className="w-48 shrink-0 pr-3">
                                        <p className="text-xs font-medium text-gray-900 truncate">{o.description}</p>
                                        <p className="text-[10px] text-gray-400 truncate">{contract?.title || o.contract_id.slice(0, 8)}</p>
                                    </div>
                                    <div className="flex-1 relative h-6 bg-gray-50 rounded-full overflow-visible">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.max(1, (1 - left / 100) * 100)}%` }}
                                            transition={{ duration: 0.8, delay: i * 0.05 }}
                                            className={`absolute left-0 top-1/2 -translate-y-1/2 h-3 rounded-full ${color} opacity-20`}
                                        />
                                        <motion.div
                                            initial={{ left: `${left}%`, scale: 0 }}
                                            animate={{ left: `${left}%`, scale: 1 }}
                                            transition={{ duration: 0.5, delay: i * 0.05 + 0.2, type: 'spring' }}
                                            className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full ${color} border-2 border-white shadow-sm`}
                                        >
                                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                                <div className="bg-gray-900 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap">
                                                    {formatDate(o.dateObj)}
                                                </div>
                                            </div>
                                        </motion.div>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function ObligationsPage() {
    const [obligations, setObligations] = useState<any[]>([])
    const [contracts, setContracts] = useState<any[]>([])
    const [dashboard, setDashboard] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [updating, setUpdating] = useState<string | null>(null)
    const [view, setView] = useState<'list' | 'timeline'>('list')
    const navigate = useNavigate()
    const [searchParams, setSearchParams] = useSearchParams()
    const statusFilter = searchParams.get('status') || ''

    useEffect(() => { loadData() }, [statusFilter])

    const loadData = async () => {
        setLoading(true)
        try {
            const url = statusFilter
                ? `/obligations?org_id=${ORG_ID}&status=${statusFilter}`
                : `/obligations?org_id=${ORG_ID}`
            const [o, d, c] = await Promise.all([
                apiFetch(url).then(r => r.json()),
                apiFetch(`/obligations/dashboard/summary?org_id=${ORG_ID}`).then(r => r.json()),
                apiFetch(`/contracts?org_id=${ORG_ID}`).then(r => r.json()),
            ])
            setObligations(o || [])
            setDashboard(d)
            setContracts(c || [])
        } catch (e: any) {
            setError(e.message || 'Failed to load obligations')
            setLoading(false)
            return
        }
        setLoading(false)
    }

    const updateStatus = async (id: string, status: string) => {
        setUpdating(id)
        await apiFetch(`/obligations/${id}/status?status=${status}`, { method: 'PUT' })
        await loadData()
        setUpdating(null)
    }

    const statusIcon = (status: string) => {
        if (status === 'completed') return <CheckCircle size={16} className="text-green-600" />
        if (status === 'overdue') return <AlertTriangle size={16} className="text-red-600" />
        return <Clock size={16} className="text-yellow-600" />
    }

    const statusColor = (status: string) => {
        if (status === 'completed') return 'bg-green-100 text-green-700'
        if (status === 'overdue') return 'bg-red-100 text-red-700'
        return 'bg-yellow-100 text-yellow-700'
    }

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Obligations Tracker</h1>
                <div className="grid grid-cols-4 gap-6 mb-8">
                    {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="bg-white rounded-xl border border-border h-64 animate-pulse" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Obligations Tracker</h1>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
                    <AlertTriangle size={20} className="text-red-600" />
                    <p className="text-sm text-red-700">{error}</p>
                    <button onClick={() => { setError(null); loadData(); }} className="ml-auto text-sm text-red-700 underline">Retry</button>
                </div>
            </div>
        )
    }

    return (
        <div className="p-8 space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">Obligations Tracker</h1>
                <div className="flex items-center bg-white border border-gray-200 rounded-lg p-1">
                    <button
                        onClick={() => setView('list')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${view === 'list' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                        <LayoutList size={14} /> List
                    </button>
                    <button
                        onClick={() => setView('timeline')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${view === 'timeline' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                        <CalendarDays size={14} /> Timeline
                    </button>
                </div>
            </div>

            {dashboard && (
                <div className="grid grid-cols-4 gap-6">
                    <div
                        onClick={() => setSearchParams({})}
                        className={`bg-white rounded-xl border p-6 text-center cursor-pointer transition-colors ${!statusFilter ? 'border-primary ring-1 ring-primary/20' : 'border-border hover:border-primary/30'}`}
                    >
                        <ClipboardList size={20} className="mx-auto mb-2 text-blue-600" />
                        <p className="text-sm text-gray-500 mb-1">Total</p>
                        <p className="text-3xl font-bold text-blue-600">{dashboard.total}</p>
                    </div>
                    <div
                        onClick={() => setSearchParams({ status: 'pending' })}
                        className={`bg-white rounded-xl border p-6 text-center cursor-pointer transition-colors ${statusFilter === 'pending' ? 'border-primary ring-1 ring-primary/20' : 'border-border hover:border-primary/30'}`}
                    >
                        <Clock size={20} className="mx-auto mb-2 text-yellow-600" />
                        <p className="text-sm text-gray-500 mb-1">Pending</p>
                        <p className="text-3xl font-bold text-yellow-600">{dashboard.pending}</p>
                    </div>
                    <div
                        onClick={() => setSearchParams({ status: 'completed' })}
                        className={`bg-white rounded-xl border p-6 text-center cursor-pointer transition-colors ${statusFilter === 'completed' ? 'border-primary ring-1 ring-primary/20' : 'border-border hover:border-primary/30'}`}
                    >
                        <CheckCircle size={20} className="mx-auto mb-2 text-green-600" />
                        <p className="text-sm text-gray-500 mb-1">Completed</p>
                        <p className="text-3xl font-bold text-green-600">{dashboard.completed}</p>
                    </div>
                    <div
                        onClick={() => setSearchParams({ status: 'overdue' })}
                        className={`bg-white rounded-xl border p-6 text-center cursor-pointer transition-colors ${statusFilter === 'overdue' ? 'border-primary ring-1 ring-primary/20' : 'border-border hover:border-primary/30'}`}
                    >
                        <AlertTriangle size={20} className="mx-auto mb-2 text-red-600" />
                        <p className="text-sm text-gray-500 mb-1">Overdue</p>
                        <p className="text-3xl font-bold text-red-600">{dashboard.overdue}</p>
                    </div>
                </div>
            )}

            <AnimatePresence mode="wait">
                {view === 'timeline' ? (
                    <motion.div
                        key="timeline"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                    >
                        <TimelineView obligations={obligations} contracts={contracts} />
                    </motion.div>
                ) : (
                    <motion.div
                        key="list"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="bg-white rounded-xl border border-border overflow-hidden"
                    >
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-border">
                                <tr>
                                    <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Description</th>
                                    <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Type</th>
                                    <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Due Date</th>
                                    <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Status</th>
                                    <th className="text-right text-xs font-medium text-gray-500 uppercase px-6 py-3">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {obligations.map(o => (
                                    <tr
                                        key={o.id}
                                        onClick={() => navigate(`/contracts/${o.contract_id}?tab=obligations`)}
                                        className="hover:bg-gray-50 transition-colors cursor-pointer group"
                                    >
                                        <td className="px-6 py-4 text-sm max-w-md truncate">
                                            <div className="flex items-center gap-2">
                                                {o.description}
                                                <ArrowRight size={14} className="text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm capitalize">{o.obligation_type}</td>
                                        <td className="px-6 py-4 text-sm">{o.due_date || '-'}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize flex items-center gap-1 w-fit ${statusColor(o.status)}`}>
                                                {statusIcon(o.status)} {o.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right" onClick={e => e.stopPropagation()}>
                                            {o.status !== 'completed' ? (
                                                <button
                                                    onClick={() => updateStatus(o.id, 'completed')}
                                                    disabled={updating === o.id}
                                                    className="text-xs bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center gap-1 ml-auto"
                                                >
                                                    {updating === o.id ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle size={12} />}
                                                    Mark Done
                                                </button>
                                            ) : (
                                                <span className="text-xs text-green-600 font-medium">Completed</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                {obligations.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center">
                                            <ClipboardList size={40} className="mx-auto mb-3 text-gray-300" />
                                            <p className="text-gray-500 font-medium">No obligations tracked yet</p>
                                            <p className="text-sm text-gray-500 mt-1">Upload a contract to auto-extract obligations</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
