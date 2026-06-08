import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { BarChart3, FileText, CheckCircle } from 'lucide-react'
import { useContracts, useAnalyticsSummary } from '../hooks/useQueries'

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
    const { data: summary, isLoading: sLoading } = useAnalyticsSummary()

    const loading = cLoading || sLoading

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Analytics</h1>
                <div className="grid grid-cols-3 gap-6 mb-8">
                    {[1,2,3].map(i => <SkeletonCard key={i} />)}
                </div>
                <div className="grid grid-cols-2 gap-6">
                    <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
                    <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
                </div>
            </div>
        )
    }

    const contractsList = contracts || []

    // Contract status distribution
    const statusCounts: Record<string, number> = {}
    contractsList.forEach((c: any) => {
        statusCounts[c.status] = (statusCounts[c.status] || 0) + 1
    })
    const statusData = Object.entries(statusCounts).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))

    // Contract type distribution
    const typeCounts: Record<string, number> = {}
    contractsList.forEach((c: any) => {
        typeCounts[c.contract_type] = (typeCounts[c.contract_type] || 0) + 1
    })
    const typeData = Object.entries(typeCounts).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))

    const processedCount = contractsList.filter((c: any) => c.status !== 'processing').length
    const completionRate = contractsList.length > 0 ? Math.round((processedCount / contractsList.length) * 100) : 0

    return (
        <div className="p-8">
            <motion.h1
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold mb-6"
            >Analytics</motion.h1>

            <div className="grid grid-cols-3 gap-6 mb-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <FileText size={20} className="mx-auto mb-2 text-blue-600" />
                    <p className="text-sm text-gray-500">Total Contracts</p>
                    <p className="text-2xl font-bold">{contractsList.length}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <CheckCircle size={20} className="mx-auto mb-2 text-green-600" />
                    <p className="text-sm text-gray-500">Processed</p>
                    <p className="text-2xl font-bold">{processedCount}</p>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-xl border border-border p-6 text-center"
                >
                    <BarChart3 size={20} className="mx-auto mb-2 text-purple-600" />
                    <p className="text-sm text-gray-500">Completion Rate</p>
                    <p className="text-2xl font-bold">{completionRate}%</p>
                </motion.div>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-6">
                <motion.div
                    initial={{ opacity: 0, x: -15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
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
                    initial={{ opacity: 0, x: 15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.35 }}
                    className="bg-white rounded-xl border border-border p-6"
                >
                    <h3 className="font-semibold mb-4">Contract Types</h3>
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
        </div>
    )
}
