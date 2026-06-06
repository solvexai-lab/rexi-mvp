import { useState, useEffect } from 'react'
import { Gavel, Plus, Trash2, Check, X, Loader2, Shield } from 'lucide-react'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"

const RULE_TYPES = [
    "termination", "liability", "indemnity", "payment", "confidentiality",
    "governing_law", "force_majeure", "non_compete", "intellectual_property",
    "data_processing", "dispute_resolution", "assignment", "amendment", "warranty"
]

const CONDITIONS = ["must_have", "max_value", "min_value", "must_not_have"]
const SEVERITIES = ["critical", "high", "medium", "low"]

function SkeletonRow() {
    return (
        <tr className="animate-pulse">
            <td className="px-6 py-4"><div className="h-4 w-32 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-20 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-20 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-16 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-16 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-12 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-8 bg-gray-200 rounded ml-auto" /></td>
        </tr>
    )
}

export default function PlaybookPage() {
    const [rules, setRules] = useState<any[]>([])
    const [form, setForm] = useState<any>({
        rule_name: '', rule_type: RULE_TYPES[0], condition: CONDITIONS[0],
        threshold_value: '', severity: 'high', is_active: true
    })
    const [showAdd, setShowAdd] = useState(false)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [saving, setSaving] = useState(false)
    const [deleting, setDeleting] = useState<string | null>(null)

    useEffect(() => { loadRules() }, [])

    const loadRules = async () => {
        setLoading(true)
        setError(null)
        try {
            const r = await apiFetch(`/playbook/rules?org_id=${ORG_ID}`)
            if (!r.ok) throw new Error('Failed to load')
            setRules(await r.json())
        } catch (e: any) {
            setError(e.message || 'Failed to load playbook rules')
        }
        setLoading(false)
    }

    const saveRule = async () => {
        setSaving(true)
        await apiFetch(`/playbook/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...form, org_id: ORG_ID })
        })
        setShowAdd(false)
        setForm({ rule_name: '', rule_type: RULE_TYPES[0], condition: CONDITIONS[0], threshold_value: '', severity: 'high', is_active: true })
        await loadRules()
        setSaving(false)
    }

    const deleteRule = async (id: string) => {
        setDeleting(id)
        await apiFetch(`/playbook/rules/${id}`, { method: 'DELETE' })
        await loadRules()
        setDeleting(null)
    }

    const severityBadge = (s: string) => {
        if (s === 'critical') return 'bg-red-100 text-red-700'
        if (s === 'high') return 'bg-orange-100 text-orange-700'
        if (s === 'medium') return 'bg-yellow-100 text-yellow-700'
        return 'bg-blue-100 text-blue-700'
    }

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Playbook Rules</h1>
                <button onClick={() => setShowAdd(true)} className="bg-primary text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-light transition-colors">
                    <Plus size={18} /> Add Rule
                </button>
            </div>

            {showAdd && (
                <div className="bg-white rounded-xl border border-border p-6 mb-6">
                    <h3 className="font-semibold mb-4">New Rule</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs text-primary-lighter uppercase font-medium">Rule Name</label>
                            <input value={form.rule_name} onChange={e => setForm({...form, rule_name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. Max Liability Cap" />
                        </div>
                        <div>
                            <label className="text-xs text-primary-lighter uppercase font-medium">Clause Type</label>
                            <select value={form.rule_type} onChange={e => setForm({...form, rule_type: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                {RULE_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-primary-lighter uppercase font-medium">Condition</label>
                            <select value={form.condition} onChange={e => setForm({...form, condition: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                {CONDITIONS.map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-primary-lighter uppercase font-medium">Threshold / Value</label>
                            <input value={form.threshold_value} onChange={e => setForm({...form, threshold_value: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. 2000000" />
                        </div>
                        <div>
                            <label className="text-xs text-primary-lighter uppercase font-medium">Severity</label>
                            <select value={form.severity} onChange={e => setForm({...form, severity: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                        <button onClick={saveRule} disabled={saving} className="bg-primary text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 disabled:opacity-50">
                            {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} Save
                        </button>
                        <button onClick={() => setShowAdd(false)} className="border border-border px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-50">
                            <X size={16} /> Cancel
                        </button>
                    </div>
                </div>
            )}

            <div className="bg-white rounded-xl border border-border overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-border">
                        <tr>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Rule Name</th>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Type</th>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Condition</th>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Threshold</th>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Severity</th>
                            <th className="text-left text-xs font-medium text-primary-lighter uppercase px-6 py-3">Status</th>
                            <th className="text-right text-xs font-medium text-primary-lighter uppercase px-6 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {loading ? (
                            <><SkeletonRow /><SkeletonRow /><SkeletonRow /></>
                        ) : rules.length > 0 ? rules.map(r => (
                            <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 text-sm font-medium">{r.rule_name}</td>
                                <td className="px-6 py-4 text-sm capitalize">{r.rule_type.replace('_', ' ')}</td>
                                <td className="px-6 py-4 text-sm capitalize">{r.condition.replace('_', ' ')}</td>
                                <td className="px-6 py-4 text-sm">{r.threshold_value}</td>
                                <td className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${severityBadge(r.severity)}`}>{r.severity}</span></td>
                                <td className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs font-medium ${r.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>{r.is_active ? 'Active' : 'Inactive'}</span></td>
                                <td className="px-6 py-4 text-right">
                                    <button onClick={() => deleteRule(r.id)} disabled={deleting === r.id} className="text-red-600 hover:text-red-800 disabled:opacity-50">
                                        {deleting === r.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                    </button>
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan={7} className="px-6 py-12 text-center">
                                    <Shield size={40} className="mx-auto mb-3 text-gray-300" />
                                    <p className="text-primary-lighter font-medium">No playbook rules yet</p>
                                    <p className="text-sm text-primary-lighter mt-1">Create your first rule to start auto-checking contracts</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
