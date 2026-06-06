import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
    ArrowLeft, AlertTriangle, Shield, BookOpen, FileText, CheckCircle, Clock,
    Eye, Send, Download, MessageSquare, ThumbsUp, ThumbsDown, User, Loader2,
    Zap, Layers, Gavel, Bell, Sparkles, Scale, ChevronRight, Highlighter,
    TreePine, Lock, ShieldAlert, Edit3, X, Save
} from 'lucide-react'
import {
    useContract, useContractStages, useContractComments,
    usePlainEnglish, useGeneratePlainEnglish, useAskContract,
    useContractVersions, useHighlights, useGenerateHighlights,
    useContractTree, useContractPII, useAnonymizeText,
    useApproveStage, useRejectStage, useSubmitForApproval,
    useTransitionContract, usePostComment, useRedlineCompare,
    useUpdateContract, useExplainRisk, useRiskReport,
} from '../hooks/useQueries'
import {
    PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar,
    XAxis, YAxis, CartesianGrid
} from 'recharts'
import { apiFetch } from '../lib/api'
import { showToast } from '../hooks/useToast'
import PDFViewer from '../components/PDFViewer'
import ContractStructure from '../components/ContractStructure'
import ContractPII from '../components/ContractPII'
import DocxDiffPanel from '../components/DocxDiffPanel'

const SEVERITY_COLORS: Record<string, string> = {
    critical: '#EF4444', high: '#F59E0B', medium: '#3B82F6', low: '#22C55E'
}

function SkeletonBlock({ className = '' }: { className?: string }) {
    return <div className={`bg-gray-200 rounded animate-pulse ${className}`} />
}

function SkeletonDetail() {
    return (
        <div className="p-8 space-y-6">
            <SkeletonBlock className="h-8 w-64" />
            <SkeletonBlock className="h-4 w-48" />
            <div className="grid grid-cols-3 gap-4">
                <SkeletonBlock className="h-24" />
                <SkeletonBlock className="h-24" />
                <SkeletonBlock className="h-24" />
            </div>
            <SkeletonBlock className="h-64" />
        </div>
    )
}

export default function ContractDetailPage() {
    const { id } = useParams()
    const navigate = useNavigate()

    // ── React Query data hooks ──
    const { data, isLoading: loading, error: contractError } = useContract(id)
    const { data: stagesData } = useContractStages(id)
    const { data: commentsData } = useContractComments(id)
    const stages = stagesData || []
    const comments = commentsData || []

    const [newComment, setNewComment] = useState('')
    const [searchParams, setSearchParams] = useSearchParams()
    const urlTab = searchParams.get('tab') || 'overview'
    const [tab, setTab] = useState(urlTab)

    // Sync tab with URL
    useEffect(() => {
        if (tab !== urlTab) {
            setSearchParams({ tab })
        }
    }, [tab])

    useEffect(() => {
        if (urlTab && urlTab !== tab) {
            setTab(urlTab)
        }
    }, [urlTab])
    const [reportLoading, setReportLoading] = useState(false)
    const [actionLoading, setActionLoading] = useState<string | null>(null)

    // Mutation hooks
    const submitApproval = useSubmitForApproval()
    const approveStageMut = useApproveStage()
    const rejectStageMut = useRejectStage()
    const transitionMut = useTransitionContract()
    const postCommentMut = usePostComment()
    const redlineMut = useRedlineCompare()

    // Phase 3 state
    const [chatQuestion, setChatQuestion] = useState('')
    const [chatAnswer, setChatAnswer] = useState('')
    const [chatLoading, setChatLoading] = useState(false)
    const [chatStreaming, setChatStreaming] = useState(false)
    const [chatSources, setChatSources] = useState<{title?: string, line_num?: number, score?: number, text?: string}[]>([])
    const [chatRetrievalMethod, setChatRetrievalMethod] = useState<string>('')
    const [showEditModal, setShowEditModal] = useState(false)
    const [editForm, setEditForm] = useState<any>({})
    const [savingEdit, setSavingEdit] = useState(false)
    const [redlineOtherId, setRedlineOtherId] = useState('')
    const [redlineResult, setRedlineResult] = useState<any>(null)
    const [redlineLoading, setRedlineLoading] = useState(false)
    const [redlineMode, setRedlineMode] = useState<'version' | 'contract' | 'docx'>('version')
    const [selectedVersionId, setSelectedVersionId] = useState('')
    const { data: versionsData } = useContractVersions(id)
    const [explainClauseId, setExplainClauseId] = useState<string | null>(null)
    const [explainResult, setExplainResult] = useState<any>(null)
    const [explainLoading, setExplainLoading] = useState(false)
    const { data: highlightsData } = useHighlights(id)
    const generateHighlights = useGenerateHighlights()

    // Enrichment layer hooks
    const { data: treeData, isLoading: treeLoading, error: treeError } = useContractTree(id)
    const { data: piiData, isLoading: piiLoading, error: piiError } = useContractPII(id)
    const anonymizeMutation = useAnonymizeText()
    const [anonymizeResult, setAnonymizeResult] = useState<any>(null)
    const [chatMethod, setChatMethod] = useState<string>('')

    const tabs = [
        { key: 'overview', label: 'Overview', icon: FileText },
        { key: 'clauses', label: 'Clauses', icon: BookOpen },
        { key: 'structure', label: 'Structure', icon: TreePine },
        { key: 'pii', label: 'PII', icon: Lock },
        { key: 'plain-english', label: 'Plain English', icon: Eye },
        { key: 'explain', label: 'Explain AI', icon: Zap },
        { key: 'redline', label: 'Redline', icon: Gavel },
        { key: 'chat', label: 'Chat', icon: MessageSquare },
        { key: 'highlights', label: 'Highlights', icon: Highlighter },
        { key: 'processing', label: 'Processing', icon: Layers },
        { key: 'risk', label: 'Risk', icon: Shield },
        { key: 'obligations', label: 'Obligations', icon: CheckCircle },
        { key: 'approvals', label: 'Approvals', icon: ThumbsUp },
        { key: 'comments', label: 'Comments', icon: Bell },
        { key: 'pdf', label: 'PDF', icon: Download },
    ]

    // --- Actions (using mutations) ---
    const handleSubmitForApproval = async () => {
        if (!id) return
        setActionLoading('submit')
        try {
            await submitApproval.mutateAsync(id)
        } catch {}
        setActionLoading(null)
    }

    const handleApproveStage = async (stageId: string) => {
        setActionLoading(stageId)
        try {
            await approveStageMut.mutateAsync({ stageId, comment: 'Approved' })
            showToast('Stage approved', 'success')
        } catch {}
        setActionLoading(null)
    }

    const handleRejectStage = async (stageId: string) => {
        setActionLoading(stageId)
        try {
            await rejectStageMut.mutateAsync({ stageId, comment: 'Rejected' })
            showToast('Stage rejected', 'warning')
        } catch {}
        setActionLoading(null)
    }

    const handleTransition = async (newStatus: string) => {
        if (!id) return
        setActionLoading(`transition-${newStatus}`)
        try {
            await transitionMut.mutateAsync({ contractId: id, newStatus })
            showToast(`Status changed to ${newStatus}`, 'success')
        } catch {}
        setActionLoading(null)
    }

    const handlePostComment = async () => {
        if (!newComment.trim() || !id) return
        setActionLoading('comment')
        try {
            await postCommentMut.mutateAsync({ contractId: id, content: newComment })
            setNewComment('')
        } catch {}
        setActionLoading(null)
    }

    const riskReportMut = useRiskReport()
    const exportReport = async () => {
        if (!id) return
        setReportLoading(true)
        try {
            const d = await riskReportMut.mutateAsync(id)
            const blob = new Blob([d.report_html], { type: 'text/html' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `risk-report-${d.contract_title || id}.html`
            a.click()
            URL.revokeObjectURL(url)
            showToast('Report downloaded', 'success')
        } catch {
            showToast('Failed to download report', 'error')
        }
        setReportLoading(false)
    }

    // Phase 3 hooks
    const { data: plainEnglishData, isLoading: peLoading } = usePlainEnglish(id)
    const generatePe = useGeneratePlainEnglish()
    const askContract = useAskContract()

    const handleChat = async () => {
        if (!chatQuestion.trim() || !id) return
        setChatLoading(true)
        setChatStreaming(true)
        setChatAnswer('')
        setChatSources([])
        setChatRetrievalMethod('')

        try {
            const response = await fetch(`/api/v1/chat/contracts/${id}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: chatQuestion }),
            })

            if (!response.ok) {
                const err = await response.json()
                setChatAnswer('Error: ' + (err.detail || 'Failed to get answer'))
                setChatLoading(false)
                setChatStreaming(false)
                return
            }

            const data = await response.json()
            setChatAnswer(data.answer || '')
            setChatRetrievalMethod(data.retrieval_method || '')
            setChatSources(data.sources || [])
        } catch (e: any) {
            setChatAnswer('Error: ' + (e.message || 'Failed to get answer'))
        }

        setChatLoading(false)
        setChatStreaming(false)
    }

    const handleRedline = async () => {
        if (!redlineOtherId || !id) return
        setRedlineLoading(true)
        try {
            const data = await redlineMut.mutateAsync({ contractId: id, otherId: redlineOtherId })
            setRedlineResult(data)
        } catch (e: any) {
            showToast(e.message || 'Comparison failed', 'error')
        }
        setRedlineLoading(false)
    }

    const explainRiskMut = useExplainRisk()
    const updateContractMut = useUpdateContract()
    const handleExplain = async (clauseId: string) => {
        setExplainClauseId(clauseId)
        setExplainLoading(true)
        try {
            const data = await explainRiskMut.mutateAsync(clauseId)
            setExplainResult(data)
        } catch (e: any) {
            showToast(e.message || 'Failed to explain risk', 'error')
        }
        setExplainLoading(false)
    }

    // --- Helpers ---
    const scoreColor = (s: number) => {
        if (s < 0.3) return 'text-green-600'
        if (s < 0.6) return 'text-yellow-600'
        if (s < 0.8) return 'text-orange-600'
        return 'text-red-600'
    }
    const sevBadge = (s: string) => {
        if (s === 'critical') return 'bg-red-100 text-red-700'
        if (s === 'high') return 'bg-orange-100 text-orange-700'
        if (s === 'medium') return 'bg-yellow-100 text-yellow-700'
        return 'bg-blue-100 text-blue-700'
    }
    const statusBadge = (s: string) => {
        const map: Record<string, string> = {
            draft: 'bg-gray-100 text-gray-700', in_review: 'bg-yellow-100 text-yellow-700',
            approved: 'bg-blue-100 text-blue-700', signed: 'bg-green-100 text-green-700',
            active: 'bg-green-100 text-green-700', expired: 'bg-orange-100 text-orange-700',
            terminated: 'bg-red-100 text-red-700', analyzed: 'bg-purple-100 text-purple-700',
        }
        return map[s] || 'bg-gray-100 text-gray-700'
    }

    // --- Renders ---
    if (loading) return <SkeletonDetail />
    if (contractError) {
        const msg = (contractError as any)?.message || 'Failed to load contract'
        return (
            <div className="p-8">
                <button onClick={() => navigate('/contracts')} className="flex items-center gap-2 text-sm text-primary-lighter hover:text-primary mb-4">
                    <ArrowLeft size={16} /> Back to Contracts
                </button>
                <div className="bg-white rounded-xl border border-border p-12 text-center">
                    <AlertTriangle size={48} className="mx-auto mb-4 text-red-500" />
                    <h2 className="text-xl font-bold mb-2">{msg.includes('not found') ? 'Contract Not Found' : 'Error'}</h2>
                    <p className="text-primary-lighter mb-4">{msg}</p>
                    <button onClick={() => navigate('/contracts')} className="bg-primary text-white px-4 py-2 rounded-lg">
                        Back to Contracts
                    </button>
                </div>
            </div>
        )
    }
    if (!data) return <SkeletonDetail />

    const { contract, clauses, assessment, findings, obligations } = data

    // Risk chart data
    const severityChart = [
        { name: 'Critical', value: findings?.filter((f: any) => f.severity === 'critical' && !f.is_resolved).length || 0, color: SEVERITY_COLORS.critical },
        { name: 'High', value: findings?.filter((f: any) => f.severity === 'high' && !f.is_resolved).length || 0, color: SEVERITY_COLORS.high },
        { name: 'Medium', value: findings?.filter((f: any) => f.severity === 'medium' && !f.is_resolved).length || 0, color: SEVERITY_COLORS.medium },
        { name: 'Low', value: findings?.filter((f: any) => f.severity === 'low' && !f.is_resolved).length || 0, color: SEVERITY_COLORS.low },
    ].filter(d => d.value > 0)

    const typeCounts: Record<string, number> = {}
    findings?.forEach((f: any) => {
        if (!f.is_resolved) typeCounts[f.finding_type] = (typeCounts[f.finding_type] || 0) + 1
    })
    const typeChart = Object.entries(typeCounts).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), value
    }))

    const scoreLayers = assessment ? [
        { label: 'Playbook', score: assessment.playbook_score, weight: '35%', color: '#3B82F6' },
        { label: 'Law', score: assessment.law_score, weight: '40%', color: '#8B5CF6' },
        { label: 'Regulatory', score: assessment.regulatory_score, weight: '25%', color: '#F59E0B' },
    ] : []

    // Approval stepper
    const stageNames = ['legal_review', 'finance_review', 'ceo_review']
    const stageMap: Record<string, any> = {}
    stages.forEach((s: any) => { stageMap[s.stage_name] = s })
    const currentStageIdx = stageNames.findIndex(n => stageMap[n]?.status === 'pending')
    const allApproved = stages.length > 0 && stages.every((s: any) => s.status === 'approved')

    return (
        <div className="p-8">
            {/* Header */}
            <button onClick={() => navigate('/contracts')} className="flex items-center gap-2 text-sm text-primary-lighter hover:text-primary mb-4 transition-colors">
                <ArrowLeft size={16} /> Back to Contracts
            </button>

            <div className="flex items-start justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold">{contract.title}</h1>
                    <div className="flex items-center gap-3 mt-1 text-sm text-primary-lighter">
                        <span>{contract.counterparty_name || 'No counterparty'}</span>
                        <span>·</span>
                        <span className="capitalize">{contract.contract_type}</span>
                        <span>·</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${statusBadge(contract.status)}`}>
                            {contract.status.replace('_', ' ')}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {assessment && (
                        <div className="text-center mr-4">
                            <div className={`text-4xl font-bold ${scoreColor(assessment.overall_score)}`}>
                                {(assessment.overall_score * 100).toFixed(0)}
                            </div>
                            <p className="text-xs text-primary-lighter mt-1">Risk Score</p>
                        </div>
                    )}
                    <button
                        onClick={() => { setEditForm({ ...contract }); setShowEditModal(true) }}
                        className="border border-border px-3 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors"
                    >
                        <Edit3 size={14} /> Edit
                    </button>
                    <button
                        onClick={exportReport}
                        disabled={reportLoading}
                        className="border border-border px-3 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        {reportLoading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                        Export Report
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 overflow-x-auto">
                {tabs.map(t => (
                    <button key={t.key} onClick={() => setTab(t.key)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                            tab === t.key ? 'bg-white text-primary shadow-sm' : 'text-primary-lighter hover:text-primary'
                        }`}>
                        <t.icon size={15} /> {t.label}
                    </button>
                ))}
            </div>

            {/* Overview */}
            {tab === 'overview' && (
                <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                        <div className="bg-white rounded-xl border border-border p-6">
                            <h3 className="font-semibold mb-4">Contract Details</h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between"><span className="text-primary-lighter">Status</span><span className="capitalize">{contract.status.replace('_', ' ')}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Governing Law</span><span>{contract.governing_law || '-'}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Auto Renewal</span><span>{contract.auto_renewal ? 'Yes' : 'No'}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Value</span><span>{contract.value_inr ? `₹${contract.value_inr.toLocaleString()}` : '-'}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Start Date</span><span>{contract.start_date || '-'}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">End Date</span><span>{contract.end_date || '-'}</span></div>
                            </div>
                        </div>
                        <div className="bg-white rounded-xl border border-border p-6">
                            <h3 className="font-semibold mb-4">Clauses Extracted</h3>
                            <div className="flex flex-wrap gap-2">
                                {clauses?.length > 0 ? clauses.map((cl: any) => (
                                    <span key={cl.id} className="px-3 py-1 bg-primary/5 rounded-full text-xs font-medium capitalize">{cl.clause_type.replace('_', ' ')}</span>
                                )) : <span className="text-sm text-primary-lighter">No clauses extracted</span>}
                            </div>
                        </div>
                        <div className="bg-white rounded-xl border border-border p-6">
                            <h3 className="font-semibold mb-4">Quick Stats</h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between"><span className="text-primary-lighter">Clauses</span><span className="font-medium">{clauses?.length || 0}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Findings</span><span className="font-medium">{findings?.filter((f: any) => !f.is_resolved).length || 0}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Obligations</span><span className="font-medium">{obligations?.length || 0}</span></div>
                                <div className="flex justify-between"><span className="text-primary-lighter">Approval Stage</span><span className="font-medium capitalize">{contract.status.replace('_', ' ')}</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Clauses */}
            {tab === 'clauses' && (
                <div className="space-y-3">
                    {clauses?.length > 0 ? clauses.map((cl: any) => (
                        <div key={cl.id} className="bg-white rounded-xl border border-border p-5 hover:shadow-sm transition-shadow">
                            <div className="flex items-center gap-3 mb-2">
                                <span className="px-2 py-0.5 bg-primary/10 rounded text-xs font-medium capitalize">{cl.clause_type.replace('_', ' ')}</span>
                                <span className="text-xs text-primary-lighter">Confidence: {(cl.confidence_score * 100).toFixed(0)}%</span>
                                {cl.page_number > 1 && <span className="text-xs text-primary-lighter">Page {cl.page_number}</span>}
                            </div>
                            <p className="text-sm text-primary-lighter leading-relaxed">{cl.clause_text}</p>
                        </div>
                    )) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <BookOpen size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-primary-lighter">No clauses extracted from this contract</p>
                        </div>
                    )}
                </div>
            )}

            {/* Structure */}
            {tab === 'structure' && (
                <ContractStructure
                    structure={treeData?.structure || []}
                    doc_name={treeData?.doc_name || data?.contract?.title || 'Contract'}
                    node_count={treeData?.node_count || 0}
                    loading={treeLoading}
                    error={treeError ? String(treeError) : null}
                    contractId={id}
                />
            )}

            {/* PII */}
            {tab === 'pii' && (
                <ContractPII
                    findings={piiData?.findings || []}
                    has_pii={piiData?.has_pii || false}
                    entity_types={piiData?.entity_types || []}
                    anonymized_preview={piiData?.anonymized_preview || ''}
                    loading={piiLoading}
                    error={piiError ? String(piiError) : null}
                    onAnonymize={async () => {
                        if (!data?.contract?.parsed_text) return
                        const result = await anonymizeMutation.mutateAsync(data.contract.parsed_text)
                        setAnonymizeResult(result)
                    }}
                    anonymizeResult={anonymizeResult}
                    anonymizeLoading={anonymizeMutation.isPending}
                />
            )}

            {/* Plain English */}
            {tab === 'plain-english' && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold flex items-center gap-2"><Sparkles size={18} /> Plain English Summary</h3>
                        <button
                            onClick={() => id && generatePe.mutate(id)}
                            disabled={generatePe.isPending}
                            className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                        >
                            {generatePe.isPending ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                            Generate / Refresh
                        </button>
                    </div>
                    {peLoading ? (
                        <div className="space-y-3">
                            {[1,2,3].map(i => <SkeletonBlock key={i} className="h-24" />)}
                        </div>
                    ) : plainEnglishData?.summaries?.length > 0 ? (
                        <div className="space-y-3">
                            {plainEnglishData.summaries.map((s: any) => (
                                <div key={s.id} className="bg-white rounded-xl border border-border p-5">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="px-2 py-0.5 bg-primary/10 rounded text-xs font-medium capitalize">{s.clause_type.replace('_', ' ')}</span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                            s.risk_level === 'high' ? 'bg-red-100 text-red-700' :
                                            s.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-green-100 text-green-700'
                                        }`}>{s.risk_level}</span>
                                    </div>
                                    <p className="text-sm text-primary-lighter mb-2 leading-relaxed">{s.plain_english}</p>
                                    {s.suggestions && <p className="text-xs text-blue-600">💡 {s.suggestions}</p>}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <Sparkles size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-primary-lighter">No plain English summaries yet</p>
                            <p className="text-sm text-primary-lighter mt-1">Click Generate to analyze clauses</p>
                        </div>
                    )}
                </div>
            )}

            {/* Explainable AI */}
            {tab === 'explain' && (
                <div className="space-y-4">
                    <h3 className="font-semibold flex items-center gap-2"><Zap size={18} /> Explainable Risk Analysis</h3>
                    <p className="text-sm text-primary-lighter">Click a clause to see why it was flagged as risky.</p>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            {clauses?.map((cl: any) => (
                                <button
                                    key={cl.id}
                                    onClick={() => handleExplain(cl.id)}
                                    className={`w-full text-left bg-white rounded-xl border p-3 hover:shadow-sm transition-shadow ${
                                        explainClauseId === cl.id ? 'border-primary ring-1 ring-primary' : 'border-border'
                                    }`}
                                >
                                    <span className="text-xs font-medium capitalize">{cl.clause_type.replace('_', ' ')}</span>
                                    <p className="text-xs text-primary-lighter mt-1 truncate">{cl.clause_text}</p>
                                </button>
                            ))}
                        </div>
                        <div className="bg-white rounded-xl border border-border p-5">
                            {explainLoading ? (
                                <div className="flex items-center justify-center h-40">
                                    <Loader2 size={24} className="animate-spin text-primary" />
                                </div>
                            ) : explainResult ? (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl font-bold">{explainResult.fairness_grade}</span>
                                        <span className="text-sm text-primary-lighter">Score: {explainResult.fairness_score}/100</span>
                                    </div>
                                    {explainResult.red_flags?.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-medium text-red-600 mb-2">Red Flags</h4>
                                            {explainResult.red_flags.map((rf: any, i: number) => (
                                                <div key={i} className="bg-red-50 rounded-lg p-3 mb-2">
                                                    <p className="text-sm font-medium">{rf.title}</p>
                                                    <p className="text-xs text-primary-lighter mt-1">{rf.explanation}</p>
                                                    {rf.suggestion && <p className="text-xs text-blue-600 mt-1">→ {rf.suggestion}</p>}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {explainResult.warnings?.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-medium text-yellow-600 mb-2">Warnings</h4>
                                            {explainResult.warnings.map((w: any, i: number) => (
                                                <div key={i} className="bg-yellow-50 rounded-lg p-3 mb-2">
                                                    <p className="text-sm font-medium">{w.title}</p>
                                                    <p className="text-xs text-primary-lighter">{w.explanation}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center text-primary-lighter py-12">
                                    <Zap size={32} className="mx-auto mb-2 text-gray-300" />
                                    <p className="text-sm">Select a clause to see AI explanation</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Redline Diff */}
            {tab === 'redline' && (
                <div className="space-y-4">
                    <h3 className="font-semibold flex items-center gap-2"><Scale size={18} /> Redline Comparison</h3>

                    {/* Mode toggle */}
                    <div className="flex gap-2">
                        <button
                            onClick={() => setRedlineMode('version')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${redlineMode === 'version' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                        >
                            Compare with Version
                        </button>
                        <button
                            onClick={() => setRedlineMode('contract')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${redlineMode === 'contract' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                        >
                            Compare with Contract
                        </button>
                        <button
                            onClick={() => setRedlineMode('docx')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${redlineMode === 'docx' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                        >
                            Compare DOCX Files
                        </button>
                    </div>

                    {redlineMode !== 'docx' && (
                        <div className="flex gap-3 items-end">
                            <div className="flex-1">
                                <label className="text-xs text-primary-lighter block mb-1">This contract</label>
                                <div className="px-3 py-2 border border-border rounded-lg text-sm bg-gray-50">{contract.title}</div>
                            </div>

                            {redlineMode === 'version' ? (
                                <div className="flex-1">
                                    <label className="text-xs text-primary-lighter block mb-1">Select Version</label>
                                    <select
                                        value={selectedVersionId}
                                        onChange={e => {
                                            setSelectedVersionId(e.target.value)
                                            setRedlineOtherId(e.target.value)
                                        }}
                                        className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                                    >
                                        <option value="">Choose a version...</option>
                                        {(versionsData?.versions || []).map((v: any) => (
                                            <option key={v.id} value={v.id}>
                                                v{v.version_number} — {v.title || 'Untitled'} ({new Date(v.created_at).toLocaleDateString()})
                                            </option>
                                        ))}
                                    </select>
                                    {(versionsData?.versions || []).length === 0 && (
                                        <p className="text-xs text-gray-400 mt-1">No versions stored yet.</p>
                                    )}
                                </div>
                            ) : (
                                <div className="flex-1">
                                    <label className="text-xs text-primary-lighter block mb-1">Compare with (Contract ID)</label>
                                    <input
                                        type="text"
                                        value={redlineOtherId}
                                        onChange={e => setRedlineOtherId(e.target.value)}
                                        placeholder="Enter contract ID..."
                                        className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            )}
                            <button
                                onClick={handleRedline}
                                disabled={redlineLoading || !redlineOtherId}
                                className="px-4 py-2 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                            >
                                {redlineLoading ? <Loader2 size={14} className="animate-spin" /> : <Scale size={14} />}
                                Compare
                            </button>
                        </div>
                    )}

                    {redlineMode === 'docx' && (
                        <DocxDiffPanel />
                    )}
                    {redlineResult?.comparison?.length > 0 && (
                        <div className="space-y-3">
                            {redlineResult.comparison.map((item: any, i: number) => (
                                <div key={i} className="bg-white rounded-xl border border-border p-5">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                            item.label === 'unchanged' ? 'bg-green-100 text-green-700' :
                                            item.label === 'material_change' ? 'bg-red-100 text-red-700' :
                                            item.label === 'added' ? 'bg-blue-100 text-blue-700' :
                                            item.label === 'removed' ? 'bg-gray-100 text-gray-700' :
                                            'bg-yellow-100 text-yellow-700'
                                        }`}>{item.label.replace('_', ' ')}</span>
                                        <span className="text-xs text-primary-lighter">Similarity: {(item.similarity_score * 100).toFixed(0)}%</span>
                                        <span className="text-xs text-primary-lighter">Risk: {item.risk_delta}</span>
                                    </div>
                                    <p className="text-sm font-medium mb-2">{item.change_summary}</p>
                                    {item.key_differences?.length > 0 && (
                                        <ul className="space-y-1 mb-3">
                                            {item.key_differences.map((diff: string, j: number) => (
                                                <li key={j} className="text-xs text-primary-lighter flex items-start gap-1">
                                                    <ChevronRight size={12} className="mt-0.5 shrink-0" /> {diff}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                    <div className="grid grid-cols-2 gap-3 text-xs">
                                        {item.old_text && (
                                            <div className="bg-red-50 rounded p-2">
                                                <p className="text-red-600 font-medium mb-1">Original</p>
                                                <p className="text-primary-lighter">{item.old_text}</p>
                                            </div>
                                        )}
                                        {item.new_text && (
                                            <div className="bg-green-50 rounded p-2">
                                                <p className="text-green-600 font-medium mb-1">New</p>
                                                <p className="text-primary-lighter">{item.new_text}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Edit Modal */}
            {showEditModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                    <div className="bg-white rounded-xl w-full max-w-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold">Edit Contract</h2>
                            <button onClick={() => setShowEditModal(false)} className="p-1 hover:bg-gray-100 rounded">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <label className="text-xs font-medium uppercase text-gray-500">Title</label>
                                <input value={editForm.title || ''} onChange={e => setEditForm({...editForm, title: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-medium uppercase text-gray-500">Type</label>
                                    <select value={editForm.contract_type || 'vendor'} onChange={e => setEditForm({...editForm, contract_type: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm">
                                        {['vendor', 'nda', 'employment', 'lease', 'service', 'partnership', 'license'].map(c => (
                                            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-medium uppercase text-gray-500">Status</label>
                                    <select value={editForm.status || 'draft'} onChange={e => setEditForm({...editForm, status: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm">
                                        {['draft', 'in_review', 'approved', 'signed', 'active', 'expired', 'terminated'].map(s => (
                                            <option key={s} value={s}>{s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="text-xs font-medium uppercase text-gray-500">Counterparty</label>
                                <input value={editForm.counterparty_name || ''} onChange={e => setEditForm({...editForm, counterparty_name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-medium uppercase text-gray-500">Start Date</label>
                                    <input type="date" value={editForm.start_date || ''} onChange={e => setEditForm({...editForm, start_date: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                                </div>
                                <div>
                                    <label className="text-xs font-medium uppercase text-gray-500">End Date</label>
                                    <input type="date" value={editForm.end_date || ''} onChange={e => setEditForm({...editForm, end_date: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-medium uppercase text-gray-500">Value (INR)</label>
                                    <input type="number" value={editForm.value_inr || 0} onChange={e => setEditForm({...editForm, value_inr: parseFloat(e.target.value)})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                                </div>
                                <div className="flex items-center gap-2 pt-5">
                                    <input type="checkbox" id="auto_renewal" checked={editForm.auto_renewal || false} onChange={e => setEditForm({...editForm, auto_renewal: e.target.checked})} className="rounded" />
                                    <label htmlFor="auto_renewal" className="text-sm">Auto-renewal</label>
                                </div>
                            </div>
                            <div>
                                <label className="text-xs font-medium uppercase text-gray-500">Governing Law</label>
                                <input value={editForm.governing_law || ''} onChange={e => setEditForm({...editForm, governing_law: e.target.value})} className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-4">
                            <button onClick={() => setShowEditModal(false)} className="px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
                            <button
                                onClick={async () => {
                                    setSavingEdit(true)
                                    try {
                                        await updateContractMut.mutateAsync({ id: id!, data: editForm })
                                        showToast('Contract updated', 'success')
                                        setShowEditModal(false)
                                    } catch {
                                        showToast('Failed to update', 'error')
                                    }
                                    setSavingEdit(false)
                                }}
                                disabled={savingEdit}
                                className="px-4 py-2 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                            >
                                {savingEdit ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                                Save
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Chat with Contract */}
            {tab === 'chat' && (
                <div className="space-y-4">
                    <h3 className="font-semibold flex items-center gap-2"><MessageSquare size={18} /> Chat with Contract</h3>
                    <div className="bg-white rounded-xl border border-border p-4">
                        {chatAnswer && (
                            <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
                                <p className="text-sm whitespace-pre-wrap">{chatAnswer}</p>
                                {chatRetrievalMethod && (
                                    <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
                                        <span className="text-xs text-gray-500">Retrieval:</span>
                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                            chatRetrievalMethod === 'tree' ? 'bg-green-100 text-green-700' :
                                            chatRetrievalMethod === 'embeddings' ? 'bg-blue-100 text-blue-700' :
                                            'bg-gray-100 text-gray-600'
                                        }`}>
                                            {chatRetrievalMethod === 'tree' ? 'PageIndex Tree' :
                                             chatRetrievalMethod === 'embeddings' ? 'Embeddings' :
                                             chatRetrievalMethod === 'clauses' ? 'Clause Fallback' : chatRetrievalMethod}
                                        </span>
                                    </div>
                                )}
                                {chatSources.length > 0 && (
                                    <div className="pt-2 border-t border-gray-200">
                                        <p className="text-xs text-gray-500 mb-1.5">Sources:</p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {chatSources.map((src, i) => (
                                                <span key={i} className="text-xs px-2 py-1 bg-white border border-gray-200 rounded-md text-gray-700">
                                                    {src.title || src.text?.slice(0, 40) || 'Section'}
                                                    {src.line_num ? ` (L${src.line_num})` : ''}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={chatQuestion}
                                onChange={e => setChatQuestion(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleChat()}
                                placeholder="Ask anything about this contract..."
                                className="flex-1 px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                onClick={handleChat}
                                disabled={chatLoading || !chatQuestion.trim()}
                                className="px-4 py-2 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                            >
                                {chatLoading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                Ask
                            </button>
                        </div>
                        <div className="flex gap-2 mt-3 flex-wrap">
                            {['What is the termination clause?', 'Explain liability cap', 'Any auto-renewal terms?', 'What are my obligations?'].map(q => (
                                <button
                                    key={q}
                                    onClick={() => { setChatQuestion(q); handleChat() }}
                                    className="px-2 py-1 bg-gray-100 rounded text-xs text-primary-lighter hover:bg-gray-200"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Highlights */}
            {tab === 'highlights' && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold flex items-center gap-2"><Highlighter size={18} /> Clause Highlights</h3>
                        <button
                            onClick={() => id && generateHighlights.mutate(id)}
                            disabled={generateHighlights.isPending}
                            className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light disabled:opacity-50"
                        >
                            {generateHighlights.isPending ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                            Generate Highlights
                        </button>
                    </div>
                    {(highlightsData?.highlights || []).length === 0 && (
                        <div className="bg-white rounded-xl border border-border p-8 text-center text-sm text-primary-lighter">
                            No highlights generated yet. Click "Generate Highlights" to extract clause bounding boxes from the PDF.
                        </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        {(highlightsData?.highlights || []).map((h: any, i: number) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="bg-white rounded-xl border border-border p-4"
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">{h.clause_type}</span>
                                    <span className="text-xs text-primary-lighter">Page {h.page_number}</span>
                                </div>
                                <p className="text-sm text-gray-700 line-clamp-3">{h.clause_text}</p>
                                {h.bounding_box && (
                                    <div className="mt-2 text-xs text-primary-lighter">
                                        Bbox: x={h.bounding_box.x?.toFixed(2)}, y={h.bounding_box.y?.toFixed(2)}
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
            )}

            {/* Processing Pipeline */}
            {tab === 'processing' && (
                <div className="space-y-6">
                    <div className="bg-white rounded-xl border border-border p-6">
                        <h3 className="font-semibold mb-4">AI Processing Pipeline</h3>
                        <div className="relative">
                            {/* Pipeline steps */}
                            {[
                                { step: 1, label: 'Document Ingestion', desc: 'PDF parsed with Docling', icon: FileText, done: true },
                                { step: 2, label: 'Chunking', desc: '400-page document split into semantic chunks', icon: Layers, done: true },
                                { step: 3, label: 'Clause Extraction', desc: `${clauses?.length || 0} clauses identified via GPT-4o-mini`, icon: BookOpen, done: clauses?.length > 0 },
                                { step: 4, label: 'Entity Recognition', desc: 'Parties, dates, values, governing law extracted', icon: Zap, done: !!contract.counterparty_name },
                                { step: 5, label: 'Risk Assessment', desc: assessment ? `Score: ${(assessment.overall_score * 100).toFixed(0)}/100` : 'Pending', icon: Shield, done: !!assessment },
                                { step: 6, label: 'Knowledge Graph', desc: 'Nodes linked in Neo4j', icon: Layers, done: true },
                            ].map((s, i, arr) => (
                                <div key={s.step} className="flex gap-4">
                                    <div className="flex flex-col items-center">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${s.done ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                                            <s.icon size={18} />
                                        </div>
                                        {i < arr.length - 1 && <div className={`w-0.5 flex-1 my-1 ${s.done ? 'bg-green-300' : 'bg-gray-200'}`} />}
                                    </div>
                                    <div className="pb-6 flex-1">
                                        <p className="font-medium text-sm">{s.label}</p>
                                        <p className="text-xs text-primary-lighter">{s.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Risk */}
            {tab === 'risk' && (
                <div className="space-y-6">
                    {assessment ? (
                        <>
                            <div className="flex items-center justify-between">
                                <h3 className="font-semibold flex items-center gap-2"><ShieldAlert size={18} /> Risk Assessment</h3>
                                <button
                                    onClick={async () => {
                                        try {
                                            const data = await riskReportMut.mutateAsync(id!)
                                            const blob = new Blob([data.report_html], { type: 'text/html' })
                                            const url = URL.createObjectURL(blob)
                                            const a = document.createElement('a')
                                            a.href = url
                                            a.download = `Risk_Report_${data.contract_title || id}.html`
                                            a.click()
                                            URL.revokeObjectURL(url)
                                        } catch {
                                            showToast('Failed to download report', 'error')
                                        }
                                    }}
                                    className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light"
                                >
                                    <FileText size={14} /> Download Report
                                </button>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                {scoreLayers.map(layer => (
                                    <div key={layer.label} className="bg-white rounded-xl border border-border p-6 text-center">
                                        <p className="text-sm text-primary-lighter mb-2">{layer.label} ({layer.weight})</p>
                                        <p className={`text-3xl font-bold ${scoreColor(layer.score)}`}>{(layer.score * 100).toFixed(0)}</p>
                                    </div>
                                ))}
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                {severityChart.length > 0 && (
                                    <div className="bg-white rounded-xl border border-border p-6">
                                        <h3 className="font-semibold mb-4">Findings by Severity</h3>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <PieChart>
                                                <Pie data={severityChart} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
                                                    {severityChart.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                                                </Pie>
                                                <Tooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                                {typeChart.length > 0 && (
                                    <div className="bg-white rounded-xl border border-border p-6">
                                        <h3 className="font-semibold mb-4">Findings by Type</h3>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <BarChart data={typeChart}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                                                <YAxis />
                                                <Tooltip />
                                                <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </div>

                            <h3 className="font-semibold">Open Findings</h3>
                            <div className="space-y-2">
                                {findings?.filter((f: any) => !f.is_resolved).map((f: any) => (
                                    <div key={f.id} className="bg-white rounded-xl border border-border p-4 flex items-start gap-3">
                                        <AlertTriangle size={16} className={f.severity === 'critical' ? 'text-red-600' : f.severity === 'high' ? 'text-orange-600' : 'text-yellow-600'} />
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${sevBadge(f.severity)}`}>{f.severity}</span>
                                                <span className="text-xs text-primary-lighter capitalize">{f.finding_type.replace('_', ' ')}</span>
                                            </div>
                                            <p className="text-sm font-medium">{f.title}</p>
                                            <p className="text-xs text-primary-lighter">{f.description}</p>
                                            {f.suggested_amendment && <p className="text-xs text-blue-600 mt-1">Suggestion: {f.suggested_amendment}</p>}
                                        </div>
                                    </div>
                                ))}
                                {findings?.filter((f: any) => !f.is_resolved).length === 0 && (
                                    <div className="bg-white rounded-xl border border-border p-8 text-center">
                                        <CheckCircle size={32} className="mx-auto mb-2 text-green-500" />
                                        <p className="text-sm text-primary-lighter">All findings resolved</p>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <Shield size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="font-medium">Risk assessment pending</p>
                            <p className="text-sm text-primary-lighter mt-1">Run analysis to see risk scores and findings</p>
                        </div>
                    )}
                </div>
            )}

            {/* Obligations */}
            {tab === 'obligations' && (
                <div className="space-y-3">
                    {obligations?.length > 0 ? obligations.map((o: any) => (
                        <div key={o.id} className="bg-white rounded-xl border border-border p-5 flex items-center gap-4">
                            <div className={`p-2 rounded-lg ${o.status === 'completed' ? 'bg-green-100 text-green-600' : o.status === 'overdue' ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'}`}>
                                {o.status === 'completed' ? <CheckCircle size={18} /> : o.status === 'overdue' ? <AlertTriangle size={18} /> : <Clock size={18} />}
                            </div>
                            <div className="flex-1">
                                <p className="text-sm font-medium">{o.description}</p>
                                <p className="text-xs text-primary-lighter">Due: {o.due_date || 'No date'} · Type: {o.obligation_type}</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${o.status === 'completed' ? 'bg-green-100 text-green-700' : o.status === 'overdue' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                {o.status}
                            </span>
                        </div>
                    )) : (
                        <div className="bg-white rounded-xl border border-border p-12 text-center">
                            <CheckCircle size={40} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-primary-lighter">No obligations extracted from this contract</p>
                        </div>
                    )}
                </div>
            )}

            {/* Approvals — Horizontal Stepper */}
            {tab === 'approvals' && (
                <div className="space-y-6">
                    {/* Stepper */}
                    <div className="bg-white rounded-xl border border-border p-6">
                        <h3 className="font-semibold mb-4">Approval Workflow</h3>
                        {stages.length > 0 ? (
                            <div className="flex items-center">
                                {stageNames.map((name, i) => {
                                    const stage = stageMap[name]
                                    const isDone = stage?.status === 'approved'
                                    const isCurrent = stage?.status === 'pending'
                                    const isRejected = stage?.status === 'rejected'
                                    return (
                                        <div key={name} className="flex items-center flex-1">
                                            <div className="flex flex-col items-center flex-1">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 border-2 transition-colors ${
                                                    isDone ? 'bg-green-600 border-green-600 text-white' :
                                                    isRejected ? 'bg-red-600 border-red-600 text-white' :
                                                    isCurrent ? 'bg-blue-600 border-blue-600 text-white' :
                                                    'bg-gray-100 border-gray-300 text-gray-400'
                                                }`}>
                                                    {isDone ? <CheckCircle size={18} /> :
                                                     isRejected ? <ThumbsDown size={18} /> :
                                                     isCurrent ? <Clock size={18} /> :
                                                     <span className="text-sm">{i + 1}</span>}
                                                </div>
                                                <p className="text-xs font-medium capitalize">{name.replace('_', ' ')}</p>
                                                <p className="text-xs text-primary-lighter">{stage?.approver_name || ''}</p>
                                                {isCurrent && (
                                                    <div className="flex gap-2 mt-2">
                                                        <button
                                                            onClick={() => handleApproveStage(stage.id)}
                                                            disabled={actionLoading === stage.id}
                                                            className="px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-1"
                                                        >
                                                            {actionLoading === stage.id ? <Loader2 size={10} className="animate-spin" /> : <ThumbsUp size={10} />}
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => handleRejectStage(stage.id)}
                                                            disabled={actionLoading === stage.id}
                                                            className="px-3 py-1 bg-red-600 text-white text-xs rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-1"
                                                        >
                                                            {actionLoading === stage.id ? <Loader2 size={10} className="animate-spin" /> : <ThumbsDown size={10} />}
                                                            Reject
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                            {i < stageNames.length - 1 && (
                                                <div className={`h-0.5 flex-1 mx-2 ${isDone ? 'bg-green-400' : 'bg-gray-200'}`} />
                                            )}
                                        </div>
                                    )
                                })}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <p className="text-primary-lighter">No approval workflow started</p>
                                <button
                                    onClick={handleSubmitForApproval}
                                    disabled={actionLoading === 'submit'}
                                    className="mt-3 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-light disabled:opacity-50"
                                >
                                    {actionLoading === 'submit' ? <Loader2 size={14} className="animate-spin inline mr-1" /> : null}
                                    Submit for Approval
                                </button>
                            </div>
                        )}
                        {allApproved && (
                            <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center gap-2 text-green-700 text-sm">
                                <CheckCircle size={16} /> All stages approved. Contract is fully cleared.
                            </div>
                        )}
                    </div>

                    {/* Status transitions */}
                    <div className="bg-white rounded-xl border border-border p-6">
                        <h3 className="font-semibold mb-3">Status Transition</h3>
                        <div className="flex gap-2 flex-wrap">
                            {['draft', 'in_review', 'approved', 'signed', 'active', 'terminated'].map(s => (
                                <button
                                    key={s}
                                    onClick={() => handleTransition(s)}
                                    disabled={contract.status === s || actionLoading === `transition-${s}`}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                                        contract.status === s
                                            ? 'bg-primary text-white'
                                            : 'border border-border hover:bg-gray-50 disabled:opacity-50'
                                    }`}
                                >
                                    {actionLoading === `transition-${s}` ? <Loader2 size={10} className="animate-spin inline" /> : null}
                                    {s.replace('_', ' ')}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Comments */}
            {tab === 'comments' && (
                <div className="space-y-4">
                    <div className="bg-white rounded-xl border border-border p-4">
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-white text-xs font-bold">A</div>
                            <div className="flex-1">
                                <textarea
                                    value={newComment}
                                    onChange={e => setNewComment(e.target.value)}
                                    placeholder="Add a comment..."
                                    className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    rows={2}
                                />
                                <div className="flex justify-end mt-2">
                                    <button
                                        onClick={handlePostComment}
                                        disabled={!newComment.trim() || actionLoading === 'comment'}
                                        className="bg-primary text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-primary-light transition-colors disabled:opacity-50"
                                    >
                                        {actionLoading === 'comment' ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                        Post
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="space-y-3">
                        {comments?.length > 0 ? comments.map((c: any) => (
                            <div key={c.id} className="bg-white rounded-xl border border-border p-4 flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary-light flex items-center justify-center text-white text-xs font-bold">
                                    {c.author_name?.charAt(0) || 'U'}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium">{c.author_name}</span>
                                        <span className="text-xs text-primary-lighter capitalize">{c.author_role}</span>
                                        <span className="text-xs text-primary-lighter">{new Date(c.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-sm">{c.content}</p>
                                </div>
                            </div>
                        )) : (
                            <div className="bg-white rounded-xl border border-border p-12 text-center">
                                <MessageSquare size={40} className="mx-auto mb-3 text-gray-300" />
                                <p className="text-primary-lighter">No comments yet</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* PDF */}
            {tab === 'pdf' && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white rounded-xl border border-border overflow-hidden"
                    style={{ height: 750 }}
                >
                    {contract.pdf_url || contract.pdf_path ? (
                        <PDFViewer url={contract.pdf_url || `/api/v1/contracts/${contract.id}/pdf`} contractId={contract.id} />
                    ) : (
                        <div className="text-center py-12">
                            <FileText size={48} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-primary-lighter font-medium">PDF preview not available</p>
                            <p className="text-sm text-primary-lighter mt-1">The contract was uploaded without a PDF file</p>
                        </div>
                    )}
                </motion.div>
            )}
        </div>
    )
}
