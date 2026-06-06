import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Save, Building2, Users, Shield } from 'lucide-react'
import { useOrganization, useUpdateOrganization } from '../hooks/useQueries'

export default function SettingsPage() {
    const { data: orgData, isLoading, error } = useOrganization()
    const updateOrg = useUpdateOrganization()
    const [org, setOrg] = useState<any>(null)
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        if (orgData) setOrg(orgData)
    }, [orgData])

    const handleSave = () => {
        if (!org) return
        updateOrg.mutate(org)
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    if (isLoading) {
        return (
            <div className="p-8 max-w-4xl">
                <div className="h-8 w-48 bg-gray-200 rounded mb-6 animate-pulse" />
                <div className="space-y-4">
                    <div className="h-40 bg-gray-100 rounded-xl animate-pulse" />
                    <div className="h-32 bg-gray-100 rounded-xl animate-pulse" />
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8 max-w-4xl">
                <h1 className="text-2xl font-bold mb-6">Organization Settings</h1>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
                    <p className="font-medium">Failed to load organization settings</p>
                    <p className="text-sm mt-1">{(error as any)?.message || 'Unknown error'}</p>
                </div>
            </div>
        )
    }

    return (
        <div className="p-8 max-w-4xl">
            <motion.h1
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold mb-6"
            >Organization Settings</motion.h1>

            <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-white rounded-xl border border-border p-6 mb-6"
            >
                <div className="flex items-center gap-3 mb-4">
                    <Building2 size={20} className="text-primary" />
                    <h2 className="font-semibold">Company Profile</h2>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">Company Name</label>
                        <input value={org.name || ''} onChange={e => setOrg({...org, name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">Industry</label>
                        <select value={org.industry || 'manufacturing'} onChange={e => setOrg({...org, industry: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm">
                            {['manufacturing', 'saas', 'healthcare', 'fintech', 'retail', 'logistics'].map(i => <option key={i} value={i}>{i}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">Revenue Range</label>
                        <select value={org.revenue_range || '100-300cr'} onChange={e => setOrg({...org, revenue_range: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm">
                            {['50-100cr', '100-300cr', '300-500cr'].map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">Employee Count</label>
                        <input type="number" value={org.employee_count || 0} onChange={e => setOrg({...org, employee_count: parseInt(e.target.value)})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                    <div className="col-span-2">
                        <label className="text-xs text-primary-lighter uppercase font-medium">Registered Address</label>
                        <input value={org.address || ''} onChange={e => setOrg({...org, address: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">GSTIN</label>
                        <input value={org.gstin || ''} onChange={e => setOrg({...org, gstin: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">CIN</label>
                        <input value={org.cin || ''} onChange={e => setOrg({...org, cin: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-xl border border-border p-6 mb-6"
            >
                <div className="flex items-center gap-3 mb-4">
                    <Shield size={20} className="text-primary" />
                    <h2 className="font-semibold">DPDP Compliance Officer</h2>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">DPO Name</label>
                        <input value={org.dpo_name || ''} onChange={e => setOrg({...org, dpo_name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                    <div>
                        <label className="text-xs text-primary-lighter uppercase font-medium">DPO Email</label>
                        <input value={org.dpo_email || ''} onChange={e => setOrg({...org, dpo_email: e.target.value})} className="w-full mt-1 px-3 py-2 border border-border rounded-lg text-sm" />
                    </div>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-xl border border-border p-6 mb-6"
            >
                <div className="flex items-center gap-3 mb-4">
                    <Users size={20} className="text-primary" />
                    <h2 className="font-semibold">Approval Chain</h2>
                </div>
                <p className="text-sm text-primary-lighter">
                    Approval chains are managed per-contract in the contract detail page.
                </p>
            </motion.div>

            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSave}
                disabled={updateOrg.isPending}
                className="bg-primary text-white px-6 py-2 rounded-lg flex items-center gap-2 hover:bg-primary-light transition-colors disabled:opacity-50"
            >
                <Save size={18} /> {saved ? 'Saved!' : updateOrg.isPending ? 'Saving...' : 'Save Settings'}
            </motion.button>
        </div>
    )
}
