import { useState } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import {
    LayoutDashboard, FileText, ShieldAlert, Bell, Share2,
    Settings, ChevronLeft, ChevronRight, AlertTriangle,
    CheckCircle, BarChart3, Building2, Fingerprint, Search
} from 'lucide-react'
import DashboardPage from './pages/Dashboard'
import ContractsPage from './pages/Contracts'
import ContractDetailPage from './pages/ContractDetail'
import RiskPage from './pages/Risk'
import RegulatoryPage from './pages/Regulatory'
import GraphPage from './pages/Graph'
import PlaybookPage from './pages/Playbook'
import ObligationsPage from './pages/Obligations'
import TemplatesPage from './pages/Templates'
import AuditPage from './pages/Audit'
import CalendarPage from './pages/Calendar'
import AnalyticsPage from './pages/Analytics'
import SettingsPage from './pages/Settings'
import CounterpartyPage from './pages/Counterparty'
import FingerprintPage from './pages/Fingerprint'
import PortfolioSearchPage from './pages/PortfolioSearch'
import { apiFetch } from "./lib/api"
import NotificationBell from './components/NotificationBell'
import { useOrganization } from './hooks/useQueries'

const pageVariants = {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 }
}

const pageTransition = {
    type: 'spring' as const,
    stiffness: 300,
    damping: 30
}

function AnimatedPage({ children }: { children: React.ReactNode }) {
    return (
        <motion.div
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            transition={pageTransition}
            className="h-full"
        >
            {children}
        </motion.div>
    )
}

function Sidebar({ collapsed, setCollapsed, orgName }: { collapsed: boolean; setCollapsed: (v: boolean) => void; orgName: string }) {
    const location = useLocation()

    const navSections = [
        {
            items: [
                { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
                { path: '/contracts', icon: FileText, label: 'Contracts' },
                { path: '/risk', icon: ShieldAlert, label: 'Risk' },
                { path: '/playbook', icon: BarChart3, label: 'Playbook' },
                { path: '/regulatory', icon: Bell, label: 'Regulatory' },
                { path: '/obligations', icon: AlertTriangle, label: 'Obligations' },
                { path: '/calendar', icon: CheckCircle, label: 'Calendar' },
            ]
        },
        {
            items: [
                { path: '/templates', icon: FileText, label: 'Templates' },
                { path: '/counterparty', icon: Building2, label: 'Counterparties' },
                { path: '/fingerprint', icon: Fingerprint, label: 'Fingerprint' },
                { path: '/search', icon: Search, label: 'Portfolio Search' },
            ]
        },
        {
            items: [
                { path: '/graph', icon: Share2, label: 'Knowledge Graph' },
                { path: '/analytics', icon: BarChart3, label: 'Analytics' },
                { path: '/audit', icon: BarChart3, label: 'Audit Logs' },
                { path: '/settings', icon: Settings, label: 'Settings' },
            ]
        },
    ]

    return (
        <motion.aside
            initial={false}
            animate={{ width: collapsed ? 64 : 256 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="bg-primary text-white flex flex-col h-screen relative z-20"
        >
            {/* Glass header */}
            <div className="h-16 flex items-center px-4 border-b border-white/10 backdrop-blur-sm bg-primary/90">
                <motion.div
                    initial={false}
                    animate={{ opacity: collapsed ? 0 : 1, scale: collapsed ? 0.8 : 1 }}
                    className="overflow-hidden"
                >
                    {!collapsed && (
                        <span className="text-xl font-bold tracking-wider whitespace-nowrap">REXI</span>
                    )}
                </motion.div>
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="ml-auto p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                >
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>
            <nav className="flex-1 py-4 overflow-y-auto">
                {navSections.map((section, secIdx) => (
                    <div key={secIdx} className={secIdx > 0 ? 'mt-3 pt-3 border-t border-white/10' : ''}>
                        {section.items.map((item) => {
                            const isActive = location.pathname === item.path
                            return (
                                <Link key={item.path} to={item.path}>
                                    <motion.div
                                        whileHover={{ x: collapsed ? 0 : 4 }}
                                        whileTap={{ scale: 0.98 }}
                                        className={`flex items-center mx-2 rounded-lg transition-colors relative ${
                                            isActive ? 'bg-white/15' : 'hover:bg-white/10'
                                        } ${collapsed ? 'justify-center py-3' : 'px-4 py-2.5'}`}
                                    >
                                        {isActive && (
                                            <motion.div
                                                layoutId="sidebar-active"
                                                className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent rounded-r-full"
                                                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                            />
                                        )}
                                        <item.icon size={20} />
                                        <motion.span
                                            initial={false}
                                            animate={{
                                                opacity: collapsed ? 0 : 1,
                                                width: collapsed ? 0 : 'auto',
                                                marginLeft: collapsed ? 0 : 12
                                            }}
                                            className="text-sm whitespace-nowrap overflow-hidden"
                                        >
                                            {item.label}
                                        </motion.span>
                                    </motion.div>
                                </Link>
                            )
                        })}
                    </div>
                ))}
            </nav>
            {/* Footer */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-center gap-3">
                    <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-xs font-bold border border-accent/30"
                    >
                        A
                    </motion.div>
                    <motion.div
                        initial={false}
                        animate={{
                            opacity: collapsed ? 0 : 1,
                            width: collapsed ? 0 : 'auto'
                        }}
                        className="overflow-hidden"
                    >
                        {!collapsed && (
                            <div className="text-sm whitespace-nowrap">
                                <p className="font-medium">{orgName || 'Your Organization'}</p>
                                <p className="text-xs text-white/50">{orgName ? 'Active' : 'Demo Mode'}</p>
                            </div>
                        )}
                    </motion.div>
                </div>
            </div>
        </motion.aside>
    )
}

export default function App() {
    const [collapsed, setCollapsed] = useState(false)
    const location = useLocation()
    const { data: orgData } = useOrganization()

    return (
        <div className="flex h-screen bg-page">
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} orgName={orgData?.name} />
            <main className="flex-1 overflow-auto relative">
                {/* Demo Mode Banner */}
                <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-center">
                    <p className="text-xs text-amber-700 font-medium">
                        🔒 Demo Mode — Authentication & multi-tenant features coming in Q3
                    </p>
                </div>
                {/* Top bar */}
                <div className="absolute top-0 right-0 z-30 p-4">
                    <NotificationBell />
                </div>
                {/* Toast provider */}
                <Toaster
                    position="top-right"
                    toastOptions={{
                        duration: 4000,
                        style: {
                            background: '#fff',
                            border: '1px solid #E5E7EB',
                            borderRadius: '12px',
                            padding: '12px 16px',
                            fontSize: '14px',
                            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.15)',
                        },
                        success: {
                            iconTheme: { primary: '#22C55E', secondary: '#fff' },
                        },
                        error: {
                            iconTheme: { primary: '#EF4444', secondary: '#fff' },
                            duration: 5000,
                        },
                    }}
                />
                <AnimatePresence mode="wait">
                    <Routes location={location} key={location.pathname}>
                        <Route path="/" element={<AnimatedPage><DashboardPage /></AnimatedPage>} />
                        <Route path="/contracts" element={<AnimatedPage><ContractsPage /></AnimatedPage>} />
                        <Route path="/contracts/:id" element={<AnimatedPage><ContractDetailPage /></AnimatedPage>} />
                        <Route path="/risk" element={<AnimatedPage><RiskPage /></AnimatedPage>} />
                        <Route path="/playbook" element={<AnimatedPage><PlaybookPage /></AnimatedPage>} />
                        <Route path="/regulatory" element={<AnimatedPage><RegulatoryPage /></AnimatedPage>} />
                        <Route path="/obligations" element={<AnimatedPage><ObligationsPage /></AnimatedPage>} />
                        <Route path="/calendar" element={<AnimatedPage><CalendarPage /></AnimatedPage>} />
                        <Route path="/templates" element={<AnimatedPage><TemplatesPage /></AnimatedPage>} />
                        <Route path="/analytics" element={<AnimatedPage><AnalyticsPage /></AnimatedPage>} />
                        <Route path="/graph" element={<AnimatedPage><GraphPage /></AnimatedPage>} />
                        <Route path="/audit" element={<AnimatedPage><AuditPage /></AnimatedPage>} />
                        <Route path="/counterparty" element={<AnimatedPage><CounterpartyPage /></AnimatedPage>} />
                        <Route path="/fingerprint" element={<AnimatedPage><FingerprintPage /></AnimatedPage>} />
                        <Route path="/search" element={<AnimatedPage><PortfolioSearchPage /></AnimatedPage>} />
                        <Route path="/settings" element={<AnimatedPage><SettingsPage /></AnimatedPage>} />
                    </Routes>
                </AnimatePresence>
            </main>
        </div>
    )
}
