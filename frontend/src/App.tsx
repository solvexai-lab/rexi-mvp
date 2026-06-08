import { useState } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import {
    LayoutDashboard, FileText, ShieldAlert, Bell, Share2,
    Settings, ChevronLeft, ChevronRight, AlertTriangle,
    CheckCircle, BarChart3, Building2, Fingerprint, Search,
    Menu, X
} from 'lucide-react'
import DashboardPage from './pages/Dashboard'
import ContractsPage from './pages/Contracts'
import ContractDetailPage from './pages/ContractDetail'
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
import NotFoundPage from './pages/NotFound'
import NotificationBell from './components/NotificationBell'
import { useOrganization } from './hooks/useQueries'

function AnimatedPage({ children }: { children: React.ReactNode }) {
    return <div className="h-full">{children}</div>
}

function Sidebar({ collapsed, setCollapsed, orgName, mobileOpen, setMobileOpen }: { collapsed: boolean; setCollapsed: (v: boolean) => void; orgName: string; mobileOpen: boolean; setMobileOpen: (v: boolean) => void }) {
    const location = useLocation()

    const navSections = [
        {
            label: 'OPERATE',
            items: [
                { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
                { path: '/contracts', icon: FileText, label: 'Contracts' },
                { path: '/obligations', icon: AlertTriangle, label: 'Obligations' },
                { path: '/calendar', icon: CheckCircle, label: 'Calendar' },
            ]
        },
        {
            label: 'GOVERN',
            items: [
                { path: '/playbook', icon: BarChart3, label: 'Playbook' },
                { path: '/regulatory', icon: Bell, label: 'Regulatory' },
                { path: '/graph', icon: Share2, label: 'Impact Analysis' },
                { path: '/analytics', icon: BarChart3, label: 'Analytics' },
            ]
        },
        {
            label: 'SYSTEM',
            items: [
                { path: '/templates', icon: FileText, label: 'Templates' },
                { path: '/counterparty', icon: Building2, label: 'Counterparties' },
                { path: '/audit', icon: ShieldAlert, label: 'Audit Logs' },
                { path: '/settings', icon: Settings, label: 'Settings' },
            ]
        },
    ]

    const sidebarContent = (
        <>
            {/* Mobile header */}
            <div className="md:hidden h-16 flex items-center justify-between px-4 border-b border-white/10">
                <span className="text-xl font-bold tracking-wider">REXI</span>
                <button onClick={() => setMobileOpen(false)} className="p-2 hover:bg-white/10 rounded-lg">
                    <X size={20} />
                </button>
            </div>
            {/* Desktop header */}
            <div className="hidden md:flex h-16 items-center px-4 border-b border-white/10 backdrop-blur-sm bg-primary/90">
                <div className={`overflow-hidden transition-opacity duration-200 ${collapsed ? 'opacity-0' : 'opacity-100'}`}>
                    {!collapsed && (
                        <span className="text-xl font-bold tracking-wider whitespace-nowrap">REXI</span>
                    )}
                </div>
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="ml-auto p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                >
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>
            <nav className="flex-1 py-4 overflow-y-auto">
                {navSections.map((section, secIdx) => (
                    <div key={secIdx} className={secIdx > 0 ? 'mt-2 pt-2 border-t border-white/10' : ''}>
                        {!collapsed && section.label && (
                            <p className="px-4 pt-2 pb-1 text-[10px] font-bold uppercase tracking-widest text-white/40">
                                {section.label}
                            </p>
                        )}
                        {section.items.map((item) => {
                            const isActive = location.pathname === item.path
                            return (
                                <Link key={item.path} to={item.path} onClick={() => setMobileOpen(false)}>
                                    <div
                                        className={`flex items-center mx-2 rounded-lg transition-colors relative ${
                                            isActive ? 'bg-white/15' : 'hover:bg-white/10'
                                        } ${collapsed ? 'justify-center py-3' : 'px-4 py-2.5'}`}
                                    >
                                        {isActive && (
                                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent rounded-r-full" />
                                        )}
                                        <item.icon size={20} />
                                        <span className={`text-sm whitespace-nowrap overflow-hidden transition-all duration-200 ${collapsed ? 'w-0 opacity-0 ml-0' : 'w-auto opacity-100 ml-3'}`}>
                                            {item.label}
                                        </span>
                                    </div>
                                </Link>
                            )
                        })}
                    </div>
                ))}
            </nav>
            {/* Footer */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-xs font-bold border border-accent/30">
                        A
                    </div>
                    <div className={`overflow-hidden transition-all duration-200 ${collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
                        {!collapsed && (
                            <div className="text-sm whitespace-nowrap">
                                <p className="font-medium">{orgName || 'Your Organization'}</p>
                                <p className="text-xs text-white/50">{orgName ? 'Active' : 'Demo Mode'}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )

    return (
        <>
            {/* Mobile overlay */}
            {mobileOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
                    <aside className="absolute left-0 top-0 h-full w-64 bg-primary text-white flex flex-col z-50 shadow-2xl">
                        {sidebarContent}
                    </aside>
                </div>
            )}
            {/* Desktop sidebar */}
            <aside
                className="hidden md:flex bg-primary text-white flex-col h-screen relative z-20 transition-all duration-200"
                style={{ width: collapsed ? 64 : 256 }}
            >
                {sidebarContent}
            </aside>
        </>
    )
}

export default function App() {
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const location = useLocation()
    const { data: orgData } = useOrganization()

    return (
        <div className="flex h-screen bg-page">
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} orgName={orgData?.name} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
            <main className="flex-1 overflow-auto relative">
                {/* Mobile header bar */}
                <div className="md:hidden h-12 flex items-center justify-between px-4 border-b border-gray-200 bg-white sticky top-0 z-10">
                    <button onClick={() => setMobileOpen(true)} className="p-2 hover:bg-gray-100 rounded-lg">
                        <Menu size={20} />
                    </button>
                    <span className="font-bold text-lg tracking-wider text-primary">REXI</span>
                    <div className="w-8" />{/* spacer */}
                </div>
                {/* Demo notice — subtle footer-style */}
                <div className="bg-gray-50 border-b border-gray-100 px-4 py-1 text-center">
                    <p className="text-[10px] text-gray-400 tracking-wide">
                        Demo environment — no login required
                    </p>
                </div>
                {/* Top bar */}
                <div className="absolute top-0 right-0 z-30 p-4 hidden md:block">
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
                            duration: Infinity,
                        },
                    }}
                />
                <AnimatePresence mode="wait">
                    <Routes location={location} key={location.pathname}>
                        <Route path="/" element={<AnimatedPage><DashboardPage /></AnimatedPage>} />
                        <Route path="/contracts" element={<AnimatedPage><ContractsPage /></AnimatedPage>} />
                        <Route path="/contracts/:id" element={<AnimatedPage><ContractDetailPage /></AnimatedPage>} />
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
                        <Route path="*" element={<AnimatedPage><NotFoundPage /></AnimatedPage>} />
                    </Routes>
                </AnimatePresence>
            </main>
        </div>
    )
}
