/** Centralized API client with retry logic and env-based URL. */
export const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

const MAX_RETRIES = 2
const RETRY_DELAY = 500

async function sleep(ms: number) {
    return new Promise(r => setTimeout(r, ms))
}

export async function apiFetch(path: string, options?: RequestInit, retries = MAX_RETRIES): Promise<Response> {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`
    try {
        const res = await fetch(url, options)
        if (!res.ok && retries > 0 && res.status >= 500) {
            await sleep(RETRY_DELAY)
            return apiFetch(path, options, retries - 1)
        }
        if (!res.ok) {
            const errBody = await res.json().catch(() => ({}))
            const message = errBody.detail || errBody.message || `HTTP ${res.status}: ${res.statusText}`
            throw new Error(message)
        }
        return res
    } catch (err) {
        if (retries > 0 && err instanceof Error && !err.message.startsWith('HTTP ')) {
            await sleep(RETRY_DELAY)
            return apiFetch(path, options, retries - 1)
        }
        throw err
    }
}
