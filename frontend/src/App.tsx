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

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
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