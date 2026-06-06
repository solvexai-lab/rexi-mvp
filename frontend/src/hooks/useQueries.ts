import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'
import { showToast } from './useToast'

export const ORG_ID = localStorage.getItem('rexi_org_id') || 'demo-org'

/* ─── Dashboard ─── */
export function useDashboardSummary() {
    return useQuery({
        queryKey: ['dashboard', 'summary'],
        queryFn: async () => {
            const res = await apiFetch(`/analytics/summary?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Contracts ─── */
export function useContracts() {
    return useQuery({
        queryKey: ['contracts'],
        queryFn: async () => {
            const res = await apiFetch(`/contracts?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

export function useContract(id: string | undefined) {
    return useQuery({
        queryKey: ['contract', id],
        queryFn: async () => {
            const res = await apiFetch(`/contracts/${id}`)
            return res.json()
        },
        enabled: !!id,
    })
}

export function useContractStages(id: string | undefined) {
    return useQuery({
        queryKey: ['contract-stages', id],
        queryFn: async () => {
            const res = await apiFetch(`/approvals/contracts/${id}/stages`)
            return res.json()
        },
        enabled: !!id,
    })
}

export function useContractComments(id: string | undefined) {
    return useQuery({
        queryKey: ['contract-comments', id],
        queryFn: async () => {
            const res = await apiFetch(`/comments/contracts/${id}`)
            return res.json()
        },
        enabled: !!id,
    })
}

export function useUploadContract() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (formData: FormData) => {
            const res = await apiFetch(`/contracts/upload`, { method: 'POST', body: formData })
            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Upload failed')
            }
            return res.json()
        },
        onSuccess: (data) => {
            showToast(`Uploaded — ${data.clauses_extracted} clauses, risk ${data.risk_score}`, 'success')
            qc.invalidateQueries({ queryKey: ['contracts'] })
            qc.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
            qc.invalidateQueries({ queryKey: ['risk'] })
        },
        onError: (err: any) => showToast(err.message, 'error'),
    })
}

/* ─── Risk ─── */
export function useRiskDashboard() {
    return useQuery({
        queryKey: ['risk', 'dashboard'],
        queryFn: async () => {
            const res = await apiFetch(`/risk/dashboard?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

export function useRiskFindings() {
    return useQuery({
        queryKey: ['risk', 'findings'],
        queryFn: async () => {
            const res = await apiFetch(`/risk/findings?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

export function useRiskHistory() {
    return useQuery({
        queryKey: ['analytics', 'risk-history'],
        queryFn: async () => {
            const res = await apiFetch(`/analytics/risk-history?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

export function useResolveFinding() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (id: string) => {
            const res = await apiFetch(`/risk/findings/${id}/resolve`, { method: 'PUT' })
            if (!res.ok) throw new Error('Failed to resolve')
            return res.json()
        },
        onSuccess: () => {
            showToast('Finding resolved', 'success')
            qc.invalidateQueries({ queryKey: ['risk'] })
            qc.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
        },
        onError: () => showToast('Failed to resolve finding', 'error'),
    })
}

/* ─── Analytics ─── */
export function useAnalyticsSummary() {
    return useQuery({
        queryKey: ['analytics', 'summary'],
        queryFn: async () => {
            const res = await apiFetch(`/analytics/summary?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Settings / Org ─── */
export function useOrganization() {
    return useQuery({
        queryKey: ['organization'],
        queryFn: async () => {
            const res = await apiFetch(`/organizations/${ORG_ID}`)
            if (!res.ok) throw new Error('Failed to load organization')
            return res.json()
        },
    })
}

export function useUpdateOrganization() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: Record<string, any>) => {
            const res = await apiFetch(`/organizations/${ORG_ID}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            if (!res.ok) throw new Error('Failed to save')
            return res.json()
        },
        onSuccess: () => {
            showToast('Settings saved successfully', 'success')
            qc.invalidateQueries({ queryKey: ['organization'] })
        },
        onError: () => showToast('Failed to save settings', 'error'),
    })
}

/* ─── Regulatory ─── */
export function useRegulatoryAlerts() {
    return useQuery({
        queryKey: ['regulatory', 'alerts'],
        queryFn: async () => {
            const res = await apiFetch(`/regulatory/alerts?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Playbook ─── */
export function usePlaybookRules() {
    return useQuery({
        queryKey: ['playbook', 'rules'],
        queryFn: async () => {
            const res = await apiFetch(`/playbook/rules?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Obligations ─── */
export function useObligations() {
    return useQuery({
        queryKey: ['obligations'],
        queryFn: async () => {
            const res = await apiFetch(`/obligations?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Plain English ─── */
export function usePlainEnglish(contractId: string | undefined) {
    return useQuery({
        queryKey: ['plain-english', contractId],
        queryFn: async () => {
            const res = await apiFetch(`/plain-english/contracts/${contractId}`)
            return res.json()
        },
        enabled: !!contractId,
    })
}

export function useGeneratePlainEnglish() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (contractId: string) => {
            const res = await apiFetch(`/plain-english/contracts/${contractId}/generate`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to generate')
            return res.json()
        },
        onSuccess: (_, contractId) => {
            showToast('Plain English summaries generated', 'success')
            qc.invalidateQueries({ queryKey: ['plain-english', contractId] })
        },
        onError: () => showToast('Failed to generate summaries', 'error'),
    })
}

/* ─── Contract Actions ─── */
export function useApproveStage() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ stageId, comment = '' }: { stageId: string; comment?: string }) => {
            const res = await apiFetch(`/approvals/stages/${stageId}/approve?comment=${encodeURIComponent(comment)}`, { method: 'PUT' })
            if (!res.ok) throw new Error('Failed to approve')
            return res.json()
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['contract-stages'] }),
    })
}

export function useRejectStage() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ stageId, comment = '' }: { stageId: string; comment?: string }) => {
            const res = await apiFetch(`/approvals/stages/${stageId}/reject?comment=${encodeURIComponent(comment)}`, { method: 'PUT' })
            if (!res.ok) throw new Error('Failed to reject')
            return res.json()
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['contract-stages'] }),
    })
}

export function useSubmitForApproval() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (contractId: string) => {
            const res = await apiFetch(`/approvals/contracts/${contractId}/submit?org_id=${ORG_ID}`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to submit')
            return res.json()
        },
        onSuccess: (_, contractId) => {
            showToast('Contract submitted for approval', 'success')
            qc.invalidateQueries({ queryKey: ['contract-stages'] })
            qc.invalidateQueries({ queryKey: ['contract', contractId] })
        },
        onError: () => showToast('Failed to submit', 'error'),
    })
}

export function useTransitionContract() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ contractId, newStatus }: { contractId: string; newStatus: string }) => {
            const res = await apiFetch(`/approvals/contracts/${contractId}/transition?new_status=${newStatus}&org_id=${ORG_ID}`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to transition')
            return res.json()
        },
        onSuccess: (_, { contractId }) => {
            showToast('Status updated', 'success')
            qc.invalidateQueries({ queryKey: ['contract', contractId] })
            qc.invalidateQueries({ queryKey: ['contracts'] })
        },
        onError: () => showToast('Failed to update status', 'error'),
    })
}

export function usePostComment() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ contractId, content }: { contractId: string; content: string }) => {
            const res = await apiFetch(`/comments/contracts/${contractId}?content=${encodeURIComponent(content)}&org_id=${ORG_ID}`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to post comment')
            return res.json()
        },
        onSuccess: (_, { contractId }) => qc.invalidateQueries({ queryKey: ['contract-comments', contractId] }),
    })
}

export function useDeleteComment() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ commentId, contractId }: { commentId: string; contractId: string }) => {
            const res = await apiFetch(`/comments/${commentId}`, { method: 'DELETE' })
            if (!res.ok) throw new Error('Failed to delete')
            return res.json()
        },
        onSuccess: (_, { contractId }) => qc.invalidateQueries({ queryKey: ['contract-comments', contractId] }),
    })
}

export function useRedlineCompare() {
    return useMutation({
        mutationFn: async ({ contractId, otherId }: { contractId: string; otherId: string }) => {
            const res = await apiFetch(`/redline/contracts/${contractId}/compare/${otherId}`)
            if (!res.ok) throw new Error('Comparison failed')
            return res.json()
        },
    })
}

export function useDeleteContract() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (contractId: string) => {
            const res = await apiFetch(`/contracts/${contractId}`, { method: 'DELETE' })
            if (!res.ok) throw new Error('Failed to delete')
            return res.json()
        },
        onSuccess: () => {
            showToast('Contract deleted', 'success')
            qc.invalidateQueries({ queryKey: ['contracts'] })
            qc.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
        },
        onError: () => showToast('Failed to delete contract', 'error'),
    })
}

/* ─── Chat ─── */
export function useAskContract() {
    return useMutation({
        mutationFn: async ({ contractId, question }: { contractId: string; question: string }) => {
            const res = await apiFetch(`/chat/contracts/${contractId}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            })
            if (!res.ok) throw new Error('Failed to get answer')
            return res.json()
        },
    })
}

/* ─── Counterparty ─── */
export function useCounterpartyDashboard() {
    return useQuery({
        queryKey: ['counterparty', 'dashboard'],
        queryFn: async () => {
            const res = await apiFetch(`/counterparties/dashboard?org_id=${ORG_ID}`)
            return res.json()
        },
    })
}

/* ─── Contract Versions ─── */
export function useContractVersions(contractId: string | undefined) {
    return useQuery({
        queryKey: ['contract-versions', contractId],
        queryFn: async () => {
            const res = await apiFetch(`/redline/contracts/${contractId}/versions`)
            return res.json()
        },
        enabled: !!contractId,
    })
}

/* ─── Highlights ─── */
export function useHighlights(contractId: string | undefined) {
    return useQuery({
        queryKey: ['highlights', contractId],
        queryFn: async () => {
            const res = await apiFetch(`/highlights/contracts/${contractId}`)
            return res.json()
        },
        enabled: !!contractId,
    })
}

export function useGenerateHighlights() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (contractId: string) => {
            const res = await apiFetch(`/highlights/contracts/${contractId}/generate`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to generate highlights')
            return res.json()
        },
        onSuccess: (_, contractId) => {
            showToast('Highlights generated', 'success')
            qc.invalidateQueries({ queryKey: ['highlights', contractId] })
        },
        onError: () => showToast('Failed to generate highlights', 'error'),
    })
}

/* ─── Redline ─── */
export function useCompareContracts() {
    return useMutation({
        mutationFn: async ({ a, b }: { a: string; b: string }) => {
            const res = await apiFetch(`/redline/contracts/${a}/compare/${b}`)
            if (!res.ok) throw new Error('Failed to compare')
            return res.json()
        },
    })
}

/* ─── Fingerprint / Similarity ─── */
export function useFingerprintAnalyze() {
    return useMutation({
        mutationFn: async ({ threshold = 0.65, contractIds }: { threshold?: number; contractIds?: string[] } = {}) => {
            const res = await apiFetch(`/fingerprint/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ org_id: ORG_ID, threshold, contract_ids: contractIds }),
            })
            if (!res.ok) throw new Error('Analysis failed')
            return res.json()
        },
    })
}

export function useContractFingerprint(contractId: string | undefined) {
    return useQuery({
        queryKey: ['fingerprint', contractId],
        queryFn: async () => {
            const res = await apiFetch(`/fingerprint/contracts/${contractId}/compare?org_id=${ORG_ID}`)
            return res.json()
        },
        enabled: !!contractId,
    })
}

/* ─── Portfolio Search (Embeddings) ─── */
export function usePortfolioSearch() {
    return useMutation({
        mutationFn: async ({ query, topK = 5 }: { query: string; topK?: number }) => {
            const res = await apiFetch(`/embeddings/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, top_k: topK }),
            })
            if (!res.ok) throw new Error('Search failed')
            return res.json()
        },
    })
}

/* ─── 3-Pillar Knowledge Graph ─── */
export function useGraphPillars(pillar: 'playbook' | 'statutes' | 'regulations') {
    return useQuery({
        queryKey: ['graph', 'pillars', pillar],
        queryFn: async () => {
            const res = await apiFetch(`/graph/pillars/${pillar}?org_id=${ORG_ID}`)
            if (!res.ok) throw new Error('Failed to load pillars')
            return res.json()
        },
    })
}

export function useGraphImpact(pillar: 'regulations' | 'playbook' | 'statutes', id: string | undefined) {
    const apiPath = pillar === 'regulations' ? 'regulation' : pillar === 'statutes' ? 'statute' : 'playbook'
    return useQuery({
        queryKey: ['graph', 'impact', pillar, id],
        queryFn: async () => {
            const res = await apiFetch(`/graph/impact/${apiPath}/${id}?org_id=${ORG_ID}`)
            if (!res.ok) throw new Error('Failed to load impact')
            return res.json()
        },
        enabled: !!id,
    })
}

export function useGraphNetwork(pillar: string = 'all') {
    return useQuery({
        queryKey: ['graph', 'network', pillar],
        queryFn: async () => {
            const res = await apiFetch(`/graph/network?org_id=${ORG_ID}&pillar=${pillar}`)
            if (!res.ok) throw new Error('Failed to load network graph')
            return res.json()
        },
    })
}

export function useRescanPlaybook() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async () => {
            const res = await apiFetch(`/graph/rescan-playbook?org_id=${ORG_ID}`, { method: 'POST' })
            if (!res.ok) throw new Error('Rescan failed')
            return res.json()
        },
        onSuccess: (data) => {
            showToast(`Rescan complete — ${data.violations_found} violations found`, 'success')
            qc.invalidateQueries({ queryKey: ['graph'] })
            qc.invalidateQueries({ queryKey: ['risk'] })
        },
        onError: () => showToast('Rescan failed', 'error'),
    })
}

/* ─── PageIndex Tree ─── */
export function useContractTree(id: string | undefined) {
    return useQuery({
        queryKey: ['contract-tree', id],
        queryFn: async () => {
            const res = await apiFetch(`/pageindex/contracts/${id}/tree`)
            if (!res.ok) throw new Error('Failed to load tree')
            return res.json()
        },
        enabled: !!id,
    })
}

export function useContractTreeQuery(id: string | undefined) {
    return useMutation({
        mutationFn: async (query: string) => {
            const res = await apiFetch(`/pageindex/contracts/${id}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            })
            if (!res.ok) throw new Error('Query failed')
            return res.json()
        },
    })
}

/* ─── PII ─── */
export function useContractPII(id: string | undefined) {
    return useQuery({
        queryKey: ['contract-pii', id],
        queryFn: async () => {
            const res = await apiFetch(`/pii/contracts/${id}/scan`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to scan PII')
            return res.json()
        },
        enabled: !!id,
    })
}

export function useAnonymizeText() {
    return useMutation({
        mutationFn: async (text: string) => {
            const res = await apiFetch(`/pii/anonymize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            })
            if (!res.ok) throw new Error('Anonymization failed')
            return res.json()
        },
    })
}

export function useUpdateContract() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ id, data }: { id: string; data: any }) => {
            const res = await apiFetch(`/contracts/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            })
            if (!res.ok) throw new Error('Update failed')
            return res.json()
        },
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: ['contract', vars.id] })
        },
    })
}

export function useExplainRisk() {
    return useMutation({
        mutationFn: async (clauseId: string) => {
            const res = await apiFetch(`/plain-english/clauses/${clauseId}/explain-risk`, { method: 'POST' })
            if (!res.ok) throw new Error('Explain failed')
            return res.json()
        },
    })
}

export function useRiskReport() {
    return useMutation({
        mutationFn: async (contractId: string) => {
            const res = await apiFetch(`/reports/contracts/${contractId}/risk`)
            if (!res.ok) throw new Error('Report fetch failed')
            return res.json()
        },
    })
}
