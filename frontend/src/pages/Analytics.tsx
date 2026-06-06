import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { BarChart3, TrendingUp, FileText, ShieldAlert } from 'lucide-react'
import { useContracts, useRiskFindings, useRiskHistory, useAnalyticsSummary } from '../hooks/useQueries'

const COLORS = ['#3B82F6', '#EF4444', '#F59E0B', '#22C55E', '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16']

function SkeletonCard() {
    return <div className="bg-white rounded-xl border border-border p-6 animate-pulse">
        <div className="h-5 w-5 bg-gray-200 rounded mx-auto mb-2" />
        <div className="h-4 w-20 bg-gray-200 rounded mx-auto mb-2" />
        <div className="h-8 w-12 bg-gray-200 rounded mx-auto" />
    </div>
}

export default function AnalyticsPage() {
    const { data: contracts, isLoading: cLoading } = useContracts()
    const { data: findings, isLoading: fLoading } = useRiskFindings()
    const { data: history, isLoading: hLoading } = useRiskHistory()
    const { data: summary, isLoading: sLoading } = useAnalyticsSummary()

    const loading = cLoading || fLoading || hLoading || sLoading

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Analytics</h1>
                <div className="grid grid-cols-4 gap-6 mb-8">
                    {[1,2,3,4].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="grid grid-cols-2 gap-6">
                    <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
                    <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
                </div>
            </div>
        )
    }

    const findingsList = findings || []
    const contractsList = contracts || []

    // Findings by severity
    const severityData = [
        { name: 'Critical', value: findingsList.filter((f: any) => f.severity === 'critical').length },
        { name: 'High', value: findingsList.filter((f: any) => f.severity === 'high').length },
        { name: 'Medium', value: findingsList.filter((f: any) => f.severity === 'medium').length },
        { name: 'Low', value: findingsList.filter((f: any) => f.severity === 'low').length },
    ].filter(d => d.value > 0)

    // Findings by type
    const typeCounts: Record<string, number> = {}
    findingsList.forEach((f: any) => {
        typeCounts[f.finding_type] = (typeCounts[f.finding_type] || 0) + 1
    })
    const typeData = Object.entries(typeCounts).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))

    // Contract status distribution
    const statusCounts: Record<string, number> = {}
    contractsList.forEach((c: any) => {
        statusCounts[c.status] = (statusCounts[c.status] || 0) + 1
    })
    const statusData = Object.entries(statusCounts).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))

    // Real risk history for trend chart
    const trendData = (history || []).map((h: any) => ({
        month: h.date,
        contracts: h.contracts || 0,
        riskScore: h.overall ? Math.round(h.overall * 100) : 0,
    }))

    const avgRisk = summary?.risk?.avg_score || 0
    const complianceRate = findingsList.length > 0
        ? Math.round((findingsList.filter((f: any) => f.is_resolved).length / findingsList.length) * 100)
        : 0

    return (
        <div className="p-8">
            <motion.h1
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold mb-6"
            >Analytics</motion.h1>

            <div className="grid grid-cols-4 gap-6 mb-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <FileText size={20} className="mx-auto mb-2 text-blue-600" />
                    <p className="text-sm text-primary-lighter">Total Contracts</p>
                    <p className="text-2xl font-bold">{contractsList.length}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <ShieldAlert size={20} className="mx-auto mb-2 text-red-600" />
                    <p className="text-sm text-primary-lighter">Open Findings</p>
                    <p className="text-2xl font-bold">{findingsList.filter((f: any) => !f.is_resolved).length}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <TrendingUp size={20} className="mx-auto mb-2 text-green-600" />
                    <p className="text-sm text-primary-lighter">Avg Risk Score</p>
                    <p className="text-2xl font-bold">{avgRisk > 0 ? (avgRisk * 100).toFixed(0) : '0'}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <BarChart3 size={20} className="mx-auto mb-2 text-purple-600" />
                    <p className="text-sm text-primary-lighter">Compliance Rate</p>
                    <p className="text-2xl font-bold">{complianceRate}%</p>
                </motion.div>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-6">
                <motion.div
                    initial={{ opacity: 0, x: -15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Findings by Severity</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie data={severityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                                {severityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, x: 15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.35 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Findings by Type</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={typeData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Contract Status Distribution</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                                {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.45 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Risk Score Trend</h3>
                    {trendData.length > 1 ? (
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis />
                                <Tooltip />
                                <Line type="monotone" dataKey="riskScore" stroke="#EF4444" strokeWidth={2} name="Risk Score" />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[250px] flex items-center justify-center text-sm text-primary-lighter">
                            Upload more contracts to see trends
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    )
}
