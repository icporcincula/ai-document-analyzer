import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import DocumentUpload from './components/DocumentUpload'
import ResultsDisplay from './components/ResultsDisplay'
import DocumentHistory from './components/DocumentHistory'
import Layout from './components/Layout'

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <Routes>
          <Route path="/" element={<DocumentUpload />} />
          <Route path="/results/:taskId" element={<ResultsDisplay />} />
          <Route path="/history" element={<DocumentHistory />} />
        </Routes>
        <ToastContainer />
      </Layout>
    </ThemeProvider>
  )
}

export default App