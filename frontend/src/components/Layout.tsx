import React from 'react'
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material'
import { Link } from 'react-router-dom'

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>
              Document Analyzer
            </Link>
          </Typography>
          <Box>
            <Link to="/" style={{ color: 'white', marginRight: 20, textDecoration: 'none' }}>
              Upload
            </Link>
            <Link to="/history" style={{ color: 'white', marginRight: 20, textDecoration: 'none' }}>
              History
            </Link>
            <Link to="/metrics" style={{ color: 'white', textDecoration: 'none' }}>
              Metrics
            </Link>
          </Box>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {children}
      </Container>
    </>
  )
}

export default Layout