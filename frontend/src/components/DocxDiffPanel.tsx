import { useState, useRef } from 'react'
import { Upload, FileText, Scale, Loader2, ArrowRight, X, CheckCircle, AlertTriangle } from 'lucide-react'
import { apiFetch } from '../lib/api'
import { showToast } from '../hooks/useToast'

export default function DocxDiffPanel() {
    const [oldFile, setOldFile] = useState<File | null>(null)
    const [newFile, setNewFile] = useState<File | null>(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const oldRef = useRef<HTMLInputElement>(null)
    const newRef = useRef<HTMLInputElement>(null)

    const handleCompare = async () => {
        if (!oldFile || !newFile) return
        setLoading(true)
        setResult(null)
        try {
            const form = new FormData()
            form.append('old_file', oldFile)
            form.append('new_file', newFile)
            const res = await apiFetch('/docx-diff/compare', { method: 'POST', body: form })
            if (!res.ok) throw new Error('Comparison failed')
            const data = await res.json()
            setResult(data)
            showToast(`Found ${data.summary?.total_changes || 0} changes`, 'success')
        } catch (e: any) {
            showToast(e.message || 'DOCX comparison failed', 'error')
        }
        setLoading(false)
    }

    const diffTypeBadge = (type: string) => {
        if (type === 'replace') return 'bg-yellow-100 text-yellow-700'
        if (type === 'delete') return 'bg-red-100 text-red-700'
        if (type === 'insert_after') return 'bg-green-100 text-green-700'
        return 'bg-gray-100 text-gray-700'
    }

    const diffTypeLabel = (type: string) => {
        if (type === 'replace') return 'Modified'
        if (type === 'delete') return 'Deleted'
        if (type === 'insert_after') return 'Inserted'
        return type
    }

    return (
        <div className="bg-white rounded-xl border border-border p-6 space-y-5">
            <h4 className="font-semibold flex items-center gap-2 text-sm">
                <FileText size={16} /> Upload Two DOCX Files
            </h4>

            <div className="grid grid-cols-3 gap-4">
                {/* Old file */}
                <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
                        oldFile ? 'border-green-300 bg-green-50' : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                    onClick={() => oldRef.current?.click()}
                >
                    <input
                        ref={oldRef}
                        type="file"
                        accept=".docx"
                        className="hidden"
                        onChange={e => setOldFile(e.target.files?.[0] || null)}
                    />
                    {oldFile ? (
                        <>
                            <CheckCircle size={24} className="mx-auto mb-2 text-green-600" />
                            <p className="text-sm font-medium text-green-800">{oldFile.name}</p>
                            <p className="text-xs text-green-600">{(oldFile.size / 1024).toFixed(0)} KB</p>
                            <button
                                onClick={e => { e.stopPropagation(); setOldFile(null) }}
                                className="text-xs text-red-600 mt-2 hover:underline"
                            >
                                Remove
                            </button>
                        </>
                    ) : (
                        <>
                            <Upload size={24} className="mx-auto mb-2 text-gray-400" />
                            <p className="text-sm font-medium text-gray-700">Original (Old) DOCX</p>
                            <p className="text-xs text-gray-400 mt-1">Click to upload</p>
                        </>
                    )}
                </div>

                {/* Arrow */}
                <div className="flex items-center justify-center">
                    <ArrowRight size={20} className="text-gray-300" />
                </div>

                {/* New file */}
                <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
                        newFile ? 'border-green-300 bg-green-50' : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                    onClick={() => newRef.current?.click()}
                >
                    <input
                        ref={newRef}
                        type="file"
                        accept=".docx"
                        className="hidden"
                        onChange={e => setNewFile(e.target.files?.[0] || null)}
                    />
                    {newFile ? (
                        <>
                            <CheckCircle size={24} className="mx-auto mb-2 text-green-600" />
                            <p className="text-sm font-medium text-green-800">{newFile.name}</p>
                            <p className="text-xs text-green-600">{(newFile.size / 1024).toFixed(0)} KB</p>
                            <button
                                onClick={e => { e.stopPropagation(); setNewFile(null) }}
                                className="text-xs text-red-600 mt-2 hover:underline"
                            >
                                Remove
                            </button>
                        </>
                    ) : (
                        <>
                            <Upload size={24} className="mx-auto mb-2 text-gray-400" />
                            <p className="text-sm font-medium text-gray-700">Proposed (New) DOCX</p>
                            <p className="text-xs text-gray-400 mt-1">Click to upload</p>
                        </>
                    )}
                </div>
            </div>

            <button
                onClick={handleCompare}
                disabled={loading || !oldFile || !newFile}
                className="w-full px-4 py-2.5 bg-primary text-white rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-primary-light disabled:opacity-50"
            >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Scale size={14} />}
                Compare DOCX Files
            </button>

            {/* Results */}
            {result && (
                <div className="space-y-4 pt-2">
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                        <Scale size={16} className="text-blue-600" />
                        <div>
                            <p className="text-sm font-medium text-blue-800">
                                {result.old_filename} → {result.new_filename}
                            </p>
                            <p className="text-xs text-blue-600">
                                {result.summary?.total_changes || 0} changes: {result.summary?.replacements || 0} modified, {result.summary?.deletions || 0} deleted, {result.summary?.insertions || 0} inserted
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {(result.changes || []).map((change: any, i: number) => (
                            <div key={i} className="border border-gray-100 rounded-lg overflow-hidden">
                                <div className={`px-3 py-2 text-xs font-medium flex items-center gap-2 ${diffTypeBadge(change.type)}`}>
                                    <span>{diffTypeLabel(change.type)}</span>
                                    <span className="text-gray-500">Context: "{change.context}"</span>
                                </div>
                                <div className="p-3 text-sm space-y-2">
                                    {change.old_text && (
                                        <div className="bg-red-50 rounded p-2">
                                            <p className="text-xs text-red-600 font-medium mb-1">Original</p>
                                            <p className="text-red-800">{change.old_text}</p>
                                        </div>
                                    )}
                                    {change.new_text && (
                                        <div className="bg-green-50 rounded p-2">
                                            <p className="text-xs text-green-600 font-medium mb-1">Proposed</p>
                                            <p className="text-green-800">{change.new_text}</p>
                                        </div>
                                    )}
                                    {change.diff && (
                                        <div className="bg-gray-50 rounded p-2">
                                            <p className="text-xs text-gray-600 font-medium mb-1">Diff</p>
                                            <p className="text-gray-800 font-mono text-xs whitespace-pre-wrap">{change.diff}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
