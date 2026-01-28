import { useCallback } from 'react'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { ResearchResponse } from '@/lib/api'

interface UseExportPdfReturn {
  exportToPdf: (result: ResearchResponse, elementId?: string) => Promise<void>
  exportResultToPdf: (result: ResearchResponse) => void
}

export function useExportPdf(): UseExportPdfReturn {
  
  // Export using html2canvas for visual fidelity
  const exportToPdf = useCallback(async (result: ResearchResponse, elementId?: string) => {
    if (elementId) {
      const element = document.getElementById(elementId)
      if (!element) {
        console.error('Element not found:', elementId)
        return
      }

      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#0f172a'
      })

      const pdf = new jsPDF('p', 'mm', 'a4')
      const imgData = canvas.toDataURL('image/png')
      const imgWidth = 190
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight)
      pdf.save(`research-report-${Date.now()}.pdf`)
    } else {
      exportResultToPdf(result)
    }
  }, [])

  // Export using text-based approach for cleaner PDFs
  const exportResultToPdf = useCallback((result: ResearchResponse) => {
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const margin = 20
    const contentWidth = pageWidth - margin * 2
    let yPosition = margin

    // Helper to add wrapped text
    const addWrappedText = (text: string, fontSize: number, isBold: boolean = false) => {
      pdf.setFontSize(fontSize)
      pdf.setFont('helvetica', isBold ? 'bold' : 'normal')
      const lines = pdf.splitTextToSize(text, contentWidth)
      
      lines.forEach((line: string) => {
        if (yPosition > 270) {
          pdf.addPage()
          yPosition = margin
        }
        pdf.text(line, margin, yPosition)
        yPosition += fontSize * 0.5
      })
      yPosition += 5
    }

    // Header
    pdf.setFillColor(99, 102, 241)
    pdf.rect(0, 0, pageWidth, 40, 'F')
    pdf.setTextColor(255, 255, 255)
    pdf.setFontSize(24)
    pdf.setFont('helvetica', 'bold')
    pdf.text('🔬 Research Report', margin, 25)
    
    // Reset text color
    pdf.setTextColor(30, 30, 30)
    yPosition = 55

    // Question
    pdf.setFillColor(240, 240, 250)
    pdf.rect(margin - 5, yPosition - 5, contentWidth + 10, 20, 'F')
    addWrappedText(`Query ID: ${result.query_id}`, 11, true)
    yPosition += 5

    // Metadata
    pdf.setTextColor(100, 100, 100)
    addWrappedText(`📅 Fecha: ${new Date().toLocaleDateString('es-ES', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })}`, 9)
    
    if (result.processing_time_ms) {
      addWrappedText(`⏱️ Tiempo de procesamiento: ${(result.processing_time_ms / 1000).toFixed(2)}s`, 9)
    }
    
    if (result.confidence_score) {
      addWrappedText(`📊 Confianza: ${Math.round(result.confidence_score * 100)}%`, 9)
    }
    
    pdf.setTextColor(30, 30, 30)
    yPosition += 5

    // Synthesis
    pdf.setFillColor(99, 102, 241)
    pdf.rect(margin - 5, yPosition - 3, 3, 15, 'F')
    addWrappedText('📝 Síntesis', 14, true)
    addWrappedText(result.synthesis, 10)
    yPosition += 5

    // Key Findings
    if (result.key_findings && result.key_findings.length > 0) {
      pdf.setFillColor(16, 185, 129)
      pdf.rect(margin - 5, yPosition - 3, 3, 15, 'F')
      addWrappedText('🎯 Hallazgos Clave', 14, true)
      
      result.key_findings.forEach((finding, index) => {
        addWrappedText(`${index + 1}. ${finding}`, 10)
      })
      yPosition += 5
    }

    // Sources
    if (result.sources && result.sources.length > 0) {
      pdf.setFillColor(251, 191, 36)
      pdf.rect(margin - 5, yPosition - 3, 3, 15, 'F')
      addWrappedText('📚 Fuentes', 14, true)
      
      result.sources.forEach((source, index) => {
        addWrappedText(`${index + 1}. ${source.title}`, 10, true)
        pdf.setTextColor(99, 102, 241)
        addWrappedText(source.url, 8)
        pdf.setTextColor(30, 30, 30)
        if (source.snippet) {
          addWrappedText(source.snippet.substring(0, 200) + '...', 9)
        }
        yPosition += 2
      })
    }

    // Footer
    const pageCount = pdf.getNumberOfPages()
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i)
      pdf.setFontSize(8)
      pdf.setTextColor(150, 150, 150)
      pdf.text(
        `Generado por Autonomous Tech Research Agent | Desarrollado por Danilo Viteri | Página ${i} de ${pageCount}`,
        pageWidth / 2,
        285,
        { align: 'center' }
      )
    }

    // Save
    const fileName = `research-report-${result.query_id.slice(0, 30).replace(/[^a-z0-9]/gi, '-')}-${Date.now()}.pdf`
    pdf.save(fileName)
  }, [])

  return {
    exportToPdf,
    exportResultToPdf,
  }
}
