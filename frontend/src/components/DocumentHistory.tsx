import React, { useState, useEffect } from 'react'
import { Box, Typography, TextField, Button, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton, Pagination } from '@mui/material'
import { Search as SearchIcon, Download as DownloadIcon, Delete as DeleteIcon } from '@mui/icons-material'
import axios from 'axios'

interface DocumentHistoryItem {
  task_id: string
  filename: string
  document_type: string
  status: string
  created_at: string
  processing_time: number
  file_size: number
  pii_count: number
}

const DocumentHistory: React.FC = () => {
  const [history, setHistory] = useState<DocumentHistoryItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [page, setPage] = useState<number>(1)
  const [totalPages, setTotalPages] = useState<number>(1)
  const [error, setError] = useState<string | null>(null)

  const pageSize = 10

  useEffect(() => {
    fetchHistory()
  }, [page])

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/v1/history?page=${page}&page_size=${pageSize}&search=${searchTerm}`)
      setHistory(response.data.items)
      setTotalPages(response.data.total_pages)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch history')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    fetchHistory()
  }

  const handleDelete = async (taskId: string) => {
    try {
      await axios.delete(`/api/v1/history/${taskId}`)
      fetchHistory()
    } catch (err: any) {
      setError('Failed to delete document')
    }
  }

  const exportHistoryToCSV = () => {
    const headers = ['Task ID', 'Filename', 'Document Type', 'Status', 'Created At', 'Processing Time', 'File Size', 'PII Count']
    const rows = history.map(item => [
      item.task_id,
      item.filename,
      item.document_type,
      item.status,
      new Date(item.created_at).toLocaleString(),
      `${item.processing_time.toFixed(2)}s`,
      `${(item.file_size / 1024).toFixed(2)} KB`,
      item.pii_count
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `document_history_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'warning'
      case 'failed': return 'error'
      default: return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Document History
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<DownloadIcon />}
          onClick={exportHistoryToCSV}
        >
          Export History
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search documents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button 
          variant="contained" 
          startIcon={<SearchIcon />}
          onClick={handleSearch}
        >
          Search
        </Button>
      </Box>

      {error && (
        <Box sx={{ mb: 2 }}>
          <Typography color="error">{error}</Typography>
        </Box>
      )}

      {loading ? (
        <Typography>Loading...</Typography>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Task ID</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Document Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Processing Time</TableCell>
                  <TableCell>File Size</TableCell>
                  <TableCell>PII Count</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.task_id}>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {item.task_id}
                      </Typography>
                    </TableCell>
                    <TableCell>{item.filename}</TableCell>
                    <TableCell>
                      <Chip label={item.document_type} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={item.status} 
                        color={getStatusColor(item.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(item.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>{item.processing_time.toFixed(2)}s</TableCell>
                    <TableCell>{(item.file_size / 1024).toFixed(2)} KB</TableCell>
                    <TableCell>
                      <Chip 
                        label={item.pii_count} 
                        color={item.pii_count > 0 ? 'warning' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton 
                        size="small" 
                        onClick={() => window.location.href = `/results/${item.task_id}`}
                      >
                        <DownloadIcon />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        onClick={() => handleDelete(item.task_id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
            <Typography variant="body2" color="textSecondary">
              Showing {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, history.length)} of {history.length} documents
            </Typography>
            <Pagination 
              count={totalPages} 
              page={page} 
              onChange={(_, newPage) => setPage(newPage)}
              color="primary"
            />
          </Box>
        </>
      )}
    </Box>
  )
}

export default DocumentHistory