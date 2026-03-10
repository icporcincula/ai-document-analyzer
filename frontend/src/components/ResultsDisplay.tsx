import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, LinearProgress, Alert, Button, Chip, Grid, Card, CardContent } from '@mui/material'
import { Download as DownloadIcon } from '@mui/icons-material'
import axios from 'axios'
import { saveAs } from 'file-saver'

interface AnalysisResult {
  task_id: string
  status: string
  extracted_fields: Record<string, any>
  pii_entities: Array<{
    entity_type: string
    text: string
    confidence: number
  }>
  confidence_scores: Record<string, number>
  processing_time: number
  file_size: number
  document_type: string
}

const ResultsDisplay: React.FC = () => {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (taskId) {
      fetchResult(taskId)
    }
  }, [taskId])

  const fetchResult = async (id: string) => {
    try {
      setLoading(true)
      const response = await axios.get<AnalysisResult>(`http://localhost:8000/api/v1/results/${id}`)
      setResult(response.data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch results')
    } finally {
      setLoading(false)
    }
  }

  const exportToCSV = () => {
    if (!result) return
    
    const headers = ['Field', 'Value', 'Confidence']
    const rows = Object.entries(result.extracted_fields).map(([field, value]) => [
      field,
      String(value),
      result.confidence_scores[field] || 'N/A'
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    saveAs(blob, `analysis_results_${result.task_id}.csv`)
  }

  const exportToExcel = () => {
    if (!result) return
    
    // This would require the xlsx library implementation
    // For now, we'll just show a message
    alert('Excel export functionality would be implemented here')
  }

  const exportToJSON = () => {
    if (!result) return
    
    const jsonContent = JSON.stringify(result, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })
    saveAs(blob, `analysis_results_${result.task_id}.json`)
  }

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Processing Results
        </Typography>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Please wait while we process your document...
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={() => navigate('/')}>
          Go Back to Upload
        </Button>
      </Box>
    )
  }

  if (!result) {
    return (
      <Alert severity="info">
        No results found for this task ID.
      </Alert>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Analysis Results
        </Typography>
        <Chip 
          label={result.status} 
          color={result.status === 'completed' ? 'success' : 'warning'} 
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Document Information
              </Typography>
              <Typography><strong>Task ID:</strong> {result.task_id}</Typography>
              <Typography><strong>Document Type:</strong> {result.document_type}</Typography>
              <Typography><strong>File Size:</strong> {(result.file_size / 1024).toFixed(2)} KB</Typography>
              <Typography><strong>Processing Time:</strong> {result.processing_time.toFixed(2)} seconds</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                PII Detection Summary
              </Typography>
              <Typography><strong>Total PII Entities:</strong> {result.pii_entities.length}</Typography>
              {result.pii_entities.map((entity, index) => (
                <Chip 
                  key={index}
                  label={`${entity.entity_type}: ${entity.text}`}
                  variant="outlined"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Extracted Fields
                </Typography>
                <Box>
                  <Button 
                    startIcon={<DownloadIcon />} 
                    onClick={exportToCSV}
                    sx={{ mr: 1 }}
                  >
                    CSV
                  </Button>
                  <Button 
                    startIcon={<DownloadIcon />} 
                    onClick={exportToExcel}
                    sx={{ mr: 1 }}
                  >
                    Excel
                  </Button>
                  <Button 
                    startIcon={<DownloadIcon />} 
                    onClick={exportToJSON}
                  >
                    JSON
                  </Button>
                </Box>
              </Box>
              
              <Grid container spacing={2}>
                {Object.entries(result.extracted_fields).map(([field, value]) => (
                  <Grid item xs={12} sm={6} md={4} key={field}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          {field}
                        </Typography>
                        <Typography variant="body1">
                          {String(value)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Confidence: {(result.confidence_scores[field] * 100).toFixed(1)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button variant="outlined" onClick={() => navigate('/')}>
          Analyze Another Document
        </Button>
        <Button variant="contained" onClick={() => navigate('/history')}>
          View History
        </Button>
      </Box>
    </Box>
  )
}

export default ResultsDisplay