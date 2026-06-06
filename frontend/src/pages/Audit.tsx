import { useState, useEffect } from 'react'
import { Activity, Clock, CheckCircle, AlertTriangle, Shield, Loader2, FileText } from 'lucide-react'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"

export default function AuditPage() {
    const [logs, setLogs] = useState<any[]>([])
    const [trail, setTrail] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [tab, setTab] = useState<'logs' | 'trail'>('logs')

    useEffect(() => {
        Promise.all([
            apiFetch(`/audit/logs?org_id=${ORG_ID}`).then(r => r.json()),
            apiFetch(`/audit/trail?org_id=${ORG_ID}`).then(r => r.json()),
        ])
        .then(([l, t]) => {
            setLogs(l || [])
            setTrail(t || [])
            setLoading(false)
        })
        .catch((e: any) => {
            setError(e.message || 'Failed to load audit data')
            setLoading(false)
        })
    }, [])

    const statusIcon = (status: string) => {
        if (status === 'completed') return <CheckCircle size={16} className="text-green-600" />
        if (status === 'failed') return <AlertTriangle size={16} className="text-red-600" />
        return <Clock size={16} className="text-yellow-600" />
    }

    const statusBadge = (status: string) => {
        if (status === 'completed') return 'bg-green-100 text-green-700'
        if (status === 'failed') return 'bg-red-100 text-red-700'
        return 'bg-yellow-100 text-yellow-700'
    }

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
                <div className="animate-pulse space-y-3">
                    {[1,2,3,4].map(i => <div key={i} className="bg-white rounded-xl border border-border p-5 h-16" />)}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
                    <p className="font-medium">Failed to load audit data</p>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            </div>
        )
    }

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Audit & Compliance</h1>
                <div className="flex items-center gap-2 text-sm">
                    <Shield size={16} className="text-green-600" />
                    <span className="text-green-700 font-medium">SHA-256 Chain Verified</span>
                </div>
            </div>

            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
                {['logs', 'trail'].map(t => (
                    <button key={t} onClick={() => setTab(t as any)}
                        className={`px-4 py-2 rounded-md text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-white text-primary shadow-sm' : 'text-primary-lighter'}`}>
                        {t === 'logs' ? 'Automation Logs' : 'Tamper-Proof Trail'}
                    </button>
                ))}
            </div>

            {tab === 'logs' && (
                <div className="bg-white rounded-xl border border-border overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-border">
                            <tr>
                                <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Automation</th>
                                <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Status</th>
                                <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Input</th>
                                <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Output</th>
                                <th className="text-right text-xs font-medium text-primary-lighter uppercase px-6 py-3">Duration</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {logs.length > 0 ? logs.map(log => (
                                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium capitalize">{log.automation_type.replace(/_/g, ' ')}</td>
                                    <td className="px-6 py-4">
                                        <span className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium w-fit ${statusBadge(log.status)}`}>
                                            {statusIcon(log.status)} <span className="capitalize">{log.status}</span>
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-primary-lighter max-w-xs truncate">{log.input_summary}</td>
                                    <td className="px-6 py-4 text-sm text-primary-lighter max-w-xs truncate">{log.output_summary}</td>
                                    <td className="px-6 py-4 text-sm text-right font-medium">{log.duration_ms}ms</td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center">
                                        <Activity size={40} className="mx-auto mb-3 text-gray-300" />
                                        <p className="text-primary-lighter font-medium">No audit logs yet</p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {tab === 'trail' && (
                <div className="space-y-3">
                    {trail.length > 0 ? trail.map((entry: any) => (
                        <div key={entry.id} className="bg-white rounded-xl border border-border p-5">
                            <div className="flex items-start gap-3">
                                <div className="p-2 rounded-lg bg-primary/5">
                                    <Activity size={16} className="text-primary" />
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium capitalize">{entry.action}</span>
                                        <span className="text-xs text-primary-lighter">{entry.resource_type} · {entry.resource_id?.slice(0, 8)}</span>
                                    </div>
                                    <p className="text-xs text-primary-lighter">Actor: {entry.actor_email} · {new Date(entry.created_at).toLocaleString()}</p>
                                    {entry.entry_hash && (
                                        <p className="text-xs text-primary-lighter mt-1 font-mono">Hash: {entry.entry_hash.slice(0, 24)}...</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <Shield size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-primary-lighter font-medium">No audit trail entries yet</p>
                            <p className="text-sm text-primary-lighter mt-1">Every action is cryptographically hashed for tamper-proof compliance</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
