import { useState } from 'react'
import { motion } from 'framer-motion'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts'
import {
    Building2, FileText, AlertTriangle, TrendingUp, DollarSign,
    ChevronRight, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import { useCounterpartyDashboard } from '../hooks/useQueries'

const RISK_COLORS = {
    high: '#EF4444',
    medium: '#F59E0B',
    low: '#22C55E',
}

const PIE_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#6366F1']

export default function CounterpartyPage() {
    const { data, isLoading, error } = useCounterpartyDashboard()
    const [selected, setSelected] = useState<string | null>(null)

    const counterparties = data?.counterparties || []

    const selectedCp = counterparties.find((c: any) => c.name === selected)

    const riskDistribution = [
        { name: 'High Risk', value: counterparties.filter((c: any) => c.risk_tier === 'high').length },
        { name: 'Medium Risk', value: counterparties.filter((c: any) => c.risk_tier === 'medium').length },
        { name: 'Low Risk', value: counterparties.filter((c: any) => c.risk_tier === 'low').length },
    ].filter(d => d.value > 0)

    const totalValue = counterparties.reduce((sum: number, c: any) => sum + (c.total_value_inr || 0), 0)
    const totalContracts = counterparties.reduce((sum: number, c: any) => sum + (c.contract_count || 0), 0)
    const totalCritical = counterparties.reduce((sum: number, c: any) => sum + (c.critical_findings || 0), 0)
    const avgRisk = counterparties.length
        ? counterparties.reduce((sum: number, c: any) => sum + (c.avg_risk_score || 0), 0) / counterparties.length
        : 0

    if (isLoading) {
        return (
            <div className="p-8 space-y-6">
                <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-gray-200 rounded-xl animate-pulse" />)}
                </div>
                <div className="h-96 bg-gray-200 rounded-xl animate-pulse" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
                    <AlertTriangle className="inline mr-2" size={20} />
                    Failed to load counterparty data. Is the backend running?
                </div>
            </div>
        )
    }

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Counterparty Dashboard</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Pure SQL aggregation — no AI calls. Risk, exposure, and contract density per vendor.
                    </p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
                    <Building2 size={16} />
                    {counterparties.length} counterparties
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-4">
                <KpiCard
                    icon={<FileText size={20} className="text-blue-600" />}
                    label="Total Contracts"
                    value={totalContracts}
                    sub={`Across ${counterparties.length} counterparties`}
                />
                <KpiCard
                    icon={<DollarSign size={20} className="text-green-600" />}
                    label="Total Exposure"
                    value={`₹${(totalValue / 1e7).toFixed(1)}Cr`}
                    sub="Aggregate contract value"
                />
                <KpiCard
                    icon={<AlertTriangle size={20} className="text-red-600" />}
                    label="Critical Findings"
                    value={totalCritical}
                    sub="Unresolved risk items"
                    trend={totalCritical > 5 ? 'up' : 'down'}
                />
                <KpiCard
                    icon={<TrendingUp size={20} className="text-amber-600" />}
                    label="Avg Risk Score"
                    value={avgRisk.toFixed(2)}
                    sub="0 = safe, 1 = critical"
                    trend={avgRisk > 0.5 ? 'up' : 'down'}
                />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-2 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
                >
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Risk Score by Counterparty</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={counterparties} layout="vertical" margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                            <XAxis type="number" domain={[0, 1]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
                            <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                            <Tooltip
                                formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, 'Risk Score']}
                                contentStyle={{ borderRadius: 12, border: '1px solid #E5E7EB' }}
                            />
                            <Bar dataKey="avg_risk_score" radius={[0, 4, 4, 0]}>
                                {counterparties.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.risk_tier as keyof typeof RISK_COLORS] || '#9CA3AF'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
                >
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Risk Distribution</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={riskDistribution}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={4}
                                dataKey="value"
                            >
                                {riskDistribution.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                ))}
                            </Pie>
                            <Legend />
                            <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E5E7EB' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </motion.div>
            </div>

            {/* Table */}
            <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
            >
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">Counterparty Breakdown</h3>
                    <span className="text-xs text-gray-400">Click a row for details</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Counterparty</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Contracts</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Value (INR)</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Risk Score</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Critical</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">High</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Next Renewal</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Tier</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {counterparties.map((cp: any) => (
                                <tr
                                    key={cp.name}
                                    onClick={() => setSelected(cp.name === selected ? null : cp.name)}
                                    className={`hover:bg-gray-50 cursor-pointer transition-colors ${selected === cp.name ? 'bg-blue-50' : ''}`}
                                >
                                    <td className="px-6 py-3 font-medium text-gray-900">{cp.name}</td>
                                    <td className="px-6 py-3 text-gray-600">{cp.contract_count}</td>
                                    <td className="px-6 py-3 text-gray-600">₹{(cp.total_value_inr / 1e5).toFixed(1)}L</td>
                                    <td className="px-6 py-3">
                                        <RiskBadge score={cp.avg_risk_score} tier={cp.risk_tier} />
                                    </td>
                                    <td className="px-6 py-3 text-red-600 font-medium">{cp.critical_findings}</td>
                                    <td className="px-6 py-3 text-amber-600 font-medium">{cp.high_findings}</td>
                                    <td className="px-6 py-3 text-gray-600">{cp.next_renewal || '—'}</td>
                                    <td className="px-6 py-3">
                                        <TierBadge tier={cp.risk_tier} />
                                    </td>
                                </tr>
                            ))}
                            {counterparties.length === 0 && (
                                <tr>
                                    <td colSpan={8} className="px-6 py-12 text-center text-gray-400">
                                        No counterparty data yet. Upload contracts to see aggregation.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </motion.div>

            {/* Selected detail panel */}
            {selectedCp && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
                >
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">{selectedCp.name}</h3>
                        <button
                            onClick={() => setSelected(null)}
                            className="text-sm text-gray-500 hover:text-gray-700"
                        >
                            Close
                        </button>
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                        <DetailItem label="Active Contracts" value={selectedCp.active_count} />
                        <DetailItem label="Total Value" value={`₹${(selectedCp.total_value_inr / 1e5).toFixed(1)}L`} />
                        <DetailItem label="Critical Findings" value={selectedCp.critical_findings} highlight={selectedCp.critical_findings > 0} />
                        <DetailItem label="High Findings" value={selectedCp.high_findings} highlight={selectedCp.high_findings > 0} />
                    </div>
                </motion.div>
            )}
        </div>
    )
}

function KpiCard({ icon, label, value, sub, trend }: any) {
    return (
        <motion.div
            whileHover={{ y: -2 }}
            className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
                {trend && (
                    trend === 'up'
                        ? <ArrowUpRight size={18} className="text-red-500" />
                        : <ArrowDownRight size={18} className="text-green-500" />
                )}
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{label}</div>
            <div className="text-xs text-gray-400 mt-1">{sub}</div>
        </motion.div>
    )
}

function RiskBadge({ score, tier }: { score: number; tier: string }) {
    const color = tier === 'high' ? 'text-red-600 bg-red-50' : tier === 'medium' ? 'text-amber-600 bg-amber-50' : 'text-green-600 bg-green-50'
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${color}`}>
            {(score * 100).toFixed(0)}%
        </span>
    )
}

function TierBadge({ tier }: { tier: string }) {
    const colors = {
        high: 'bg-red-100 text-red-700 border-red-200',
        medium: 'bg-amber-100 text-amber-700 border-amber-200',
        low: 'bg-green-100 text-green-700 border-green-200',
    }
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors[tier as keyof typeof colors] || 'bg-gray-100 text-gray-700'}`}>
            {tier.charAt(0).toUpperCase() + tier.slice(1)}
        </span>
    )
}

function DetailItem({ label, value, highlight }: { label: string; value: any; highlight?: boolean }) {
    return (
        <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">{label}</div>
            <div className={`text-lg font-semibold ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</div>
        </div>
    )
}
