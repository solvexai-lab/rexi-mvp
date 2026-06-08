import { useState, useEffect } from 'react'
import { Bell, AlertTriangle, CheckCircle, Loader2, FileText } from 'lucide-react'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"

export default function RegulatoryPage() {
    const [alerts, setAlerts] = useState<any[]>([])
    const [updates, setUpdates] = useState<any[]>([])
    const [dashboard, setDashboard] = useState<any>(null)
    const [tab, setTab] = useState('alerts')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [acknowledging, setAcknowledging] = useState<string | null>(null)

    useEffect(() => {
        Promise.all([
            apiFetch(`/regulatory/alerts?org_id=${ORG_ID}`).then(r => r.json()),
            apiFetch(`/regulatory/updates`).then(r => r.json()),
            apiFetch(`/regulatory/dashboard?org_id=${ORG_ID}`).then(r => r.json()),
        ])
        .then(([a, u, d]) => {
            setAlerts(a || [])
            setUpdates(u || [])
            setDashboard(d)
            setLoading(false)
        })
        .catch((e: any) => {
            setError(e.message || 'Failed to load regulatory data')
            setLoading(false)
        })
    }, [])

    const acknowledge = async (id: string) => {
        setAcknowledging(id)
        await apiFetch(`/regulatory/alerts/${id}/acknowledge`, { method: 'PUT' })
        setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'acknowledged' } : a))
        setAcknowledging(null)
    }

    const priorityColor = (p: string) => {
        if (p === 'critical') return 'border-l-4 border-red-500'
        if (p === 'high') return 'border-l-4 border-orange-500'
        if (p === 'medium') return 'border-l-4 border-yellow-500'
        return 'border-l-4 border-blue-500'
    }

    const priorityBadge = (p: string) => {
        if (p === 'critical') return 'bg-red-100 text-red-700'
        if (p === 'high') return 'bg-orange-100 text-orange-700'
        if (p === 'medium') return 'bg-yellow-100 text-yellow-700'
        return 'bg-blue-100 text-blue-700'
    }

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Regulatory Intelligence</h1>
                <div className="animate-pulse space-y-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="bg-white rounded-xl border border-border p-5 h-32" />
                    ))}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Regulatory Intelligence</h1>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
                    <p className="font-medium">Failed to load regulatory data</p>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            </div>
        )
    }

    const unreadCount = alerts.filter(a => a.status === 'unread').length

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Regulatory Intelligence</h1>
                {unreadCount > 0 && (
                    <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                        {unreadCount} unread
                    </span>
                )}
            </div>

            {/* Dashboard Stats */}
            {dashboard && (
                <div className="grid grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-xl border border-border p-5 text-center">
                        <p className="text-sm text-gray-500">Total Alerts</p>
                        <p className="text-2xl font-bold">{dashboard.total_alerts}</p>
                    </div>
                    <div className="bg-white rounded-xl border border-border p-5 text-center">
                        <p className="text-sm text-gray-500">Unread</p>
                        <p className="text-2xl font-bold text-red-600">{dashboard.unread}</p>
                    </div>
                    <div className="bg-white rounded-xl border border-border p-5 text-center">
                        <p className="text-sm text-gray-500">Updates</p>
                        <p className="text-2xl font-bold">{updates.length}</p>
                    </div>
                    <div className="bg-white rounded-xl border border-border p-5 text-center">
                        <p className="text-sm text-gray-500">Critical</p>
                        <p className="text-2xl font-bold text-red-600">{dashboard.by_priority?.critical || 0}</p>
                    </div>
                </div>
            )}

            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
                {['alerts', 'updates'].map(t => (
                    <button key={t} onClick={() => setTab(t)}
                        className={`px-4 py-2 rounded-md text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-white text-primary shadow-sm' : 'text-gray-500'}`}>
                        {t}
                    </button>
                ))}
            </div>

            {tab === 'alerts' && (
                <div className="space-y-3">
                    {alerts.length > 0 ? alerts.map(a => (
                        <div key={a.id} className={`bg-white rounded-xl border border-border p-5 ${priorityColor(a.priority)}`}>
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Bell size={16} className={a.priority === 'critical' ? 'text-red-600' : 'text-gray-500'} />
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${priorityBadge(a.priority)}`}>{a.priority}</span>
                                        {a.status === 'unread' && <span className="w-2 h-2 bg-blue-600 rounded-full" />}
                                    </div>
                                    <h3 className="font-semibold mb-1">{a.title}</h3>
                                    <p className="text-sm text-gray-500 mb-3">{a.description}</p>
                                    {a.suggested_actions?.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            {a.suggested_actions.map((action: string, i: number) => (
                                                <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">{action}</span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                {a.status === 'unread' && (
                                    <button
                                        onClick={() => acknowledge(a.id)}
                                        disabled={acknowledging === a.id}
                                        className="ml-4 px-3 py-1.5 bg-primary text-white text-xs rounded-lg hover:bg-primary-light transition-colors disabled:opacity-50"
                                    >
                                        {acknowledging === a.id ? <Loader2 size={12} className="animate-spin" /> : 'Ack'}
                                    </button>
                                )}
                            </div>
                        </div>
                    )) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <Bell size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-gray-500">No regulatory alerts</p>
                        </div>
                    )}
                </div>
            )}

            {tab === 'updates' && (
                <div className="space-y-3">
                    {updates.length > 0 ? updates.map(u => (
                        <div key={u.id} className="bg-white rounded-xl border border-border p-5">
                            <h3 className="font-semibold mb-1">{u.title}</h3>
                            <p className="text-sm text-gray-500 mb-2">{u.summary}</p>
                            <div className="flex items-center gap-3">
                                {u.effective_date && <span className="text-xs text-gray-500">Effective: {u.effective_date}</span>}
                                {u.affected_clause_types?.length > 0 && (
                                    <div className="flex gap-1">
                                        {u.affected_clause_types.map((ct: string, i: number) => (
                                            <span key={i} className="px-2 py-0.5 bg-primary/5 rounded text-xs capitalize">{ct.replace('_', ' ')}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <FileText size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-gray-500">No regulatory updates</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
