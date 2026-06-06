import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    CalendarDays, Clock, AlertTriangle, CheckCircle,
    ChevronLeft, ChevronRight, FileText, X
} from 'lucide-react'
import { apiFetch } from "../lib/api"
import { ORG_ID } from "../hooks/useQueries"

interface CalendarEvent {
    id: string
    type: 'renewal' | 'expired' | 'obligation' | 'overdue'
    title: string
    date: string
    contract?: any
    obligation?: any
}

export default function CalendarPage() {
    const [contracts, setContracts] = useState<any[]>([])
    const [obligations, setObligations] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [currentMonth, setCurrentMonth] = useState(new Date())
    const [selectedDate, setSelectedDate] = useState<string | null>(null)

    useEffect(() => {
        Promise.all([
            apiFetch(`/contracts?org_id=${ORG_ID}`).then(r => r.json()),
            apiFetch(`/obligations?org_id=${ORG_ID}`).then(r => r.json()),
        ])
        .then(([c, o]) => {
            setContracts(c || [])
            setObligations(o || [])
            setLoading(false)
        })
        .catch((e: any) => {
            setError(e.message || 'Failed to load calendar data')
            setLoading(false)
        })
    }, [])

    if (error) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Calendar</h1>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
                    <p className="font-medium">Failed to load calendar data</p>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            </div>
        )
    }

    const today = new Date().toISOString().split('T')[0]

    const events: CalendarEvent[] = useMemo(() => {
        const list: CalendarEvent[] = []
        contracts.forEach(c => {
            if (c.end_date) {
                const isPast = c.end_date < today
                const type = isPast ? 'expired' : c.auto_renewal ? 'renewal' : 'expiring'
                if (type !== 'expiring') {
                    list.push({
                        id: `renew-${c.id}`,
                        type,
                        title: c.title,
                        date: c.end_date,
                        contract: c,
                    })
                }
            }
        })
        obligations.forEach(o => {
            if (o.due_date) {
                const isOverdue = o.due_date < today && o.status !== 'completed'
                list.push({
                    id: `ob-${o.id}`,
                    type: isOverdue ? 'overdue' : 'obligation',
                    title: o.description,
                    date: o.due_date,
                    obligation: o,
                })
            }
        })
        return list
    }, [contracts, obligations, today])

    const stats = useMemo(() => ({
        renewals: contracts.filter(c => c.end_date && c.end_date >= today && c.auto_renewal).length,
        expired: contracts.filter(c => c.end_date && c.end_date < today).length,
        pending: obligations.filter(o => o.status === 'pending' && o.due_date).length,
        overdue: obligations.filter(o => o.due_date && o.due_date < today && o.status !== 'completed').length,
    }), [contracts, obligations, today])

    // Calendar grid generation
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startOffset = firstDay.getDay() // 0 = Sunday

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December']
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    const days: { date: string; events: CalendarEvent[]; isToday: boolean }[] = []
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
        days.push({
            date: dateStr,
            events: events.filter(e => e.date === dateStr),
            isToday: dateStr === today,
        })
    }

    const selectedEvents = selectedDate ? events.filter(e => e.date === selectedDate) : []

    const eventDot = (type: string) => {
        const colors: Record<string, string> = {
            renewal: 'bg-blue-500',
            expired: 'bg-red-500',
            overdue: 'bg-orange-500',
            obligation: 'bg-green-500',
        }
        return <span className={`w-1.5 h-1.5 rounded-full ${colors[type] || 'bg-gray-400'}`} />
    }

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-6">Calendar & Renewals</h1>
                <div className="grid grid-cols-4 gap-6 mb-8">
                    {[1,2,3,4].map(i => <div key={i} className="bg-white rounded-xl border border-border p-6 h-28 animate-pulse" />)}
                </div>
                <div className="bg-white rounded-xl border border-border p-6 h-96 animate-pulse" />
            </div>
        )
    }

    return (
        <div className="p-8">
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between mb-6"
            >
                <h1 className="text-2xl font-bold">Calendar & Renewals</h1>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setCurrentMonth(new Date(year, month - 1, 1))}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronLeft size={20} />
                    </button>
                    <span className="text-lg font-semibold min-w-[160px] text-center">
                        {monthNames[month]} {year}
                    </span>
                    <button
                        onClick={() => setCurrentMonth(new Date(year, month + 1, 1))}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-6 mb-8">
                <StatCard icon={<Clock size={20} className="text-blue-600" />} label="Upcoming Renewals" value={stats.renewals} color="text-blue-600" />
                <StatCard icon={<AlertTriangle size={20} className="text-red-600" />} label="Expired Contracts" value={stats.expired} color="text-red-600" />
                <StatCard icon={<CheckCircle size={20} className="text-yellow-600" />} label="Pending Obligations" value={stats.pending} color="text-yellow-600" />
                <StatCard icon={<AlertTriangle size={20} className="text-orange-600" />} label="Overdue" value={stats.overdue} color="text-orange-600" />
            </div>

            <div className="flex gap-6">
                {/* Calendar Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex-1 bg-white rounded-xl border border-border p-6"
                >
                    {/* Day headers */}
                    <div className="grid grid-cols-7 gap-1 mb-2">
                        {dayNames.map(d => (
                            <div key={d} className="text-center text-xs font-medium text-gray-400 py-2">{d}</div>
                        ))}
                    </div>
                    {/* Days */}
                    <div className="grid grid-cols-7 gap-1">
                        {/* Empty cells for offset */}
                        {Array.from({ length: startOffset }).map((_, i) => (
                            <div key={`empty-${i}`} className="h-24 rounded-lg" />
                        ))}
                        {days.map(day => (
                            <button
                                key={day.date}
                                onClick={() => setSelectedDate(day.date === selectedDate ? null : day.date)}
                                className={`h-24 rounded-lg border p-2 text-left transition-all hover:shadow-md ${
                                    day.isToday ? 'border-blue-300 bg-blue-50' :
                                    selectedDate === day.date ? 'border-primary bg-primary/5' :
                                    'border-gray-100 hover:border-gray-200'
                                }`}
                            >
                                <span className={`text-sm font-medium ${day.isToday ? 'text-blue-600' : 'text-gray-700'}`}>
                                    {parseInt(day.date.split('-')[2])}
                                </span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                    {day.events.slice(0, 4).map((e, i) => (
                                        <span key={i}>{eventDot(e.type)}</span>
                                    ))}
                                    {day.events.length > 4 && (
                                        <span className="text-[10px] text-gray-400">+{day.events.length - 4}</span>
                                    )}
                                </div>
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* Selected day sidebar */}
                <AnimatePresence>
                    {selectedDate && (
                        <motion.div
                            initial={{ opacity: 0, x: 20, width: 0 }}
                            animate={{ opacity: 1, x: 0, width: 320 }}
                            exit={{ opacity: 0, x: 20, width: 0 }}
                            className="bg-white rounded-xl border border-border p-5 overflow-hidden shrink-0"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold">{selectedDate}</h3>
                                <button onClick={() => setSelectedDate(null)} className="p-1 hover:bg-gray-100 rounded">
                                    <X size={16} />
                                </button>
                            </div>
                            <div className="space-y-3">
                                {selectedEvents.length === 0 && (
                                    <p className="text-sm text-gray-400">No events on this day.</p>
                                )}
                                {selectedEvents.map(e => (
                                    <div key={e.id} className={`p-3 rounded-lg border-l-4 ${
                                        e.type === 'renewal' ? 'bg-blue-50 border-blue-500' :
                                        e.type === 'expired' ? 'bg-red-50 border-red-500' :
                                        e.type === 'overdue' ? 'bg-orange-50 border-orange-500' :
                                        'bg-green-50 border-green-500'
                                    }`}>
                                        <div className="flex items-center gap-2 mb-1">
                                            {e.type === 'renewal' && <Clock size={14} className="text-blue-600" />}
                                            {e.type === 'expired' && <AlertTriangle size={14} className="text-red-600" />}
                                            {e.type === 'overdue' && <AlertTriangle size={14} className="text-orange-600" />}
                                            {e.type === 'obligation' && <CheckCircle size={14} className="text-green-600" />}
                                            <span className="text-xs font-medium uppercase text-gray-500">{e.type}</span>
                                        </div>
                                        <p className="text-sm font-medium">{e.title}</p>
                                        {e.contract && (
                                            <p className="text-xs text-gray-500 mt-1">{e.contract.counterparty_name} · ₹{(e.contract.value_inr / 1e5).toFixed(1)}L</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}

function StatCard({ icon, label, value, color }: any) {
    return (
        <motion.div
            whileHover={{ y: -2 }}
            className="bg-white rounded-xl border border-border p-6 text-center"
        >
            <div className="mx-auto mb-2 w-fit p-2 bg-gray-50 rounded-lg">{icon}</div>
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
        </motion.div>
    )
}
