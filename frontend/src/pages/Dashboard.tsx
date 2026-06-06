import { motion } from 'framer-motion'
import {
    FileText, ShieldAlert, Bell, ClipboardList,
    AlertTriangle, CheckCircle, Clock, Gavel,
    DollarSign, TrendingUp, Timer, ShieldCheck
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useDashboardSummary, useOrganization } from '../hooks/useQueries'
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
    BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts'

const COLORS: Record<string, string> = {
    critical: '#EF4444',
    high: '#F59E0B',
    medium: '#3B82F6',
    low: '#22C55E',
    draft: '#9CA3AF',
    in_review: '#F59E0B',
    approved: '#3B82F6',
    signed: '#8B5CF6',
    active: '#22C55E',
    expired: '#6B7280',
    terminated: '#EF4444',
    analyzed: '#EC4899',
}

function AnimatedNumber({ value, suffix = '' }: { value: number; suffix?: string }) {
    const [display, setDisplay] = useState(0)
    useEffect(() => {
        const step = value / 20
        let current = 0
        const timer = setInterval(() => {
            current += step
            if (current >= value) {
                setDisplay(value)
                clearInterval(timer)
            } else {
                setDisplay(Math.round(current * 10) / 10)
            }
        }, 30)
        return () => clearInterval(timer)
    }, [value])
    return <span>{display}{suffix}</span>
}

import { useState, useEffect } from 'react'

function KpiCard({ icon: Icon, label, value, color, suffix = '', subtext = '', index = 0, onClick }: any) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08, duration: 0.4, ease: 'easeOut' }}
            whileHover={{ y: -4, boxShadow: '0 12px 40px -12px rgba(0,0,0,0.12)' }}
            onClick={onClick}
            className={`bg-white rounded-xl border border-border p-6 ${onClick ? 'cursor-pointer hover:border-primary/30' : 'cursor-default'}`}
        >
            <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-lg ${color.bg}`}>
                    <Icon size={20} className={color.text} />
                </div>
                {subtext && <span className="text-xs text-primary-lighter">{subtext}</span>}
            </div>
            <p className="text-2xl font-bold mb-1">
                {typeof value === 'number' ? <AnimatedNumber value={value} suffix={suffix} /> : value}
            </p>
            <p className="text-sm text-primary-lighter">{label}</p>
        </motion.div>
    )
}

function RiskGauge({ score }: { score: number }) {
    const pct = Math.min(Math.max(score * 100, 0), 100)
    const color = pct > 60 ? '#EF4444' : pct > 40 ? '#F59E0B' : '#22C55E'
    const circumference = 2 * Math.PI * 45
    const strokeDashoffset = circumference - (pct / 100) * circumference

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="bg-white rounded-xl border border-border p-6"
        >
            <h3 className="font-semibold mb-4">Average Risk Score</h3>
            <div className="flex items-center justify-center">
                <div className="relative w-40 h-40">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" stroke="#E5E5E5" strokeWidth="8" fill="none" />
                        <circle cx="50" cy="50" r="45" stroke={color} strokeWidth="8" fill="none"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                        />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-3xl font-bold" style={{ color }}>{pct.toFixed(0)}</span>
                        <span className="text-xs text-primary-lighter">/ 100</span>
                    </div>
                </div>
            </div>
            <div className="flex justify-center gap-4 mt-3 text-xs">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />Low</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />Med</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />High</span>
            </div>
        </motion.div>
    )
}

function SkeletonCard() {
    return <div className="bg-white rounded-xl border border-border p-6 animate-pulse">
        <div className="h-10 w-10 rounded-lg bg-gray-200 mb-3" />
        <div className="h-8 w-20 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-32 bg-gray-200 rounded" />
    </div>
}

export default function DashboardPage() {
    const { data, isLoading } = useDashboardSummary()
    const { data: orgData } = useOrganization()
    const navigate = useNavigate()

    if (isLoading || !data) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
                <div className="grid grid-cols-5 gap-6 mb-6">
                    {[1, 2, 3, 4, 5].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="grid grid-cols-3 gap-6">
                    <SkeletonCard /><SkeletonCard /><SkeletonCard />
                </div>
            </div>
        )
    }

    const risk = data.risk || {}
    const contracts = data.contracts || {}
    const obligations = data.obligations || {}
    const regulatory = data.regulatory || {}

    const severityChart = [
        { name: 'Critical', value: risk.by_severity?.critical || 0, color: COLORS.critical },
        { name: 'High', value: risk.by_severity?.high || 0, color: COLORS.high },
        { name: 'Medium', value: risk.by_severity?.medium || 0, color: COLORS.medium },
        { name: 'Low', value: risk.by_severity?.low || 0, color: COLORS.low },
    ].filter(d => d.value > 0)

    const statusChart = Object.entries(contracts.by_status || {}).map(([name, value]: [string, any]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
        color: COLORS[name] || '#3B82F6'
    })).filter(d => d.value > 0)

    const obligationCards = [
        { label: 'Pending', value: obligations.by_status?.pending || 0, color: 'text-orange-600 bg-orange-50' },
        { label: 'Completed', value: obligations.by_status?.completed || 0, color: 'text-green-600 bg-green-50' },
        { label: 'Overdue', value: obligations.by_status?.overdue || 0, color: 'text-red-600 bg-red-50' },
    ]

    const unreadTotal = Object.values(regulatory.unread_alerts || {}).reduce((a: any, b: any) => a + b, 0)

    return (
        <div className="p-8">
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between mb-6"
            >
                <h1 className="text-2xl font-bold">Dashboard</h1>
                <span className="text-sm text-primary-lighter">{orgData?.name || 'Your Organization'}</span>
            </motion.div>

            {/* KPI Row */}
            <div className="grid grid-cols-5 gap-6 mb-6">
                <KpiCard icon={FileText} label="Total Contracts" value={contracts.total}
                    color={{ bg: 'bg-blue-50', text: 'text-blue-600' }} index={0}
                    onClick={() => navigate('/contracts')} />
                <KpiCard icon={ShieldAlert} label="Open Findings" value={risk.open_findings}
                    color={{ bg: 'bg-red-50', text: 'text-red-600' }} index={1}
                    onClick={() => navigate('/risk')} />
                <KpiCard icon={ClipboardList} label="Pending Obligations" value={obligations.by_status?.pending || 0}
                    color={{ bg: 'bg-orange-50', text: 'text-orange-600' }} index={2}
                    onClick={() => navigate('/obligations?status=pending')} />
                <KpiCard icon={Bell} label="Unread Alerts" value={unreadTotal}
                    color={{ bg: 'bg-purple-50', text: 'text-purple-600' }} index={3}
                    onClick={() => navigate('/regulatory')} />
                <KpiCard icon={Gavel} label="Active Playbook Rules" value={data.active_playbook_rules || 0}
                    color={{ bg: 'bg-indigo-50', text: 'text-indigo-600' }} index={4}
                    onClick={() => navigate('/playbook')} />
            </div>

            {/* Platform Value Row — deterministic, no AI */}
            {data.platform_value && (
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.35 }}
                    className="mb-6"
                >
                    <div className="flex items-center gap-2 mb-3">
                        <TrendingUp size={16} className="text-green-600" />
                        <h2 className="text-sm font-semibold text-gray-700">Platform Value — Deterministic Metrics</h2>
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                        <KpiCard icon={DollarSign} label="Value Under Management"
                            value={`₹${((data.platform_value.total_value_inr || 0) / 1e7).toFixed(1)}Cr`}
                            color={{ bg: 'bg-green-50', text: 'text-green-600' }} index={0} />
                        <KpiCard icon={TrendingUp} label="Automation Rate"
                            value={`${data.platform_value.automation_rate || 0}%`}
                            color={{ bg: 'bg-emerald-50', text: 'text-emerald-600' }} index={1}
                            subtext="Contracts auto-processed" />
                        <KpiCard icon={Timer} label="Time Saved"
                            value={`${data.platform_value.time_saved_hours || 0}h`}
                            color={{ bg: 'bg-teal-50', text: 'text-teal-600' }} index={2}
                            subtext="Estimated vs manual review" />
                        <KpiCard icon={ShieldCheck} label="Compliance Coverage"
                            value={`${data.platform_value.compliance_coverage || 0}%`}
                            color={{ bg: 'bg-cyan-50', text: 'text-cyan-600' }} index={3}
                            subtext="Contracts with risk assessment" />
                    </div>
                </motion.div>
            )}

            {/* Middle Row */}
            <div className="grid grid-cols-3 gap-6 mb-6">
                <div onClick={() => navigate('/risk')} className="cursor-pointer">
                    <RiskGauge score={risk.avg_score || 0} />
                </div>

                {/* Findings by Severity */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5, duration: 0.5 }}
                    onClick={() => navigate('/risk')}
                    className="bg-white rounded-xl border border-border p-6 cursor-pointer hover:border-primary/30 transition-colors"
                >
                    <h3 className="font-semibold mb-4">Open Findings by Severity</h3>
                    {severityChart.length > 0 ? (
                        <ResponsiveContainer width="100%" height={180}>
                            <BarChart data={severityChart} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" />
                                <YAxis dataKey="name" type="category" width={70} tick={{ fontSize: 12 }} />
                                <Tooltip />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {severityChart.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[180px] flex items-center justify-center text-sm text-primary-lighter">
                            No open findings — great job!
                        </div>
                    )}
                </motion.div>

                {/* Contract Status Donut */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6, duration: 0.5 }}
                    onClick={() => navigate('/contracts')}
                    className="bg-white rounded-xl border border-border p-6 cursor-pointer hover:border-primary/30 transition-colors"
                >
                    <h3 className="font-semibold mb-4">Contract Status</h3>
                    {statusChart.length > 0 ? (
                        <ResponsiveContainer width="100%" height={180}>
                            <PieChart>
                                <Pie data={statusChart} dataKey="value" nameKey="name" cx="50%" cy="50%"
                                    innerRadius={50} outerRadius={75} paddingAngle={3}>
                                    {statusChart.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[180px] flex items-center justify-center text-sm text-primary-lighter">
                            No contracts yet
                        </div>
                    )}
                </motion.div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-3 gap-6">
                {/* Obligations */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7, duration: 0.5 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Obligations</h3>
                    <div className="space-y-3">
                        {obligationCards.map(c => (
                            <div
                                key={c.label}
                                onClick={() => navigate(`/obligations?status=${c.label.toLowerCase()}`)}
                                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                            >
                                <span className="text-sm font-medium">{c.label}</span>
                                <span className={`px-3 py-1 rounded-full text-sm font-bold ${c.color}`}>{c.value}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Recent Activity */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8, duration: 0.5 }}
                    className="bg-white rounded-xl border border-border p-6 col-span-2"
                >
                    <h3 className="font-semibold mb-4">Recent Activity</h3>
                    {data?.recent_logs?.length > 0 ? (
                        <div className="space-y-3">
                            {data.recent_logs.map((log: any, i: number) => (
                                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50">
                                    <div className={`p-1.5 rounded-lg ${
                                        log.status === 'completed' ? 'bg-green-100 text-green-600' :
                                        log.status === 'failed' ? 'bg-red-100 text-red-600' :
                                        'bg-yellow-100 text-yellow-600'
                                    }`}>
                                        {log.status === 'completed' ? <CheckCircle size={14} /> :
                                         log.status === 'failed' ? <AlertTriangle size={14} /> :
                                         <Clock size={14} />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium capitalize">{log.automation_type.replace(/_/g, ' ')}</p>
                                        <p className="text-xs text-primary-lighter truncate">{log.output_summary}</p>
                                    </div>
                                    <span className="text-xs text-primary-lighter whitespace-nowrap">{log.duration_ms}ms</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-primary-lighter py-8 text-center">No recent activity</div>
                    )}
                </motion.div>
            </div>
        </div>
    )
}
