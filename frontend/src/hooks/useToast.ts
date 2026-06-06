import toast from 'react-hot-toast'

export function showToast(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
    switch (type) {
        case 'success':
            toast.success(message, { duration: 4000, iconTheme: { primary: '#22C55E', secondary: '#fff' } })
            break
        case 'error':
            toast.error(message, { duration: 5000, iconTheme: { primary: '#EF4444', secondary: '#fff' } })
            break
        case 'warning':
            toast(message, {
                duration: 4000,
                icon: '⚠️',
                style: { background: '#FFF7ED', border: '1px solid #FED7AA', color: '#C2410C' },
            })
            break
        default:
            toast(message, { duration: 3000 })
    }
}

export function showPromiseToast<T>(
    promise: Promise<T>,
    messages: { loading: string; success: string; error: string }
) {
    return toast.promise(promise, {
        loading: messages.loading,
        success: messages.success,
        error: messages.error,
    }, { duration: 4000 })
}
