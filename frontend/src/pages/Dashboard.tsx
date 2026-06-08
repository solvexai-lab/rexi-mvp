import { useNavigate } from 'react-router-dom'
import {
    FileText, AlertTriangle, Bell, CheckCircle, Clock,
    ArrowRight, TrendingUp, Zap, Shield
} from 'lucide-react'
import { useDashboardSummary, useOrganization, usePlaybookSummary } from '../hooks/useQueries'
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts'

const STATUS_COLORS: Record<string, string> = {
    active: '#22C55E',
    signed: '#8B5CF6',
    approved: '#3B82F6',
    analyzed: '#EC4899',
    draft: '#9CA3AF',
    in_review: '#F59E0B',
    expired: '#6B7280',
    terminated: '#EF4444',
}

function SkeletonCard() {
    return <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
        <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
        <div className="h-8 w-20 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-48 bg-gray-200 rounded" />
    </div>
}

function ActionCard({ icon: Icon, title, subtitle, meta, color, onClick }: any) {
    return (
        <div
            onClick={onClick}
            className="bg-white rounded-xl border border-gray-200 p-5 cursor-pointer hover:border-gray-300 hover:shadow-sm transition-all group"
        >
            <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${color.bg} ${color.text}`}>
                    <Icon size={18} />
                </div>
                <ArrowRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm mb-1">{title}</h3>
            <p className="text-sm text-gray-500 mb-2">{subtitle}</p>
            {meta && <p className="text-xs text-gray-400">{meta}</p>}
        </div>
    )
}

function StatPill({ label, value, color }: any) {
    return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50">
            <span className={`w-2 h-2 rounded-full ${color}`} />
            <span className="text-sm text-gray-600">{label}</span>
            <span className="text-sm font-bold text-gray-900 ml-auto">{value}</span>
        </div>
    )
}

export default function DashboardPage() {
    const { data, isLoading } = useDashboardSummary()
    const { data: playbookSummary } = usePlaybookSummary()
    const { data: orgData } = useOrganization()
    const navigate = useNavigate()

    if (isLoading || !data) {
        return (
            <div className="p-8 max-w-7xl mx-auto">
                <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-6" />
                <div className="grid grid-cols-4 gap-5 mb-6">
                    {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="grid grid-cols-2 gap-5">
                    <SkeletonCard /><SkeletonCard />
                </div>
            </div>
        )
    }

    const contracts = data.contracts || {}
    const obligations = data.obligations || {}
    const regulatory = data.regulatory || {}
    const totalValue = data.platform_value?.total_value_inr || 0

    const statusChart = Object.entries(contracts.by_status || {})
        .map(([name, value]: [string, any]) => ({
            name: name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            value,
            color: STATUS_COLORS[name] || '#3B82F6'
        }))
        .filter(d => d.value > 0)

    // Build action cards from real summary data
    const pendingObligations = obligations.by_status?.pending || 0
    const unreadAlerts = Object.values(regulatory.unread_alerts || {}).reduce((a: any, b: any) => a + b, 0)
    const analyzedContracts = contracts.by_status?.analyzed || 0
    const activeContracts = contracts.by_status?.active || 0

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-xl font-bold text-gray-900">Good morning, Counsel</h1>
                    <p className="text-sm text-gray-500 mt-0.5">
                        {orgData?.name || 'Your Organization'} · {contracts.total || 0} contracts · ₹{(totalValue / 1e7).toFixed(1)}Cr under management
                    </p>
                </div>
            </div>

            {/* Action Cards — what needs attention */}
            <div className="grid grid-cols-4 gap-5 mb-6">
                <ActionCard
                    icon={AlertTriangle}
                    title={`${pendingObligations} obligation${pendingObligations !== 1 ? 's' : ''} pending`}
                    subtitle="Require action or review"
                    meta="Across active contracts"
                    color={{ bg: 'bg-amber-50', text: 'text-amber-700' }}
                    onClick={() => navigate('/obligations')}
                />
                <ActionCard
                    icon={Shield}
                    title={`${playbookSummary?.total_violations || 0} playbook violation${(playbookSummary?.total_violations || 0) !== 1 ? 's' : ''}`}
                    subtitle="Deviations from standard terms"
                    meta={`Across ${playbookSummary?.contracts_with_violations || 0} contracts · Avg score ${playbookSummary?.average_score ?? '—'}`}
                    color={{ bg: 'bg-red-50', text: 'text-red-700' }}
                    onClick={() => navigate('/contracts')}
                />
                <ActionCard
                    icon={FileText}
                    title={`${analyzedContracts} contract${analyzedContracts !== 1 ? 's' : ''} ready for review`}
                    subtitle="AI analysis complete"
                    meta="Awaiting legal sign-off"
                    color={{ bg: 'bg-blue-50', text: 'text-blue-700' }}
                    onClick={() => navigate('/contracts')}
                />
                <ActionCard
                    icon={Bell}
                    title={`${unreadAlerts} regulatory alert${unreadAlerts !== 1 ? 's' : ''}`}
                    subtitle="May affect contract terms"
                    meta="SEBI, RBI, MCA updates"
                    color={{ bg: 'bg-purple-50', text: 'text-purple-700' }}
                    onClick={() => navigate('/regulatory')}
                />
            </div>

            {/* Middle Row */}
            <div className="grid grid-cols-3 gap-5 mb-6">
                {/* Contract Status */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                    <h3 className="font-semibold text-sm text-gray-900 mb-4">Contract Status</h3>
                    {statusChart.length > 0 ? (
                        <ResponsiveContainer width="100%" height={180}>
                            <PieChart>
                                <Pie
                                    data={statusChart}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={45}
                                    outerRadius={75}
                                    paddingAngle={3}
                                >
                                    {statusChart.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[180px] flex items-center justify-center text-sm text-gray-400">
                            No contracts yet
                        </div>
                    )}
                    <div className="flex flex-wrap gap-2 mt-2">
                        {statusChart.map(s => (
                            <span key={s.name} className="text-[10px] flex items-center gap-1 text-gray-500">
                                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                                {s.name} ({s.value})
                            </span>
                        ))}
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                    <h3 className="font-semibold text-sm text-gray-900 mb-4">Portfolio Snapshot</h3>
                    <div className="space-y-2">
                        <StatPill label="Active" value={activeContracts} color="bg-green-500" />
                        <StatPill label="Analyzed" value={analyzedContracts} color="bg-pink-500" />
                        <StatPill label="Approved" value={contracts.by_status?.approved || 0} color="bg-blue-500" />
                        <StatPill label="Signed" value={contracts.by_status?.signed || 0} color="bg-purple-500" />
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-500">Total Value</span>
                            <span className="text-sm font-bold text-gray-900">₹{(totalValue / 1e7).toFixed(1)}Cr</span>
                        </div>
                    </div>
                </div>

                {/* Obligations Breakdown */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                    <h3 className="font-semibold text-sm text-gray-900 mb-4">Obligations</h3>
                    <div className="space-y-3">
                        {[
                            { label: 'Pending', value: obligations.by_status?.pending || 0, color: 'text-amber-700 bg-amber-50' },
                            { label: 'Completed', value: obligations.by_status?.completed || 0, color: 'text-green-700 bg-green-50' },
                            { label: 'Overdue', value: obligations.by_status?.overdue || 0, color: 'text-red-700 bg-red-50' },
                        ].map(item => (
                            <div
                                key={item.label}
                                onClick={() => navigate(`/obligations?status=${item.label.toLowerCase()}`)}
                                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                            >
                                <span className="text-sm font-medium text-gray-700">{item.label}</span>
                                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${item.color}`}>
                                    {item.value}
                                </span>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={() => navigate('/obligations')}
                        className="w-full mt-4 text-xs font-medium text-gray-500 hover:text-gray-700 flex items-center justify-center gap-1 transition-colors"
                    >
                        View all obligations <ArrowRight size={12} />
                    </button>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-sm text-gray-900">Recent Activity</h3>
                    <span className="text-xs text-gray-400">Last 24 hours</span>
                </div>
                {data?.recent_logs?.length > 0 ? (
                    <div className="space-y-2">
                        {data.recent_logs.slice(0, 5).map((log: any, i: number) => (
                            <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                                <div className={`p-1.5 rounded-lg ${
                                    log.status === 'completed' ? 'bg-green-100 text-green-600' :
                                    log.status === 'failed' ? 'bg-red-100 text-red-600' :
                                    'bg-amber-100 text-amber-600'
                                }`}>
                                    {log.status === 'completed' ? <CheckCircle size={14} /> :
                                     log.status === 'failed' ? <AlertTriangle size={14} /> :
                                     <Clock size={14} />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-800 capitalize">
                                        {log.automation_type.replace(/_/g, ' ')}
                                    </p>
                                    <p className="text-xs text-gray-400 truncate">{log.output_summary}</p>
                                </div>
                                <span className="text-xs text-gray-400 tabular-nums">{log.duration_ms}ms</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-sm text-gray-400 py-8 text-center">No recent activity</div>
                )}
            </div>
        </div>
    )
}
