import { motion } from 'framer-motion'
import { ShieldAlert, AlertTriangle, CheckCircle, TrendingUp, BarChart3, FileText, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useRiskDashboard, useRiskFindings, useRiskHistory, useResolveFinding } from '../hooks/useQueries'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, BarChart, Bar
} from 'recharts'

const COLORS = ['#EF4444', '#F59E0B', '#3B82F6', '#22C55E', '#8B5CF6']

function SkeletonCard() {
    return <div className="bg-white rounded-xl border border-border p-6 animate-pulse">
        <div className="h-10 w-10 rounded-lg bg-gray-200 mb-3" />
        <div className="h-8 w-20 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-32 bg-gray-200 rounded" />
    </div>
}

export default function RiskPage() {
    const navigate = useNavigate()
    const { data: dashboard, isLoading: dLoading } = useRiskDashboard()
    const { data: findingsData, isLoading: fLoading } = useRiskFindings()
    const { data: history, isLoading: hLoading } = useRiskHistory()
    const resolveMutation = useResolveFinding()

    const findings = findingsData || []
    const loading = dLoading || fLoading || hLoading

    if (loading) {
        return (
            <div className="p-8">
                <motion.h1
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-2xl font-bold mb-6"
                >Risk Assessment</motion.h1>
                <div className="grid grid-cols-4 gap-6 mb-8">
                    {[1,2,3,4].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="grid grid-cols-2 gap-6">
                    <SkeletonCard /><SkeletonCard />
                </div>
            </div>
        )
    }

    const openFindings = findings.filter((f: any) => !f.is_resolved)
    const resolvedFindings = findings.filter((f: any) => f.is_resolved)

    const severityData = [
        { name: 'Critical', value: openFindings.filter((f: any) => f.severity === 'critical').length, color: '#EF4444' },
        { name: 'High', value: openFindings.filter((f: any) => f.severity === 'high').length, color: '#F59E0B' },
        { name: 'Medium', value: openFindings.filter((f: any) => f.severity === 'medium').length, color: '#3B82F6' },
        { name: 'Low', value: openFindings.filter((f: any) => f.severity === 'low').length, color: '#22C55E' },
    ].filter(d => d.value > 0)

    const typeCounts: Record<string, number> = {}
    openFindings.forEach((f: any) => {
        typeCounts[f.finding_type] = (typeCounts[f.finding_type] || 0) + 1
    })
    const typeData = Object.entries(typeCounts).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value
    }))

    const scoreColor = (s: number) => {
        if (s < 0.3) return 'text-green-600'
        if (s < 0.6) return 'text-yellow-600'
        if (s < 0.8) return 'text-orange-600'
        return 'text-red-600'
    }

    return (
        <div className="p-8">
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between mb-6"
            >
                <h1 className="text-2xl font-bold">Risk Assessment</h1>
                <div className="flex items-center gap-2 text-sm">
                    <span className={`px-3 py-1 rounded-full font-medium ${scoreColor(dashboard?.avg_risk_score || 0)} bg-gray-50`}>
                        Overall Risk: {((dashboard?.avg_risk_score || 0) * 100).toFixed(0)}/100
                    </span>
                </div>
            </motion.div>

            {/* Stats Row */}
            <div className="grid grid-cols-4 gap-6 mb-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 cursor-pointer"
                    onClick={() => navigate('/contracts')}
                >
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-orange-50"><TrendingUp size={18} className="text-orange-600" /></div>
                        <span className="text-sm text-primary-lighter">Avg Risk Score</span>
                    </div>
                    <p className="text-2xl font-bold">{dashboard?.avg_risk_score || 0}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 cursor-pointer"
                    onClick={() => navigate('/risk')}
                >
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-red-50"><ShieldAlert size={18} className="text-red-600" /></div>
                        <span className="text-sm text-primary-lighter">Open Findings</span>
                    </div>
                    <p className="text-2xl font-bold">{openFindings.length}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-green-50"><CheckCircle size={18} className="text-green-600" /></div>
                        <span className="text-sm text-primary-lighter">Resolved</span>
                    </div>
                    <p className="text-2xl font-bold">{resolvedFindings.length}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 cursor-pointer"
                    onClick={() => navigate('/contracts')}
                >
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-blue-50"><BarChart3 size={18} className="text-blue-600" /></div>
                        <span className="text-sm text-primary-lighter">Total Contracts</span>
                    </div>
                    <p className="text-2xl font-bold">{dashboard?.total_contracts || 0}</p>
                </motion.div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-6 mb-8">
                {/* Risk Trend */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Risk Score Trend</h3>
                    {history && history.length > 1 ? (
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={history}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                                <Tooltip formatter={(v: any) => (v * 100).toFixed(0)} />
                                <Line type="monotone" dataKey="overall" stroke="#EF4444" strokeWidth={2} dot={{ r: 3 }} name="Overall" />
                                <Line type="monotone" dataKey="playbook" stroke="#3B82F6" strokeWidth={2} dot={{ r: 2 }} name="Playbook" />
                                <Line type="monotone" dataKey="law" stroke="#8B5CF6" strokeWidth={2} dot={{ r: 2 }} name="Law" />
                                <Line type="monotone" dataKey="regulatory" stroke="#F59E0B" strokeWidth={2} dot={{ r: 2 }} name="Regulatory" />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[250px] flex items-center justify-center text-sm text-primary-lighter">
                            Upload more contracts to see risk trends
                        </div>
                    )}
                </motion.div>

                {/* Findings by Severity */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Findings by Severity</h3>
                    {severityData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie data={severityData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                                    outerRadius={80} label={({ name, value }: any) => `${name}: ${value}`}>
                                    {severityData.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[250px] flex items-center justify-center text-sm text-primary-lighter">
                            No findings to display
                        </div>
                    )}
                </motion.div>
            </div>

            {/* Findings by Type */}
            {typeData.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    className="bg-white rounded-xl border border-border p-6 mb-8"
                >
                    <h3 className="font-semibold mb-4">Findings by Type</h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={typeData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>
            )}

            {/* Open Findings List */}
            <motion.h3
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="font-semibold mb-4"
            >Open Findings ({openFindings.length})</motion.h3>
            {openFindings.length > 0 ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-3"
                >
                    {openFindings.map((f: any, i: number) => (
                        <motion.div
                            key={f.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 * i }}
                            whileHover={{ x: 4, boxShadow: '0 4px 20px -4px rgba(0,0,0,0.08)' }}
                            className="bg-white rounded-xl border border-border p-5 flex items-start gap-4 cursor-pointer group"
                            onClick={() => f.contract_id && navigate(`/contracts/${f.contract_id}?tab=risk`)}
                        >
                            <div className={`p-2 rounded-lg shrink-0 ${
                                f.severity === 'critical' ? 'bg-red-100 text-red-600' :
                                f.severity === 'high' ? 'bg-orange-100 text-orange-600' :
                                f.severity === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                                'bg-blue-100 text-blue-600'
                            }`}>
                                <AlertTriangle size={18} />
                            </div>
                            <div className="flex-1 min-w-0">
                                {/* Contract link badge */}
                                {f.contract_id && (
                                    <div className="flex items-center gap-1.5 mb-1.5">
                                        <FileText size={12} className="text-gray-400" />
                                        <span className="text-xs text-gray-500 font-medium truncate">
                                            {f.contract_title || 'Unknown Contract'}
                                        </span>
                                        <ArrowRight size={12} className="text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                )}
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${
                                        f.severity === 'critical' ? 'bg-red-100 text-red-700' :
                                        f.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                                        f.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-blue-100 text-blue-700'
                                    }`}>{f.severity}</span>
                                    <span className="text-xs text-primary-lighter capitalize">{f.finding_type.replace(/_/g, ' ')}</span>
                                </div>
                                <p className="font-medium mb-1">{f.title}</p>
                                {f.description && (
                                    <p className="text-sm text-primary-lighter mb-1">{f.description}</p>
                                )}
                                {f.suggested_amendment && (
                                    <p className="text-xs text-blue-600 mt-2 bg-blue-50 px-2 py-1 rounded inline-block">
                                        Suggestion: {f.suggested_amendment}
                                    </p>
                                )}
                                {f.statute_reference && (
                                    <p className="text-xs text-primary-lighter mt-1">{f.statute_reference}</p>
                                )}
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation()
                                    resolveMutation.mutate(f.id)
                                }}
                                disabled={resolveMutation.variables === f.id && resolveMutation.isPending}
                                className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 shrink-0"
                            >
                                {resolveMutation.variables === f.id && resolveMutation.isPending ? '...' : 'Resolve'}
                            </button>
                        </motion.div>
                    ))}
                </motion.div>
            ) : (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-xl border border-border p-12 text-center"
                >
                    <CheckCircle size={40} className="mx-auto mb-3 text-green-500" />
                    <p className="font-medium">All findings resolved!</p>
                    <p className="text-sm text-primary-lighter mt-1">No open risk findings for this organization.</p>
                </motion.div>
            )}
        </div>
    )
}
