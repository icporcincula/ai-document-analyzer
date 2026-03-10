import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Box, Button, Typography, LinearProgress, Alert } from '@mui/material'
import { CloudUpload as UploadIcon } from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

interface UploadResponse {
  task_id: string
  message: string
}

const DocumentUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation(
    async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await axios.post<UploadResponse>(
        'http://localhost:8000/api/v1/analyze',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              setUploadProgress(progress)
            }
          },
        }
      )
      return response.data
    },
    {
      onSuccess: (data) => {
        setIsUploading(false)
        setUploadProgress(0)
        setFiles([])
        // Navigate to results page
        window.location.href = `/results/${data.task_id}`
      },
      onError: () => {
        setIsUploading(false)
        setUploadProgress(0)
      }
    }
  )

  const onDrop = (acceptedFiles: File[]) => {
    setFiles(acceptedFiles)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    },
    maxFiles: 1,
  })

  const handleUpload = () => {
    if (files.length > 0) {
      setIsUploading(true)
      uploadMutation.mutate(files[0])
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Document Upload
      </Typography>
      
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed #ccc',
          borderRadius: 2,
          padding: 4,
          textAlign: 'center',
          backgroundColor: isDragActive ? '#f0f0f0' : '#fafafa',
          cursor: 'pointer',
          transition: 'background-color 0.3s',
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 60, color: '#999', mb: 2 }} />
        <Typography variant="h6">
          {isDragActive ? 'Drop the file here ...' : 'Drag & drop a document here, or click to select'}
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Supported formats: PDF, DOCX, PPTX, JPG, PNG, GIF, BMP
        </Typography>
      </Box>

      {files.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1">Selected file:</Typography>
          <Typography>{files[0].name}</Typography>
          <Typography variant="body2" color="textSecondary">
            Size: {(files[0].size / 1024 / 1024).toFixed(2)} MB
          </Typography>
        </Box>
      )}

      {isUploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Uploading: {uploadProgress}%
          </Typography>
        </Box>
      )}

      {uploadMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Upload failed. Please try again.
        </Alert>
      )}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={files.length === 0 || isUploading}
        >
          Upload & Analyze
        </Button>
        <Button
          variant="outlined"
          onClick={() => setFiles([])}
          disabled={isUploading}
        >
          Clear
        </Button>
      </Box>
    </Box>
  )
}

export default DocumentUpload