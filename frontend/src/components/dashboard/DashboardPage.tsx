import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  AttachMoney as MoneyIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

const DashboardPage: React.FC = () => {
  // This is a placeholder for the dashboard
  // In a full implementation, this would show saved queries, visualizations, and dashboards

  const mockMetrics = [
    {
      title: 'Total Datasets',
      value: '3',
      icon: <AnalyticsIcon />,
      color: '#1976d2',
    },
    {
      title: 'Questions Asked',
      value: '47',
      icon: <TrendingUpIcon />,
      color: '#2e7d32',
    },
    {
      title: 'Active Users',
      value: '15',
      icon: <PeopleIcon />,
      color: '#ed6c02',
    },
    {
      title: 'Avg Response Time',
      value: '2.3s',
      icon: <MoneyIcon />,
      color: '#9c27b0',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Overview of your data analysis activities and insights.
      </Typography>

      {/* Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {mockMetrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h4" color={metric.color} fontWeight="bold">
                      {metric.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metric.title}
                    </Typography>
                  </Box>
                  <Box sx={{ color: metric.color }}>
                    {metric.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Coming Soon Notice */}
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Dashboard Coming Soon
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          This dashboard will show your saved queries, visualizations, and key metrics from your data analysis.
        </Typography>
        
        <Alert severity="info" sx={{ mt: 3, textAlign: 'left' }}>
          <Typography variant="body2">
            <strong>Planned Features:</strong>
            <br />
            • Save and organize your favorite queries
            <br />
            • Create custom dashboards with multiple visualizations
            <br />
            • Set up automated reports and alerts
            <br />
            • Export dashboards as PDFs or images
            <br />
            • Share insights with your team
          </Typography>
        </Alert>
      </Paper>
    </Box>
  );
};

export default DashboardPage;