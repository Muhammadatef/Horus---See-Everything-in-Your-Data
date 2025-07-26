import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
} from '@mui/material';
import ReactECharts from 'echarts-for-react';

interface VisualizationConfig {
  type: string;
  title: string;
  data: any[];
  description?: string;
  // Chart-specific properties
  category_column?: string;
  value_column?: string;
  x_column?: string;
  y_column?: string;
  columns?: string[];
  // Metric-specific properties
  value?: number | string;
  format?: string;
}

interface ChartVisualizationProps {
  config: VisualizationConfig;
}

const ChartVisualization: React.FC<ChartVisualizationProps> = ({ config }) => {
  if (!config) return null;

  const renderMetric = () => {
    const { value, format, title, description } = config;
    
    let displayValue = value;
    
    if (format === 'currency' && typeof value === 'number') {
      displayValue = `$${value.toFixed(2)}`;
    } else if (format === 'number' && typeof value === 'number') {
      displayValue = value.toLocaleString();
    }

    return (
      <Card elevation={3} className="metric-card">
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h2" color="primary" sx={{ fontWeight: 'bold', my: 2 }}>
            {displayValue}
          </Typography>
          {description && (
            <Typography variant="body2" color="text.secondary">
              {description}
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderPieChart = () => {
    const { data, category_column, value_column, title } = config;
    
    if (!data || !category_column || !value_column) return null;

    const chartData = data.map(item => ({
      name: item[category_column],
      value: item[value_column],
    }));

    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b} : {c} ({d}%)',
      },
      legend: {
        bottom: '5%',
        left: 'center',
      },
      series: [
        {
          name: title,
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          data: chartData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
          label: {
            show: true,
            formatter: '{b}: {c}',
          },
        },
      ],
      color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4'],
    };

    return (
      <div className="chart-container">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    );
  };

  const renderBarChart = () => {
    const { data, x_column, y_column, title } = config;
    
    if (!data || !x_column || !y_column) return null;

    const categories = data.map(item => item[x_column]);
    const values = data.map(item => item[y_column]);

    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: {
          rotate: categories.some(cat => String(cat).length > 8) ? 45 : 0,
        },
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: y_column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#5470c6',
          },
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
    };

    return (
      <div className="chart-container">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    );
  };

  const renderLineChart = () => {
    const { data, x_column, y_column, title } = config;
    
    if (!data || !x_column || !y_column) return null;

    const categories = data.map(item => item[x_column]);
    const values = data.map(item => item[y_column]);

    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: categories,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: y_column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
          type: 'line',
          data: values,
          smooth: true,
          lineStyle: {
            color: '#5470c6',
            width: 3,
          },
          itemStyle: {
            color: '#5470c6',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
                { offset: 1, color: 'rgba(84, 112, 198, 0.0)' },
              ],
            },
          },
        },
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
    };

    return (
      <div className="chart-container">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    );
  };

  const renderScatterPlot = () => {
    const { data, x_column, y_column, title } = config;
    
    if (!data || !x_column || !y_column) return null;

    const scatterData = data.map(item => [item[x_column], item[y_column]]);

    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: `{a}<br/>${x_column}: {c0}<br/>${y_column}: {c1}`,
      },
      xAxis: {
        type: 'value',
        name: x_column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        nameLocation: 'center',
        nameGap: 25,
      },
      yAxis: {
        type: 'value',
        name: y_column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        nameLocation: 'center',
        nameGap: 40,
      },
      series: [
        {
          name: title,
          type: 'scatter',
          data: scatterData,
          itemStyle: {
            color: '#5470c6',
          },
          symbolSize: 8,
        },
      ],
      grid: {
        left: '10%',
        right: '4%',
        bottom: '10%',
        containLabel: true,
      },
    };

    return (
      <div className="chart-container">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    );
  };

  const renderTable = () => {
    const { data, columns, title } = config;
    
    if (!data || !columns) return null;

    const displayColumns = columns.slice(0, 8); // Limit columns for readability
    const displayData = data.slice(0, 100); // Limit rows for performance

    return (
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">{title}</Typography>
          <Typography variant="caption" color="text.secondary">
            Showing {displayData.length} rows of {data.length} total
            {columns.length > displayColumns.length && 
              ` • ${displayColumns.length} of ${columns.length} columns`
            }
          </Typography>
        </Box>
        
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                {displayColumns.map((column, index) => (
                  <TableCell key={index} sx={{ fontWeight: 'bold' }}>
                    {column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {displayData.map((row, rowIndex) => (
                <TableRow key={rowIndex} hover>
                  {displayColumns.map((column, colIndex) => (
                    <TableCell key={colIndex}>
                      {row[column]?.toString() || '—'}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  };

  const renderVisualization = () => {
    switch (config.type) {
      case 'metric':
        return renderMetric();
      case 'pie':
        return renderPieChart();
      case 'bar':
        return renderBarChart();
      case 'line':
        return renderLineChart();
      case 'scatter':
        return renderScatterPlot();
      case 'table':
        return renderTable();
      default:
        return (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Visualization type "{config.type}" not supported
            </Typography>
          </Paper>
        );
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      {renderVisualization()}
      {config.description && config.type !== 'metric' && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', textAlign: 'center', mt: 1 }}
        >
          {config.description}
        </Typography>
      )}
    </Box>
  );
};

export default ChartVisualization;