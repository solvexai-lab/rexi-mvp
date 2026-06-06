import { useState, useEffect } from 'react'
import { Bell, Check, Loader2 } from 'lucide-react'
import { apiFetch } from '../lib/api'
import { ORG_ID } from "../hooks/useQueries"

interface Notification {
    id: string
    title: string
    message: string
    is_read: boolean
    created_at: string
}

export default function NotificationBell() {
    const [open, setOpen] = useState(false)
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [unreadCount, setUnreadCount] = useState(0)
    const [loading, setLoading] = useState(false)

    const load = async () => {
        setLoading(true)
        try {
            const [nRes, uRes] = await Promise.all([
                apiFetch(`/notifications?org_id=${ORG_ID}`),
                apiFetch(`/notifications/unread-count?org_id=${ORG_ID}`),
            ])
            if (nRes.ok) setNotifications(await nRes.json())
            if (uRes.ok) setUnreadCount((await uRes.json()).count || 0)
        } catch {}
        setLoading(false)
    }

    useEffect(() => {
        load()
        const interval = setInterval(load, 30000)
        return () => clearInterval(interval)
    }, [])

    const markRead = async (id: string) => {
        try {
            await apiFetch(`/notifications/${id}/read`, { method: 'PUT' })
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
            setUnreadCount(c => Math.max(0, c - 1))
        } catch {}
    }

    const markAllRead = async () => {
        try {
            await apiFetch(`/notifications/read-all?org_id=${ORG_ID}`, { method: 'PUT' })
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
            setUnreadCount(0)
        } catch {}
    }

    return (
        <div className="relative">
            <button
                onClick={() => { setOpen(!open); if (!open) load() }}
                className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
                <Bell size={20} className="text-gray-600" />
                {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {open && (
                <>
                    <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                    <div className="absolute right-0 top-10 w-80 bg-white rounded-xl border border-gray-200 shadow-xl z-50 overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                            <h3 className="font-semibold text-sm">Notifications</h3>
                            {unreadCount > 0 && (
                                <button onClick={markAllRead} className="text-xs text-blue-600 hover:text-blue-700">
                                    Mark all read
                                </button>
                            )}
                        </div>
                        <div className="max-h-80 overflow-y-auto">
                            {loading && notifications.length === 0 ? (
                                <div className="p-8 text-center">
                                    <Loader2 size={20} className="animate-spin mx-auto text-gray-400" />
                                </div>
                            ) : notifications.length === 0 ? (
                                <div className="p-8 text-center text-sm text-gray-400">
                                    No notifications
                                </div>
                            ) : (
                                notifications.slice(0, 20).map(n => (
                                    <div
                                        key={n.id}
                                        className={`px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                                            !n.is_read ? 'bg-blue-50/50' : ''
                                        }`}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-800 truncate">{n.title}</p>
                                                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                                                <p className="text-[10px] text-gray-400 mt-1">
                                                    {new Date(n.created_at).toLocaleString()}
                                                </p>
                                            </div>
                                            {!n.is_read && (
                                                <button
                                                    onClick={() => markRead(n.id)}
                                                    className="p-1 hover:bg-blue-100 rounded text-blue-600"
                                                    title="Mark as read"
                                                >
                                                    <Check size={14} />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
