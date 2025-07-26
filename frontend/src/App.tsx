import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Layout from './components/common/Layout';
import HomePage from './components/common/HomePage';
import UploadDataPage from './components/upload/UploadDataPage';
import RealTimeUploadPage from './components/upload/RealTimeUploadPage';
import QueryDataPage from './components/query/QueryDataPage';
import RealTimeQueryPage from './components/query/RealTimeQueryPage';
import DashboardPage from './components/dashboard/DashboardPage';
import ChatPage from './components/chat/ChatPage';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#DAA520', // Egyptian gold
    },
    secondary: {
      main: '#B8860B', // Darker gold
    },
    background: {
      default: '#0f0f23', // Dark space blue
      paper: 'rgba(255, 255, 255, 0.05)', // Transparent white
    },
    text: {
      primary: 'rgba(255, 255, 255, 0.9)',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1.1rem',
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 500,
          padding: '10px 24px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box className="app">
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/upload" element={<RealTimeUploadPage />} />
              <Route path="/upload-legacy" element={<UploadDataPage />} />
              <Route path="/query" element={<RealTimeQueryPage />} />
              <Route path="/query-legacy" element={<QueryDataPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;