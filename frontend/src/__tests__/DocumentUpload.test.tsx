import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import DocumentUpload from '../components/DocumentUpload'

// Mock dependencies
jest.mock('axios')
jest.mock('react-query', () => ({
  useMutation: jest.fn(),
  useQueryClient: () => ({
    invalidateQueries: jest.fn()
  })
}))

const mockUseMutation = {
  mutate: jest.fn(),
  isLoading: false,
  isError: false
}

const mockUseQueryClient = {
  invalidateQueries: jest.fn()
}

describe('DocumentUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders upload component', () => {
    render(<DocumentUpload />)
    expect(screen.getByText('Document Upload')).toBeInTheDocument()
    expect(screen.getByText('Drag & drop a document here, or click to select')).toBeInTheDocument()
  })

  it('handles file selection', async () => {
    render(<DocumentUpload />)
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const input = screen.getByTestId('file-input') || screen.getByText('Drag & drop a document here, or click to select')
    
    fireEvent.change(input, { target: { files: [file] } })
    
    await waitFor(() => {
      expect(screen.getByText('Selected file:')).toBeInTheDocument()
      expect(screen.getByText('test.pdf')).toBeInTheDocument()
    })
  })

  it('shows upload progress', async () => {
    const { useMutation } = require('react-query')
    useMutation.mockReturnValue({
      ...mockUseMutation,
      isLoading: true
    })

    render(<DocumentUpload />)
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const input = screen.getByTestId('file-input') || screen.getByText('Drag & drop a document here, or click to select')
    
    fireEvent.change(input, { target: { files: [file] } })
    
    const uploadButton = screen.getByText('Upload & Analyze')
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText('Uploading: 0%')).toBeInTheDocument()
    })
  })

  it('handles upload success', async () => {
    const { useMutation } = require('react-query')
    useMutation.mockReturnValue({
      ...mockUseMutation,
      mutate: jest.fn((file, { onSuccess }) => {
        onSuccess({ task_id: 'test-task-id' })
      })
    })

    render(<DocumentUpload />)
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const input = screen.getByTestId('file-input') || screen.getByText('Drag & drop a document here, or click to select')
    
    fireEvent.change(input, { target: { files: [file] } })
    
    const uploadButton = screen.getByText('Upload & Analyze')
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(window.location.href).toBe('/results/test-task-id')
    })
  })

  it('handles upload error', async () => {
    const { useMutation } = require('react-query')
    useMutation.mockReturnValue({
      ...mockUseMutation,
      isError: true
    })

    render(<DocumentUpload />)
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const input = screen.getByTestId('file-input') || screen.getByText('Drag & drop a document here, or click to select')
    
    fireEvent.change(input, { target: { files: [file] } })
    
    const uploadButton = screen.getByText('Upload & Analyze')
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText('Upload failed. Please try again.')).toBeInTheDocument()
    })
  })
})