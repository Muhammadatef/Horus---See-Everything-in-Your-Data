import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  Dashboard as DashboardIcon,
  CheckCircle as CheckIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Offline as OfflineIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { healthApi, dataApi } from '../../services/api';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  // Check system health
  const { data: healthData, isError: healthError } = useQuery(
    'health',
    healthApi.detailed,
    {
      retry: 1,
      refetchInterval: 30000, // Check every 30 seconds
    }
  );

  // Get recent datasets
  const { data: datasets } = useQuery('datasets', dataApi.getDatasets, {
    retry: 1,
  });

  const features = [
    {
      icon: <SecurityIcon color="primary" />,
      title: 'Complete Privacy',
      description: 'Your data never leaves your machine. Zero cloud dependencies.',
    },
    {
      icon: <SpeedIcon color="primary" />,
      title: 'Instant Results',
      description: 'Ask questions in natural language, get answers in seconds.',
    },
    {
      icon: <OfflineIcon color="primary" />,
      title: 'Offline Ready',
      description: 'Works completely offline with local AI models.',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Data',
      description: 'Upload CSV, Excel, JSON, or Parquet files',
      icon: <UploadIcon />,
      action: () => navigate('/upload'),
      color: '#4caf50',
    },
    {
      title: 'Query Data',
      description: 'Ask questions about your data in natural language',
      icon: <SearchIcon />,
      action: () => navigate('/query'),
      color: '#2196f3',
    },
    {
      title: 'View Dashboard',
      description: 'See insights and visualizations',
      icon: <DashboardIcon />,
      action: () => navigate('/dashboard'),
      color: '#ff9800',
    },
  ];

  const getHealthStatus = () => {
    if (healthError) {
      return { status: 'error', message: 'System not responding' };
    }
    
    if (!healthData?.data) {
      return { status: 'loading', message: 'Checking system status...' };
    }

    const health = healthData.data;
    if (health.status === 'healthy') {
      return { status: 'success', message: 'All systems operational' };
    } else {
      return { status: 'warning', message: 'Some services may be degraded' };
    }
  };

  const healthStatus = getHealthStatus();

  return (
    <Box>
      {/* Hero Section */}
      <Paper
        elevation={0}
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          p: 6,
          mb: 4,
          borderRadius: 2,
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom align="center">
          Local AI-BI Platform
        </Typography>
        <Typography variant="h5" align="center" sx={{ mb: 3, opacity: 0.9 }}>
          Upload your data, ask questions in plain English, get instant insights
        </Typography>
        
        {/* System Status */}
        <Box display="flex" justifyContent="center" alignItems="center" gap={2}>
          <Chip
            icon={<CheckIcon />}
            label={healthStatus.message}
            color={healthStatus.status as any}
            variant="filled"
            sx={{ color: 'white', backgroundColor: 'rgba(255,255,255,0.2)' }}
          />
          {datasets && (
            <Chip
              label={`${datasets.length} datasets available`}
              variant="outlined"
              sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)' }}
            />
          )}
        </Box>
      </Paper>

      {/* Quick Actions */}
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Quick Actions
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {quickActions.map((action, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={action.action}
            >
              <CardContent sx={{ pb: 1 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mb: 2,
                    color: action.color,
                  }}
                >
                  {action.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {action.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" sx={{ color: action.color }}>
                  Get Started
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Features */}
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Why Choose Local AI-BI?
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {features.map((feature, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box display="flex" alignItems="center" mb={2}>
                {feature.icon}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {feature.title}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {feature.description}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Getting Started */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Getting Started
        </Typography>
        <Typography variant="body1" paragraph>
          Welcome to your local AI-powered Business Intelligence platform! Here's how to get started:
        </Typography>
        
        <List>
          <ListItem>
            <ListItemIcon>
              <Typography variant="h6" color="primary">1</Typography>
            </ListItemIcon>
            <ListItemText
              primary="Upload Your Data"
              secondary="Drag and drop CSV, Excel, JSON, or Parquet files. We'll automatically clean and process them."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <Typography variant="h6" color="primary">2</Typography>
            </ListItemIcon>
            <ListItemText
              primary="Ask Questions"
              secondary='Use natural language like "How many active users do we have?" or "Show me sales by region".'
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <Typography variant="h6" color="primary">3</Typography>
            </ListItemIcon>
            <ListItemText
              primary="Get Insights"
              secondary="Receive instant answers with automatic visualizations and charts."
            />
          </ListItem>
        </List>

        {/* Demo File Notice */}
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Try the demo:</strong> Upload the sample user analytics file from{' '}
            <code>data/samples/user_analytics.csv</code> and ask:{' '}
            <em>"How many active users do we have?"</em>
          </Typography>
        </Alert>
      </Paper>
    </Box>
  );
};

export default HomePage;