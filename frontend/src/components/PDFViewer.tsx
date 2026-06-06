import { useState, useEffect, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw, Highlighter, Flame, ShieldCheck } from 'lucide-react'
import { apiFetch } from '../lib/api'

pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface Highlight {
    id: string
    clause_type: string
    clause_text: string
    page_number: number
    x: number
    y: number
    width: number
    height: number
    color: string
    risk_color: string
}

interface PDFViewerProps {
    url: string
    contractId?: string
}

export default function PDFViewer({ url, contractId }: PDFViewerProps) {
    const [numPages, setNumPages] = useState(0)
    const [pageNumber, setPageNumber] = useState(1)
    const [scale, setScale] = useState(1.2)
    const [rotation, setRotation] = useState(0)
    const [highlights, setHighlights] = useState<Highlight[]>([])
    const [showHighlights, setShowHighlights] = useState(true)
    const [useRiskHeatmap, setUseRiskHeatmap] = useState(false)
    const [loadingHighlights, setLoadingHighlights] = useState(false)
    const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
    const [pdfError, setPdfError] = useState<string | null>(null)
    const [pdfLoading, setPdfLoading] = useState(true)

    // Load PDF as blob URL to bypass CORS/proxy issues
    useEffect(() => {
        let revoked = false
        setPdfLoading(true)
        setPdfError(null)
        setPdfBlobUrl(null)

        const loadPdf = async () => {
            try {
                const res = await apiFetch(url)
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`)
                }
                const blob = await res.blob()
                if (!revoked) {
                    const blobUrl = URL.createObjectURL(blob)
                    setPdfBlobUrl(blobUrl)
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
            if (pdfBlobUrl) {
                URL.revokeObjectURL(pdfBlobUrl)
            }
        }
    }, [url])

    // Load highlights when contractId changes
    useEffect(() => {
        if (!contractId) return
        setLoadingHighlights(true)
        apiFetch(`/highlights/contracts/${contractId}`)
            .then(r => r.json())
            .then(data => {
                const hls = (data.highlights || []).map((h: any) => ({
                    ...h,
                    ...h.bounding_box,
                    risk_color: h.bounding_box?.risk_color || h.color,
                }))
                setHighlights(hls)
            })
            .catch(() => setHighlights([]))
            .finally(() => setLoadingHighlights(false))
    }, [contractId])

    const generateHighlights = useCallback(async () => {
        if (!contractId) return
        setLoadingHighlights(true)
        try {
            const r = await apiFetch(`/highlights/contracts/${contractId}/generate`, { method: 'POST' })
            const data = await r.json()
            const hls = (data.highlights || []).map((h: any) => ({
                ...h,
                ...h.bounding_box,
                risk_color: h.bounding_box?.risk_color || h.color,
            }))
            setHighlights(hls)
        } catch (e) {
            console.error('Failed to generate highlights', e)
        }
        setLoadingHighlights(false)
    }, [contractId])

    const pageHighlights = highlights.filter(h => h.page_number === pageNumber)

    const riskCounts = {
        critical: highlights.filter(h => h.risk_color?.includes('239, 68, 68')).length,
        high: highlights.filter(h => h.risk_color?.includes('249, 115, 22')).length,
        medium: highlights.filter(h => h.risk_color?.includes('245, 158, 11')).length,
        low: highlights.filter(h => h.risk_color?.includes('34, 197, 94')).length,
    }

    if (pdfLoading) {
        return (
            <div className="flex items-center justify-center h-[700px] text-sm text-gray-400">
                Loading PDF...
            </div>
        )
    }

    if (pdfError || !pdfBlobUrl) {
        return (
            <div className="flex flex-col items-center justify-center h-[700px] text-center">
                <p className="text-red-500 font-medium mb-2">Failed to load PDF file.</p>
                {pdfError && <p className="text-xs text-gray-400 mb-4">{pdfError}</p>}
                <button
                    onClick={() => window.open(url, '_blank')}
                    className="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-light"
                >
                    Open PDF in new tab
                </button>
            </div>
        )
    }

    return (
        <div className="flex gap-4 h-[700px]">
            {/* Thumbnail sidebar */}
            <div className="w-48 overflow-y-auto border-r pr-2">
                <Document
                    file={pdfBlobUrl}
                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                    onLoadError={(err) => console.error('Thumbnail load error:', err)}
                >
                    {Array.from({ length: numPages }, (_, i) => (
                        <div
                            key={i}
                            className={`mb-2 cursor-pointer ${pageNumber === i + 1 ? 'ring-2 ring-blue-500' : ''}`}
                            onClick={() => setPageNumber(i + 1)}
                        >
                            <Page pageNumber={i + 1} width={120} />
                        </div>
                    ))}
                </Document>
            </div>

            {/* Main viewer */}
            <div className="flex-1 flex flex-col">
                {/* Toolbar */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <button onClick={() => setPageNumber(p => Math.max(1, p - 1))}><ChevronLeft size={16} /></button>
                    <span className="text-sm">{pageNumber} / {numPages}</span>
                    <button onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}><ChevronRight size={16} /></button>
                    <span className="w-px h-4 bg-gray-300 mx-1" />
                    <button onClick={() => setScale(s => Math.min(3, s + 0.2))}><ZoomIn size={16} /></button>
                    <button onClick={() => setScale(s => Math.max(0.5, s - 0.2))}><ZoomOut size={16} /></button>
                    <button onClick={() => setRotation(r => (r + 90) % 360)}><RotateCw size={16} /></button>
                    <span className="w-px h-4 bg-gray-300 mx-1" />
                    {highlights.length > 0 && (
                        <>
                            <button
                                onClick={() => setShowHighlights(v => !v)}
                                className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${showHighlights ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'}`}
                            >
                                <Highlighter size={14} />
                                {showHighlights ? `${highlights.length} highlights` : 'Hide'}
                            </button>
                            <button
                                onClick={() => setUseRiskHeatmap(v => !v)}
                                className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${useRiskHeatmap ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}
                            >
                                <Flame size={14} />
                                {useRiskHeatmap ? 'Risk Heatmap' : 'Clause Types'}
                            </button>
                        </>
                    )}
                    {loadingHighlights && <span className="text-xs text-gray-400 animate-pulse">Loading highlights...</span>}
                </div>

                {/* Page with highlights */}
                <div className="flex-1 overflow-auto bg-gray-100 rounded-lg relative">
                    <Document
                        file={pdfBlobUrl}
                        onLoadError={(err) => console.error('PDF load error:', err)}
                    >
                        <div className="relative inline-block">
                            <Page
                                pageNumber={pageNumber}
                                scale={scale}
                                rotate={rotation}
                                className="shadow-lg mx-auto my-4"
                            />
                            {/* Highlight overlays */}
                            {showHighlights && pageHighlights.map(h => (
                                <div
                                    key={h.id}
                                    className="absolute rounded-sm pointer-events-none"
                                    style={{
                                        left: `${h.x * 100}%`,
                                        top: `${h.y * 100}%`,
                                        width: `${h.width * 100}%`,
                                        height: `${h.height * 100}%`,
                                        backgroundColor: useRiskHeatmap ? h.risk_color : h.color,
                                    }}
                                    title={`${h.clause_type}${useRiskHeatmap ? ' (risk view)' : ''}`}
                                />
                            ))}
                        </div>
                    </Document>
                </div>

                {/* Legend */}
                {showHighlights && highlights.length > 0 && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                        {useRiskHeatmap ? (
                            <>
                                {riskCounts.critical > 0 && (
                                    <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full flex items-center gap-1">
                                        <Flame size={10} /> Critical ({riskCounts.critical})
                                    </span>
                                )}
                                {riskCounts.high > 0 && (
                                    <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full flex items-center gap-1">
                                        <Flame size={10} /> High ({riskCounts.high})
                                    </span>
                                )}
                                {riskCounts.medium > 0 && (
                                    <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full flex items-center gap-1">
                                        <Flame size={10} /> Medium ({riskCounts.medium})
                                    </span>
                                )}
                                {riskCounts.low > 0 && (
                                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full flex items-center gap-1">
                                        <ShieldCheck size={10} /> Low / OK ({riskCounts.low})
                                    </span>
                                )}
                            </>
                        ) : (
                            Array.from(new Set(highlights.map(h => h.clause_type))).map(ct => (
                                <span key={ct} className="text-xs px-2 py-0.5 bg-gray-100 rounded-full capitalize">
                                    {ct.replace('_', ' ')}
                                </span>
                            ))
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
