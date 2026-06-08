import { useNavigate } from 'react-router-dom'
import { ArrowLeft, FileQuestion } from 'lucide-react'

export default function NotFoundPage() {
    const navigate = useNavigate()
    return (
        <div className="flex flex-col items-center justify-center h-full p-8">
            <FileQuestion size={64} className="text-gray-300 mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
            <p className="text-sm text-gray-500 mb-6">The page you are looking for does not exist.</p>
            <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-light transition-colors"
            >
                <ArrowLeft size={16} /> Back to Dashboard
            </button>
        </div>
    )
}
