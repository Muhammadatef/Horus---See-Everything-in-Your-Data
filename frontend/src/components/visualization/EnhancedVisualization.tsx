import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as ShowChartIcon,
  ScatterPlot as ScatterPlotIcon,
  TableChart as TableChartIcon,
  Speed as SpeedIcon,
  ExpandMore as ExpandMoreIcon,
  Lightbulb as LightbulbIcon,
  Recommend as RecommendIcon,
} from '@mui/icons-material';
import ReactECharts from 'echarts-for-react';

interface VisualizationData {
  type: string;
  config: any;
  insights: string[];
  data_summary: {
    rows: number;
    columns: number;
    chart_type: string;
    recommended_actions: string[];
  };
}

interface EnhancedVisualizationProps {
  visualization: VisualizationData;
  title?: string;
  showInsights?: boolean;
}

const EnhancedVisualization: React.FC<EnhancedVisualizationProps> = ({
  visualization,
  title,
  showInsights = true,
}) => {
  if (!visualization) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No visualization available
        </Typography>
      </Paper>
    );
  }

  const getChartIcon = (chartType: string) => {
    switch (chartType) {
      case 'bar_chart':
        return <BarChartIcon />;
      case 'pie_chart':
        return <PieChartIcon />;
      case 'line_chart':
        return <ShowChartIcon />;
      case 'scatter_plot':
        return <ScatterPlotIcon />;
      case 'metric_card':
        return <SpeedIcon />;
      case 'data_table':
        return <TableChartIcon />;
      default:
        return <TrendingUpIcon />;
    }
  };

  const renderMetricCard = () => {
    const { data } = visualization.config;
    
    return (
      <Card elevation={3} sx={{ mb: 2 }}>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Box display="flex" justifyContent="center" mb={2}>
            <SpeedIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          </Box>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {data.title}
          </Typography>
          <Typography 
            variant="h2" 
            color="primary" 
            sx={{ 
              fontWeight: 'bold', 
              my: 2,
              fontSize: { xs: '2rem', sm: '3rem', md: '4rem' }
            }}
          >
            {formatMetricValue(data.value, data.format)}
          </Typography>
          <Chip 
            label={`${data.format || 'number'} format`}
            variant="outlined" 
            size="small"
            sx={{ mt: 1 }}
          />
        </CardContent>
      </Card>
    );
  };

  const formatMetricValue = (value: any, format: string) => {
    if (typeof value !== 'number') return value;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(value);
      case 'percentage':
        return `${(value * 100).toFixed(1)}%`;
      case 'thousand':
        return `${(value / 1000).toFixed(1)}K`;
      case 'million':
        return `${(value / 1000000).toFixed(1)}M`;
      case 'decimal':
        return value.toFixed(2);
      default:
        return value.toLocaleString();
    }
  };

  const renderEChart = () => {
    const config = { ...visualization.config };
    
    // Enhance the config with responsive design
    const responsiveConfig = {
      ...config,
      responsive: true,
      maintainAspectRatio: false,
      media: [
        {
          query: { maxWidth: 600 },
          option: {
            grid: { left: '10%', right: '10%', bottom: '20%' },
            legend: { orient: 'horizontal', bottom: 0 }
          }
        }
      ]
    };
    
    return (
      <Box sx={{ height: { xs: 300, sm: 400, md: 500 }, width: '100%' }}>
        <ReactECharts 
          option={responsiveConfig} 
          style={{ height: '100%', width: '100%' }}
          opts={{ renderer: 'svg' }}
        />
      </Box>
    );
  };

  const renderDataTable = () => {
    const { columns, data, pagination } = visualization.config;
    
    return (
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Data Results</Typography>
          <Typography variant="caption" color="text.secondary">
            {data.length} rows × {columns.length} columns
          </Typography>
        </Box>
        
        <Box sx={{ 
          maxHeight: 400, 
          overflow: 'auto',
          '& table': { minWidth: 650 }
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ position: 'sticky', top: 0, backgroundColor: '#f5f5f5' }}>
              <tr>
                {columns.map((col: any, index: number) => (
                  <th key={index} style={{ 
                    padding: '12px', 
                    textAlign: 'left', 
                    borderBottom: '1px solid #ddd',
                    fontWeight: 'bold'
                  }}>
                    {col.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 100).map((row: any, rowIndex: number) => (
                <tr key={rowIndex} style={{ 
                  cursor: 'pointer'
                }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                  {columns.map((col: any, colIndex: number) => (
                    <td key={colIndex} style={{ 
                      padding: '8px 12px', 
                      borderBottom: '1px solid #eee'
                    }}>
                      {row[col.key]?.toString() || '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Box>
      </Paper>
    );
  };

  const renderMainVisualization = () => {
    switch (visualization.type) {
      case 'metric':
        return renderMetricCard();
      case 'table':
        return renderDataTable();
      case 'empty':
        return (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Data Available
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload data or refine your query to see visualizations
            </Typography>
          </Paper>
        );
      default:
        return (
          <Paper sx={{ p: 2 }}>
            {renderEChart()}
          </Paper>
        );
    }
  };

  return (
    <Box>
      {/* Header */}
      {title && (
        <Box display="flex" alignItems="center" mb={2}>
          {getChartIcon(visualization.type)}
          <Typography variant="h5" sx={{ ml: 1, fontWeight: 'medium' }}>
            {title}
          </Typography>
          <Chip 
            label={visualization.type.replace('_', ' ')}
            size="small"
            variant="outlined"
            sx={{ ml: 2 }}
          />
        </Box>
      )}

      {/* Main Visualization */}
      {renderMainVisualization()}

      {/* Data Summary */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Data Summary
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>{visualization.data_summary.rows.toLocaleString()}</strong> rows
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>{visualization.data_summary.columns}</strong> columns
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Chart Type
              </Typography>
              <Box display="flex" alignItems="center">
                {getChartIcon(visualization.data_summary.chart_type)}
                <Typography variant="body2" sx={{ ml: 1 }}>
                  {visualization.data_summary.chart_type.replace('_', ' ')}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Insights and Recommendations */}
      {showInsights && (
        <Box sx={{ mt: 3 }}>
          {/* Insights */}
          {visualization.insights && visualization.insights.length > 0 && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center">
                  <LightbulbIcon sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography variant="h6">Data Insights</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {visualization.insights.map((insight, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <LightbulbIcon fontSize="small" color="action" />
                      </ListItemIcon>
                      <ListItemText primary={insight} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Recommendations */}
          {visualization.data_summary.recommended_actions && 
           visualization.data_summary.recommended_actions.length > 0 && (
            <Accordion sx={{ mt: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center">
                  <RecommendIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6">Recommended Actions</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {visualization.data_summary.recommended_actions.map((action, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <RecommendIcon fontSize="small" color="action" />
                      </ListItemIcon>
                      <ListItemText primary={action} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}
        </Box>
      )}
    </Box>
  );
};

export default EnhancedVisualization;