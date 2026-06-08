import { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react'
import { apiFetch } from '../lib/api'

pdfjs.GlobalWorkerOptions.workerSrc = `/pdf.worker.min.mjs`

interface PDFViewerProps {
    url: string
}

export default function PDFViewer({ url }: PDFViewerProps) {
    const [numPages, setNumPages] = useState(0)
    const [pageNumber, setPageNumber] = useState(1)
    const [scale, setScale] = useState(1.4)
    const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
    const [pdfError, setPdfError] = useState<string | null>(null)
    const [pdfLoading, setPdfLoading] = useState(true)

    useEffect(() => {
        let revoked = false
        setPdfLoading(true)
        setPdfError(null)
        setPdfBlobUrl(null)

        const loadPdf = async () => {
            try {
                const res = await apiFetch(url)
                if (!res.ok) throw new Error(`HTTP ${res.status}`)
                const blob = await res.blob()
                if (!revoked) {
                    setPdfBlobUrl(URL.createObjectURL(blob))
                    setPdfLoading(false)
                }
            } catch (err: any) {
                if (!revoked) {
                    setPdfError(err.message || 'Failed to load PDF')
                    setPdfLoading(false)
                }
            }
        }

        loadPdf()
        return () => {
            revoked = true
        }
    }, [url])

    if (pdfLoading) {
        return (
            <div className="flex items-center justify-center h-full text-sm text-gray-400">
                Loading PDF…
            </div>
        )
    }

    if (pdfError || !pdfBlobUrl) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-red-500 font-medium mb-2">Failed to load PDF file.</p>
                {pdfError && <p className="text-xs text-gray-400 mb-4">{pdfError}</p>}
                <button
                    onClick={() => window.open(url, '_blank')}
                    className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800"
                >
                    Open PDF in new tab
                </button>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setPageNumber(p => Math.max(1, p - 1))}
                        disabled={pageNumber <= 1}
                        className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 transition"
                    >
                        <ChevronLeft size={16} />
                    </button>
                    <span className="text-sm font-medium text-gray-700 tabular-nums">
                        {pageNumber} / {numPages}
                    </span>
                    <button
                        onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
                        disabled={pageNumber >= numPages}
                        className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 transition"
                    >
                        <ChevronRight size={16} />
                    </button>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setScale(s => Math.max(0.8, s - 0.2))}
                        className="p-1.5 rounded hover:bg-gray-100 transition"
                    >
                        <ZoomOut size={16} />
                    </button>
                    <span className="text-xs text-gray-400 w-10 text-center">{Math.round(scale * 100)}%</span>
                    <button
                        onClick={() => setScale(s => Math.min(2.5, s + 0.2))}
                        className="p-1.5 rounded hover:bg-gray-100 transition"
                    >
                        <ZoomIn size={16} />
                    </button>
                </div>
            </div>

            {/* Page */}
            <div className="flex-1 overflow-auto bg-gray-50 flex items-start justify-center p-4">
                <Document
                    file={pdfBlobUrl}
                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                    onLoadError={(err) => setPdfError(err.message)}
                >
                    <Page
                        pageNumber={pageNumber}
                        scale={scale}
                        className="shadow-lg"
                        renderAnnotationLayer={false}
                        renderTextLayer={false}
                    />
                </Document>
            </div>
        </div>
    )
}
