import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Container,
  Chip,
  IconButton,
  Fade,
  Slide,
  Zoom,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  AutoAwesome as AutoAwesomeIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Insights as InsightsIcon,
  ArrowForward as ArrowForwardIcon,
  PlayCircleFilled as PlayIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { healthApi, dataApi } from '../../services/api';

// Animated Counter Component
const AnimatedCounter: React.FC<{ end: number; suffix?: string; duration?: number }> = ({ 
  end, 
  suffix = '', 
  duration = 2000 
}) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime: number;
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    requestAnimationFrame(animate);
  }, [end, duration]);

  return <span>{count}{suffix}</span>;
};

// Feature Card Component
const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
  color: string;
}> = ({ icon, title, description, delay, color }) => {
  return (
    <Zoom in timeout={800} style={{ transitionDelay: `${delay}ms` }}>
      <Card
        sx={{
          height: '100%',
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
          transition: 'all 0.4s ease',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            transform: 'translateY(-8px)',
            border: `1px solid ${alpha(color, 0.5)}`,
            boxShadow: `0 20px 40px ${alpha(color, 0.2)}`,
          },
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: `linear-gradient(90deg, ${color}, transparent)`,
          },
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Box
            sx={{
              color: color,
              mb: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 60,
              height: 60,
              borderRadius: 2,
              background: `${alpha(color, 0.1)}`,
              border: `1px solid ${alpha(color, 0.2)}`,
            }}
          >
            {icon}
          </Box>
          <Typography
            variant="h6"
            sx={{
              color: 'rgba(255, 255, 255, 0.9)',
              fontWeight: 600,
              mb: 1,
            }}
          >
            {title}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              lineHeight: 1.6,
            }}
          >
            {description}
          </Typography>
        </CardContent>
      </Card>
    </Zoom>
  );
};

// Quick Action Button
const QuickActionButton: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
  color: string;
  delay: number;
}> = ({ icon, title, description, onClick, color, delay }) => {
  return (
    <Slide in direction="up" timeout={600} style={{ transitionDelay: `${delay}ms` }}>
      <Card
        onClick={onClick}
        sx={{
          cursor: 'pointer',
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
          transition: 'all 0.4s ease',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            transform: 'translateY(-4px) scale(1.02)',
            background: `${alpha(color, 0.1)}`,
            border: `1px solid ${alpha(color, 0.3)}`,
            boxShadow: `0 15px 30px ${alpha(color, 0.2)}`,
          },
        }}
      >
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Box
            sx={{
              color: color,
              mb: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 80,
              height: 80,
              borderRadius: 3,
              background: `${alpha(color, 0.1)}`,
              border: `2px solid ${alpha(color, 0.2)}`,
              mx: 'auto',
              fontSize: '2rem',
            }}
          >
            {icon}
          </Box>
          <Typography
            variant="h6"
            sx={{
              color: 'rgba(255, 255, 255, 0.9)',
              fontWeight: 600,
              mb: 1,
            }}
          >
            {title}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: 'rgba(255, 255, 255, 0.6)',
              lineHeight: 1.5,
            }}
          >
            {description}
          </Typography>
        </CardContent>
      </Card>
    </Slide>
  );
};

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  // Check system health
  const { data: healthData, isError: healthError } = useQuery(
    'health',
    healthApi.detailed,
    {
      retry: 1,
      refetchInterval: 30000,
    }
  );

  // Get recent datasets
  const { data: datasets } = useQuery('datasets', dataApi.getDatasets, {
    retry: 1,
  });

  const features = [
    {
      icon: <SecurityIcon fontSize="large" />,
      title: 'Complete Privacy',
      description: 'Your data never leaves your machine. Zero cloud dependencies with full local processing.',
      color: '#4CAF50',
    },
    {
      icon: <SpeedIcon fontSize="large" />,
      title: 'Lightning Fast',
      description: 'Ask questions in natural language and get instant AI-powered insights in seconds.',
      color: '#2196F3',
    },
    {
      icon: <InsightsIcon fontSize="large" />,
      title: 'Smart Analytics',
      description: 'Advanced AI automatically understands your data and generates meaningful visualizations.',
      color: '#FF9800',
    },
  ];

  const quickActions = [
    {
      icon: <SearchIcon />,
      title: 'Chat with Horus',
      description: 'Upload files and ask questions in natural language - ChatGPT style',
      onClick: () => navigate('/chat'),
      color: '#DAA520',
    },
    {
      icon: <UploadIcon />,
      title: 'Upload Data',
      description: 'Drag & drop CSV, Excel, JSON, or Parquet files',
      onClick: () => navigate('/upload'),
      color: '#4CAF50',
    },
    {
      icon: <DashboardIcon />,
      title: 'Analytics',
      description: 'Explore insights and interactive visualizations',
      onClick: () => navigate('/dashboard'),
      color: '#FF9800',
    },
  ];

  const getHealthStatus = () => {
    if (healthError) {
      return { status: 'error', message: 'System offline', color: '#f44336' };
    }
    
    if (!healthData?.data) {
      return { status: 'default', message: 'Connecting...', color: '#ff9800' };
    }

    const health = healthData.data;
    if (health.status === 'healthy') {
      return { status: 'success', message: 'All systems operational', color: '#4caf50' };
    } else {
      return { status: 'warning', message: 'Some services degraded', color: '#ff9800' };
    }
  };

  const healthStatus = getHealthStatus();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Hero Section */}
      <Fade in timeout={1000}>
        <Box
          sx={{
            textAlign: 'center',
            mb: 8,
            position: 'relative',
          }}
        >
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              mb: 4,
            }}
          >
            <Box
              sx={{
                fontSize: '4rem',
                background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 20px rgba(184, 134, 11, 0.5))',
                animation: 'pulse 3s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': {
                    filter: 'drop-shadow(0 0 20px rgba(184, 134, 11, 0.5))',
                  },
                  '50%': {
                    filter: 'drop-shadow(0 0 30px rgba(184, 134, 11, 0.8))',
                  },
                },
              }}
            >
              𓂀
            </Box>
            <Box>
              <Typography
                variant="h1"
                sx={{
                  background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 800,
                  fontSize: { xs: '3rem', md: '4rem', lg: '5rem' },
                  letterSpacing: '-0.02em',
                  lineHeight: 1,
                }}
              >
                Horus AI
              </Typography>
              <Typography
                variant="h4"
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  fontWeight: 300,
                  fontSize: { xs: '1.2rem', md: '1.5rem' },
                  mt: 1,
                }}
              >
                All-seeing Business Intelligence
              </Typography>
            </Box>
          </Box>

          <Typography
            variant="h5"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              fontWeight: 400,
              lineHeight: 1.4,
              mb: 4,
              maxWidth: '800px',
              mx: 'auto',
            }}
          >
            Upload your data, ask questions in plain English, and get instant AI-powered insights 
            with complete privacy on your local machine.
          </Typography>

          {/* Status and Stats */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 4,
              flexWrap: 'wrap',
              mb: 6,
            }}
          >
            <Chip
              icon={
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: healthStatus.color,
                    animation: healthStatus.status === 'success' ? 'pulse 2s infinite' : 'none',
                  }}
                />
              }
              label={healthStatus.message}
              sx={{
                background: 'rgba(255, 255, 255, 0.1)',
                color: 'rgba(255, 255, 255, 0.9)',
                border: `1px solid ${alpha(healthStatus.color, 0.3)}`,
                fontWeight: 500,
              }}
            />
            {datasets && (
              <Chip
                label={`${datasets.length} Datasets Ready`}
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'rgba(255, 255, 255, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  fontWeight: 500,
                }}
              />
            )}
            <Chip
              label="100% Local & Private"
              sx={{
                background: 'rgba(76, 175, 80, 0.2)',
                color: 'rgba(255, 255, 255, 0.9)',
                border: '1px solid rgba(76, 175, 80, 0.3)',
                fontWeight: 500,
              }}
            />
          </Box>

          {/* CTA Button */}
          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/chat')}
            sx={{
              background: 'linear-gradient(135deg, #DAA520, #B8860B)',
              color: 'white',
              px: 4,
              py: 2,
              fontSize: '1.1rem',
              fontWeight: 600,
              borderRadius: 3,
              textTransform: 'none',
              boxShadow: '0 8px 25px rgba(184, 134, 11, 0.3)',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'linear-gradient(135deg, #B8860B, #DAA520)',
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 35px rgba(184, 134, 11, 0.4)',
              },
            }}
          >
            Start Chatting
          </Button>
        </Box>
      </Fade>

      {/* Quick Actions */}
      <Box sx={{ mb: 8 }}>
        <Typography
          variant="h3"
          sx={{
            color: 'rgba(255, 255, 255, 0.9)',
            fontWeight: 700,
            mb: 4,
            textAlign: 'center',
          }}
        >
          Quick Actions
        </Typography>
        <Grid container spacing={4}>
          {quickActions.map((action, index) => (
            <Grid item xs={12} md={4} key={action.title}>
              <QuickActionButton
                {...action}
                delay={index * 200}
              />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Features */}
      <Box sx={{ mb: 8 }}>
        <Typography
          variant="h3"
          sx={{
            color: 'rgba(255, 255, 255, 0.9)',
            fontWeight: 700,
            mb: 2,
            textAlign: 'center',
          }}
        >
          Why Choose Horus?
        </Typography>
        <Typography
          variant="h6"
          sx={{
            color: 'rgba(255, 255, 255, 0.6)',
            fontWeight: 400,
            mb: 6,
            textAlign: 'center',
            maxWidth: '600px',
            mx: 'auto',
          }}
        >
          Experience the future of business intelligence with cutting-edge AI technology
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={feature.title}>
              <FeatureCard
                {...feature}
                delay={index * 300}
              />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Statistics */}
      <Fade in timeout={1200} style={{ transitionDelay: '800ms' }}>
        <Box
          sx={{
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 4,
            p: 6,
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '2px',
              background: 'linear-gradient(90deg, #DAA520, #B8860B, #DAA520)',
            },
          }}
        >
          <Typography
            variant="h4"
            sx={{
              color: 'rgba(255, 255, 255, 0.9)',
              fontWeight: 700,
              mb: 4,
            }}
          >
            Powered by Ancient Wisdom, Modern Technology
          </Typography>
          <Grid container spacing={4}>
            <Grid item xs={12} sm={4}>
              <Typography
                variant="h2"
                sx={{
                  background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 800,
                  mb: 1,
                }}
              >
                <AnimatedCounter end={100} suffix="%" />
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Local & Private
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography
                variant="h2"
                sx={{
                  background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 800,
                  mb: 1,
                }}
              >
                <AnimatedCounter end={5} suffix="s" />
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Query Response
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography
                variant="h2"
                sx={{
                  background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 800,
                  mb: 1,
                }}
              >
                <AnimatedCounter end={24} suffix="/7" />
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Always Available
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </Fade>
    </Container>
  );
};

export default HomePage;