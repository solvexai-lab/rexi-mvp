import { useState, useEffect } from 'react'
import { Layers, Copy, CheckCircle, Loader2, FileText, Search, Plus, Trash2, Edit3, X, Save, AlertTriangle } from 'lucide-react'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"
import { showToast } from '../hooks/useToast'

interface Template {
    id: string
    name: string
    category: string
    content: string
    variables?: Record<string, string>
}

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([])
    const [copied, setCopied] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [error, setError] = useState<string | null>(null)

    // Create / Edit modal
    const [showForm, setShowForm] = useState(false)
    const [editingId, setEditingId] = useState<string | null>(null)
    const [formName, setFormName] = useState('')
    const [formCategory, setFormCategory] = useState('vendor')
    const [formContent, setFormContent] = useState('')
    const [saving, setSaving] = useState(false)
    const [deleting, setDeleting] = useState<string | null>(null)

    const loadTemplates = async () => {
        setLoading(true)
        setError(null)
        try {
            const r = await apiFetch(`/templates?org_id=${ORG_ID}`)
            if (!r.ok) throw new Error('Failed to load')
            setTemplates(await r.json())
        } catch (e: any) {
            setError(e.message || 'Failed to load templates')
        }
        setLoading(false)
    }

    useEffect(() => { loadTemplates() }, [])

    const openCreate = () => {
        setEditingId(null)
        setFormName('')
        setFormCategory('vendor')
        setFormContent('')
        setShowForm(true)
    }

    const openEdit = (t: Template) => {
        setEditingId(t.id)
        setFormName(t.name)
        setFormCategory(t.category)
        setFormContent(t.content)
        setShowForm(true)
    }

    const saveTemplate = async () => {
        if (!formName.trim() || !formContent.trim()) return
        setSaving(true)
        try {
            const body = {
                org_id: ORG_ID,
                name: formName,
                category: formCategory,
                content: formContent,
                variables: {},
            }
            const url = editingId ? `/templates/${editingId}` : '/templates'
            const method = editingId ? 'PUT' : 'POST'
            const r = await apiFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })
            if (!r.ok) throw new Error('Save failed')
            showToast(editingId ? 'Template updated' : 'Template created', 'success')
            setShowForm(false)
            loadTemplates()
        } catch {
            showToast('Failed to save template', 'error')
        }
        setSaving(false)
    }

    const deleteTemplate = async (id: string) => {
        if (!confirm('Delete this template?')) return
        setDeleting(id)
        try {
            const r = await apiFetch(`/templates/${id}`, { method: 'DELETE' })
            if (!r.ok) throw new Error('Delete failed')
            showToast('Template deleted', 'success')
            loadTemplates()
        } catch {
            showToast('Failed to delete', 'error')
        }
        setDeleting(null)
    }

    const copyContent = (content: string, id: string) => {
        navigator.clipboard.writeText(content)
        setCopied(id)
        setTimeout(() => setCopied(null), 2000)
    }

    const filtered = templates.filter(t =>
        !search || t.name?.toLowerCase().includes(search.toLowerCase()) || t.category?.toLowerCase().includes(search.toLowerCase())
    )

    if (loading && templates.length === 0) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Contract Templates</h1>
                <div className="animate-pulse space-y-4">
                    {[1,2,3].map(i => <div key={i} className="bg-white rounded-xl border border-border p-6 h-48" />)}
                </div>
            </div>
        )
    }

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Contract Templates</h1>
                <div className="flex items-center gap-3">
                    <div className="relative w-64">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-primary-lighter" />
                        <input
                            type="text"
                            placeholder="Search templates..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <button
                        onClick={openCreate}
                        className="px-3 py-2 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light"
                    >
                        <Plus size={16} /> New
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
                    <AlertTriangle size={18} className="text-red-600" />
                    <p className="text-sm text-red-700">{error}</p>
                    <button onClick={loadTemplates} className="ml-auto text-sm text-red-700 underline">Retry</button>
                </div>
            )}

            <div className="grid grid-cols-1 gap-4">
                {filtered.length > 0 ? filtered.map(t => (
                    <div key={t.id} className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="font-semibold text-lg">{t.name}</h3>
                                <span className="text-xs text-primary-lighter uppercase bg-gray-100 px-2 py-1 rounded-full mt-1 inline-block">{t.category}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => openEdit(t)}
                                    className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-blue-600 transition-colors"
                                    title="Edit"
                                >
                                    <Edit3 size={16} />
                                </button>
                                <button
                                    onClick={() => deleteTemplate(t.id)}
                                    disabled={deleting === t.id}
                                    className="p-2 hover:bg-red-50 rounded-lg text-gray-500 hover:text-red-600 transition-colors disabled:opacity-50"
                                    title="Delete"
                                >
                                    {deleting === t.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                </button>
                                <button
                                    onClick={() => copyContent(t.content, t.id)}
                                    className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border border-border hover:bg-gray-50 transition-colors"
                                >
                                    {copied === t.id ? <><CheckCircle size={16} className="text-green-600" /> Copied</> : <><Copy size={16} /> Copy</>}
                                </button>
                            </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4 font-mono text-xs text-primary-lighter whitespace-pre-wrap max-h-64 overflow-y-auto border border-border">
                            {t.content}
                        </div>
                        {t.variables && Object.keys(t.variables).length > 0 && (
                            <div className="mt-4 flex flex-wrap gap-2">
                                <span className="text-xs text-primary-lighter mr-1">Variables:</span>
                                {Object.keys(t.variables).map((v: string) => (
                                    <span key={v} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">{`{${v}}`}</span>
                                ))}
                            </div>
                        )}
                    </div>
                )) : (
                    <div className="bg-white rounded-xl border border-border p-12 text-center">
                        <FileText size={40} className="mx-auto mb-3 text-gray-300" />
                        <p className="text-primary-lighter font-medium">
                            {search ? 'No templates match your search' : 'No templates available'}
                        </p>
                    </div>
                )}
            </div>

            {/* Create/Edit Modal */}
            {showForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                    <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-auto p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold">{editingId ? 'Edit Template' : 'New Template'}</h2>
                            <button onClick={() => setShowForm(false)} className="p-1 hover:bg-gray-100 rounded">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-1 block">Name</label>
                                <input
                                    type="text"
                                    value={formName}
                                    onChange={e => setFormName(e.target.value)}
                                    className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g. Vendor Agreement Template"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-1 block">Category</label>
                                <select
                                    value={formCategory}
                                    onChange={e => setFormCategory(e.target.value)}
                                    className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {['vendor', 'nda', 'employment', 'lease', 'service', 'partnership', 'license'].map(c => (
                                        <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-1 block">Content</label>
                                <textarea
                                    value={formContent}
                                    onChange={e => setFormContent(e.target.value)}
                                    rows={12}
                                    className="w-full px-3 py-2 border border-border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Paste contract template text here..."
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-2">
                                <button onClick={() => setShowForm(false)} className="px-4 py-2 border border-border rounded-lg text-sm hover:bg-gray-50">
                                    Cancel
                                </button>
                                <button
                                    onClick={saveTemplate}
                                    disabled={saving || !formName.trim() || !formContent.trim()}
                                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                                >
                                    {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                                    {editingId ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
