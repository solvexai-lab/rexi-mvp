import { useState } from 'react'
import { Shield, Eye, EyeOff, Copy, CheckCircle, AlertTriangle, Lock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface PIIFinding {
    entity_type: string
    text: string
    score: number
    description: string
}

const ENTITY_COLORS: Record<string, string> = {
    AADHAAR: 'bg-amber-100 text-amber-800 border-amber-200',
    PAN: 'bg-blue-100 text-blue-800 border-blue-200',
    GSTIN: 'bg-purple-100 text-purple-800 border-purple-200',
    EMAIL: 'bg-green-100 text-green-800 border-green-200',
    INDIAN_PHONE: 'bg-red-100 text-red-800 border-red-200',
    UPI: 'bg-teal-100 text-teal-800 border-teal-200',
    IFSC: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    PASSPORT: 'bg-orange-100 text-orange-800 border-orange-200',
    BANK_ACCOUNT: 'bg-gray-100 text-gray-800 border-gray-200',
    CREDIT_CARD: 'bg-rose-100 text-rose-800 border-rose-200',
    EMAIL_ADDRESS: 'bg-green-100 text-green-800 border-green-200',
}

const ENTITY_ICONS: Record<string, string> = {
    AADHAAR: '🆔',
    PAN: '📇',
    GSTIN: '🏢',
    EMAIL: '📧',
    INDIAN_PHONE: '📱',
    UPI: '💳',
    IFSC: '🏦',
    PASSPORT: '🛂',
    BANK_ACCOUNT: '💰',
    CREDIT_CARD: '💳',
    EMAIL_ADDRESS: '📧',
}

function getEntityStyle(type: string) {
    return ENTITY_COLORS[type] || 'bg-gray-100 text-gray-800 border-gray-200'
}

function getEntityIcon(type: string) {
    return ENTITY_ICONS[type] || '🔒'
}

export default function ContractPII({
    findings,
    has_pii,
    entity_types,
    anonymized_preview,
    loading,
    error,
    onAnonymize,
    anonymizeResult,
    anonymizeLoading,
}: {
    findings: PIIFinding[]
    has_pii: boolean
    entity_types: string[]
    anonymized_preview: string
    loading: boolean
    error: string | null
    onAnonymize: () => void
    anonymizeResult: { anonymized: string; replacements: any[] } | null
    anonymizeLoading: boolean
}) {
    const [showAnonymized, setShowAnonymized] = useState(false)
    const [copied, setCopied] = useState(false)

    if (loading) {
        return (
            <div className="p-8 space-y-4">
                <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="grid grid-cols-2 gap-3">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                    ))}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-8 text-center">
                <Shield className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">{error}</p>
            </div>
        )
    }

    if (!has_pii) {
        return (
            <div className="p-8 text-center">
                <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                <h3 className="text-lg font-semibold text-gray-900">No PII Detected</h3>
                <p className="text-sm text-gray-500 mt-1">
                    This contract appears clean of Indian identifiers and personal data.
                </p>
            </div>
        )
    }

    const displayText = anonymizeResult?.anonymized || anonymized_preview || ''

    return (
        <div className="p-6">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-amber-500" />
                        PII Detection Results
                    </h3>
                    <p className="text-sm text-gray-500">
                        {findings.length} sensitive entities found across {entity_types.length} categories
                    </p>
                </div>
                <button
                    onClick={onAnonymize}
                    disabled={anonymizeLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors disabled:opacity-50"
                >
                    <Lock className="w-4 h-4" />
                    {anonymizeLoading ? 'Anonymizing...' : 'Full Anonymize'}
                </button>
            </div>

            {/* Entity type badges */}
            <div className="flex flex-wrap gap-2 mb-4">
                {entity_types.map((type) => (
                    <span
                        key={type}
                        className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getEntityStyle(type)}`}
                    >
                        <span>{getEntityIcon(type)}</span>
                        {type.replace(/_/g, ' ')}
                    </span>
                ))}
            </div>

            {/* Findings list */}
            <div className="space-y-2 mb-6">
                <AnimatePresence>
                    {findings.map((finding, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className={`flex items-center justify-between p-3 rounded-lg border ${getEntityStyle(finding.entity_type)}`}
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-lg">{getEntityIcon(finding.entity_type)}</span>
                                <div>
                                    <p className="text-sm font-medium">{finding.text}</p>
                                    <p className="text-xs opacity-75">{finding.description}</p>
                                </div>
                            </div>
                            <span className="text-xs font-mono opacity-60">
                                {Math.round(finding.score * 100)}%
                            </span>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Anonymized preview */}
            {displayText && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
                        <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            {showAnonymized ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                            Anonymized Preview
                        </span>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setShowAnonymized(!showAnonymized)}
                                className="text-xs text-primary hover:underline"
                            >
                                {showAnonymized ? 'Hide' : 'Show'}
                            </button>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(displayText)
                                    setCopied(true)
                                    setTimeout(() => setCopied(false), 2000)
                                }}
                                className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                            >
                                {copied ? <CheckCircle className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                                {copied ? 'Copied' : 'Copy'}
                            </button>
                        </div>
                    </div>
                    <AnimatePresence>
                        {showAnonymized && (
                            <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <div className="p-4 text-sm text-gray-600 font-mono bg-gray-50/50 leading-relaxed max-h-64 overflow-y-auto">
                                    {displayText}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}
        </div>
    )
}
