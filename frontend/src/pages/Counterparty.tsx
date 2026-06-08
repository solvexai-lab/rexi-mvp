import { useState } from 'react'
import { motion } from 'framer-motion'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts'
import {
    Building2, FileText, TrendingUp, DollarSign,
} from 'lucide-react'
import { useCounterpartyDashboard } from '../hooks/useQueries'

const PIE_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#6366F1']

export default function CounterpartyPage() {
    const { data, isLoading, error } = useCounterpartyDashboard()
    const [selected, setSelected] = useState<string | null>(null)

    const counterparties = data?.counterparties || []

    const selectedCp = counterparties.find((c: any) => c.name === selected)

    const contractDistribution = [
        { name: '1 Contract', value: counterparties.filter((c: any) => c.contract_count === 1).length },
        { name: '2-5 Contracts', value: counterparties.filter((c: any) => c.contract_count >= 2 && c.contract_count <= 5).length },
        { name: '6+ Contracts', value: counterparties.filter((c: any) => c.contract_count >= 6).length },
    ].filter(d => d.value > 0)

    const totalValue = counterparties.reduce((sum: number, c: any) => sum + (c.total_value_inr || 0), 0)
    const totalContracts = counterparties.reduce((sum: number, c: any) => sum + (c.contract_count || 0), 0)

    if (isLoading) {
        return (
            <div className="p-8 space-y-6">
                <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
                <div className="grid grid-cols-3 gap-4">
                    {[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-200 rounded-xl animate-pulse" />)}
                </div>
                <div className="h-96 bg-gray-200 rounded-xl animate-pulse" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
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
                        Pure SQL aggregation — no AI calls. Exposure and contract density per vendor.
                    </p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
                    <Building2 size={16} />
                    {counterparties.length} counterparties
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-3 gap-4">
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
                    icon={<TrendingUp size={20} className="text-amber-600" />}
                    label="Avg Contracts / Counterparty"
                    value={counterparties.length ? (totalContracts / counterparties.length).toFixed(1) : '0'}
                    sub="Contract density"
                />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-2 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
                >
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Contracts by Counterparty</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={counterparties} layout="vertical" margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                            <XAxis type="number" />
                            <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ borderRadius: 12, border: '1px solid #E5E7EB' }}
                            />
                            <Bar dataKey="contract_count" radius={[0, 4, 4, 0]} fill="#3B82F6" />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
                >
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Contract Distribution</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={contractDistribution}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={4}
                                dataKey="value"
                            >
                                {contractDistribution.map((entry: any, index: number) => (
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
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Active</th>
                                <th className="px-6 py-3 text-left font-medium text-gray-500">Next Renewal</th>
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
                                    <td className="px-6 py-3 text-gray-600">{cp.active_count}</td>
                                    <td className="px-6 py-3 text-gray-600">{cp.next_renewal || '—'}</td>
                                </tr>
                            ))}
                            {counterparties.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
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
                        <DetailItem label="Total Contracts" value={selectedCp.contract_count} />
                        <DetailItem label="Next Renewal" value={selectedCp.next_renewal || '—'} />
                    </div>
                </motion.div>
            )}
        </div>
    )
}

function KpiCard({ icon, label, value, sub }: any) {
    return (
        <motion.div
            whileHover={{ y: -2 }}
            className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{label}</div>
            <div className="text-xs text-gray-400 mt-1">{sub}</div>
        </motion.div>
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
