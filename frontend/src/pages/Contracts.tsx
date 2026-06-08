import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { Upload, FileText, AlertTriangle, Search, X, CheckCircle, Loader2, TreePine, Database, FileCheck, Trash2 } from 'lucide-react'
import { useContracts, useUploadContract, useDeleteContract, ORG_ID } from '../hooks/useQueries'
import { showToast } from '../hooks/useToast'

const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    in_review: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-blue-100 text-blue-700',
    signed: 'bg-green-100 text-green-700',
    active: 'bg-green-100 text-green-700',
    expired: 'bg-orange-100 text-orange-700',
    terminated: 'bg-red-100 text-red-700',
    analyzed: 'bg-purple-100 text-purple-700',
}

function SkeletonRow() {
    return (
        <tr className="animate-pulse">
            <td className="px-6 py-4"><div className="h-4 w-48 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-24 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-16 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-20 bg-gray-200 rounded" /></td>
            <td className="px-6 py-4"><div className="h-4 w-20 bg-gray-200 rounded" /></td>
        </tr>
    )
}

type UploadPhase = 'idle' | 'uploading' | 'processing' | 'complete' | 'error'

export default function ContractsPage() {
    const { data: contracts, isLoading } = useContracts()
    const uploadMutation = useUploadContract()
    const [search, setSearch] = useState('')
    const [typeFilter, setTypeFilter] = useState('all')
    const [uploadPhase, setUploadPhase] = useState<UploadPhase>('idle')
    const [uploadFileName, setUploadFileName] = useState('')
    const [uploadProgress, setUploadProgress] = useState(0)
    const [dragOver, setDragOver] = useState(false)
    const [uploadEnrichment, setUploadEnrichment] = useState<any>(null)
    const navigate = useNavigate()

    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    const clearProgressInterval = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
        }
    }

    useEffect(() => {
        return () => clearProgressInterval()
    }, [])

    const simulateProgress = useCallback((phase: UploadPhase) => {
        clearProgressInterval()
        setUploadPhase(phase)
        if (phase === 'uploading') {
            setUploadProgress(0)
            intervalRef.current = setInterval(() => {
                setUploadProgress(p => {
                    if (p >= 90) { clearProgressInterval(); return 90 }
                    return p + Math.random() * 15
                })
            }, 200)
        } else if (phase === 'processing') {
            setUploadProgress(90)
            intervalRef.current = setInterval(() => {
                setUploadProgress(p => {
                    if (p >= 99) { clearProgressInterval(); return 99 }
                    return p + Math.random() * 5
                })
            }, 300)
        } else if (phase === 'complete') {
            setUploadProgress(100)
        }
    }, [])

    const handleUpload = async (file: File) => {
        if (!file.name.endsWith('.pdf')) {
            showToast('Only PDF files are supported', 'error')
            return
        }
        setUploadFileName(file.name)
        setUploadEnrichment(null)
        simulateProgress('uploading')

        const form = new FormData()
        form.append('file', file)
        form.append('org_id', ORG_ID)

        simulateProgress('processing')
        uploadMutation.mutate(form, {
            onSettled: () => {
                setTimeout(() => {
                    setUploadPhase('idle')
                    setUploadEnrichment(null)
                }, 4000)
            },
            onSuccess: (data: any) => {
                simulateProgress('complete')
                setUploadEnrichment({
                    pii: data?.pii,
                    tree: data?.tree,
                    embeddings: data?.embeddings,
                })
            },
            onError: () => {
                setUploadPhase('error')
            }
        })
    }

    const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) handleUpload(file)
        e.target.value = ''
    }

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files?.[0]
        if (file) handleUpload(file)
    }

    const filtered = (contracts || []).filter((c: any) => {
        const matchesSearch = !search || c.title?.toLowerCase().includes(search.toLowerCase()) || c.counterparty_name?.toLowerCase().includes(search.toLowerCase())
        const matchesType = typeFilter === 'all' || c.contract_type === typeFilter
        return matchesSearch && matchesType
    })

    const types = ['all', ...Array.from(new Set((contracts || []).map((c: any) => c.contract_type))) as string[]]

    const deleteContract = useDeleteContract()

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Contracts</h1>
                <label
                    className="bg-primary text-white px-4 py-2 rounded-lg cursor-pointer flex items-center gap-2 hover:bg-primary-light transition-colors"
                    onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={onDrop}
                >
                    <Upload size={18} />
                    Upload Contract
                    <input type="file" accept=".pdf" className="hidden" onChange={onFileInput} />
                </label>
            </div>

            {/* Upload Progress Overlay */}
            {uploadPhase !== 'idle' && uploadPhase !== 'error' && (
                <div className="mb-6 bg-white rounded-xl border border-border p-6">
                    <div className="flex items-center gap-4 mb-3">
                        {uploadPhase === 'complete' ? (
                            <CheckCircle size={24} className="text-green-600" />
                        ) : (
                            <Loader2 size={24} className="text-blue-600 animate-spin" />
                        )}
                        <div className="flex-1">
                            <p className="font-medium">{uploadFileName}</p>
                            <p className="text-sm text-gray-500">
                                {uploadPhase === 'uploading' ? 'Uploading...' :
                                 uploadPhase === 'processing' ? 'Analyzing with AI...' :
                                 'Complete!'}
                            </p>
                        </div>
                        <span className="text-sm font-medium">{Math.round(uploadProgress)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all duration-300 ${uploadPhase === 'complete' ? 'bg-green-500' : 'bg-blue-600'}`}
                            style={{ width: `${uploadProgress}%` }}
                        />
                    </div>
                    <div className="flex gap-4 mt-3 text-xs text-gray-500">
                        <span className={uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'complete' ? 'text-blue-600 font-medium' : ''}>1. Upload</span>
                        <span>→</span>
                        <span className={uploadPhase === 'processing' || uploadPhase === 'complete' ? 'text-blue-600 font-medium' : ''}>2. Extract</span>
                        <span>→</span>
                        <span className={uploadPhase === 'complete' ? 'text-green-600 font-medium' : ''}>3. Assess</span>
                    </div>
                    {uploadPhase === 'complete' && uploadEnrichment && (
                        <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-2">
                            {uploadEnrichment.pii && (
                                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                    uploadEnrichment.pii.has_pii ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-green-50 text-green-700 border border-green-200'
                                }`}>
                                    {uploadEnrichment.pii.has_pii
                                        ? `PII: ${uploadEnrichment.pii.count} found`
                                        : 'PII: clean'}
                                </span>
                            )}
                            {uploadEnrichment.tree && uploadEnrichment.tree.has_tree && (
                                <span className="text-xs px-2 py-1 rounded-full font-medium bg-blue-50 text-blue-700 border border-blue-200">
                                    Structure: {uploadEnrichment.tree.node_count} sections
                                </span>
                            )}
                            {uploadEnrichment.embeddings && uploadEnrichment.embeddings.indexed > 0 && (
                                <span className="text-xs px-2 py-1 rounded-full font-medium bg-purple-50 text-purple-700 border border-purple-200">
                                    Embeddings: {uploadEnrichment.embeddings.indexed} clauses
                                </span>
                            )}
                        </div>
                    )}
                </div>
            )}

            {uploadPhase === 'error' && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
                    <AlertTriangle size={20} className="text-red-600" />
                    <p className="text-sm text-red-700">Upload failed. Please try again.</p>
                    <button onClick={() => setUploadPhase('idle')} className="ml-auto text-sm text-red-700 underline">Dismiss</button>
                </div>
            )}

            {/* Drag Drop Zone */}
            <div className={`mb-6 border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50/30'
                }`}
                onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
            >
                <Upload size={32} className={`mx-auto mb-2 ${dragOver ? 'text-blue-600' : 'text-gray-500'}`} />
                <p className="text-sm font-medium">Drop PDF here or click Upload</p>
                <p className="text-xs text-gray-500 mt-1">Supports multi-page contracts up to 400 pages</p>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-4">
                <div className="relative flex-1 max-w-md">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search contracts..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {search && (
                        <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                            <X size={14} />
                        </button>
                    )}
                </div>
                <select
                    value={typeFilter}
                    onChange={e => setTypeFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {types.map(t => (
                        <option key={t} value={t}>{t === 'all' ? 'All Types' : t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    ))}
                </select>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-border overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-border">
                        <tr>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Title</th>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Counterparty</th>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Type</th>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Status</th>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Enrichment</th>
                            <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {isLoading ? (
                            <><SkeletonRow /><SkeletonRow /><SkeletonRow /></>
                        ) : filtered.length > 0 ? (
                            filtered.map((c: any, i: number) => (
                                <tr
                                    key={c.id}
                                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                                    onClick={() => navigate(`/contracts/${c.id}`)}
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <FileText size={16} className="text-gray-400" />
                                            <span className="font-medium text-sm">{c.title}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{c.counterparty_name || '-'}</td>
                                    <td className="px-6 py-4 text-sm capitalize">{c.contract_type}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${statusColors[c.status] || 'bg-gray-100'}`}>
                                            {c.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            {c.has_parsed_text && (
                                                <span title="Text extracted">
                                                    <FileCheck size={14} className="text-green-500" />
                                                </span>
                                            )}
                                            {c.has_tree && (
                                                <span title="Document structure indexed">
                                                    <TreePine size={14} className="text-blue-500" />
                                                </span>
                                            )}
                                            {c.embedding_count > 0 && (
                                                <span title={`${c.embedding_count} embedding chunks`}>
                                                    <Database size={14} className="text-purple-500" />
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                if (confirm('Delete this contract permanently?')) {
                                                    deleteContract.mutate(c.id)
                                                }
                                            }}
                                            className="p-1.5 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded-lg transition-colors"
                                            title="Delete contract"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={6} className="px-6 py-12 text-center">
                                    <FileText size={40} className="mx-auto mb-3 text-gray-300" />
                                    <p className="text-gray-500 font-medium">No contracts found</p>
                                    <p className="text-sm text-gray-400 mt-1">
                                        {search || typeFilter !== 'all' ? 'Try adjusting filters' : 'Upload your first contract to get started'}
                                    </p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
