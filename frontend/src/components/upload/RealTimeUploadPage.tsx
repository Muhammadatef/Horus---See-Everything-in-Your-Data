import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Collapse,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { uploadApi, dataApi, formatFileSize, formatDate } from '../../services/api';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ProcessingUpdate {
  type: string;
  data_source_id: string;
  status: string;
  progress: number;
  message: string;
  details: any;
  timestamp: string;
}

const RealTimeUploadPage: React.FC = () => {
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [processingSteps, setProcessingSteps] = useState<ProcessingUpdate[]>([]);
  const [currentDataSourceId, setCurrentDataSourceId] = useState<string | null>(null);
  const [showProcessingDetails, setShowProcessingDetails] = useState(false);
  const [processingInsights, setProcessingInsights] = useState<any>(null);
  const [showInsightsDialog, setShowInsightsDialog] = useState(false);
  
  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket('default', {
    onMessage: (message) => {
      if (message.type === 'data_processing_update') {
        handleProcessingUpdate(message as ProcessingUpdate);
      }
    },
    onConnect: () => {
      console.log('Connected to real-time updates');
    },
  });

  // Get upload history
  const { data: dataSources, isLoading: sourcesLoading } = useQuery(
    'dataSources',
    dataApi.getSources
  );

  // Upload mutation
  const uploadMutation = useMutation(uploadApi.uploadFile, {
    onSuccess: (data) => {
      setUploadStatus(`Upload successful: ${data.message}`);
      setUploadProgress(25);
      setCurrentDataSourceId(data.data_source_id);
      // Reset processing steps for new upload
      setProcessingSteps([]);
      // Refetch data sources
      queryClient.invalidateQueries('dataSources');
      queryClient.invalidateQueries('datasets');
    },
    onError: (error: any) => {
      setUploadStatus(`Upload failed: ${error.response?.data?.detail || error.message}`);
      setUploadProgress(0);
      setProcessingSteps([]);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation(dataApi.deleteDataset, {
    onSuccess: () => {
      queryClient.invalidateQueries('dataSources');
      queryClient.invalidateQueries('datasets');
    },
  });

  const handleProcessingUpdate = (update: ProcessingUpdate) => {
    setProcessingSteps(prev => {
      const newSteps = [...prev];
      const existingIndex = newSteps.findIndex(step => step.status === update.status);
      
      if (existingIndex >= 0) {
        newSteps[existingIndex] = update;
      } else {
        newSteps.push(update);
      }
      
      return newSteps.sort((a, b) => a.progress - b.progress);
    });

    setUploadProgress(update.progress);
    setUploadStatus(update.message);

    // Handle completion
    if (update.status === 'completed') {
      setUploadStatus('✅ Data processing completed successfully!');
      queryClient.invalidateQueries('dataSources');
      queryClient.invalidateQueries('datasets');
    }

    // Handle insights
    if (update.status === 'insights_ready' && update.details?.insights) {
      setProcessingInsights(update.details.insights);
    }

    // Handle errors
    if (update.status === 'failed') {
      setUploadStatus(`❌ Processing failed: ${update.message}`);
    }
  };

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadStatus('Uploading file...');
    setUploadProgress(10);
    setProcessingSteps([]);
    setProcessingInsights(null);
    
    uploadMutation.mutate(file);
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json'],
      'application/parquet': ['.parquet'],
    },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024, // 100MB
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
      case 'analyzing':
      case 'reading':
      case 'cleaning':
      case 'analyzing_schema':
      case 'storing':
      case 'generating_insights':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon />;
      case 'failed':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const renderProcessingSteps = () => {
    if (processingSteps.length === 0) return null;

    return (
      <Paper sx={{ mt: 3, p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" display="flex" alignItems="center">
            <TimelineIcon sx={{ mr: 1 }} />
            Processing Timeline
          </Typography>
          <IconButton
            onClick={() => setShowProcessingDetails(!showProcessingDetails)}
            size="small"
          >
            {showProcessingDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Stepper orientation="vertical" activeStep={processingSteps.length - 1}>
          {processingSteps.map((step, index) => (
            <Step key={index} completed={step.status === 'completed'}>
              <StepLabel
                icon={getStatusIcon(step.status)}
                StepIconProps={{
                  style: { 
                    color: step.status === 'completed' ? '#4caf50' : 
                           step.status === 'failed' ? '#f44336' : '#ff9800'
                  }
                }}
              >
                <Box display="flex" alignItems="center">
                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                    {step.message}
                  </Typography>
                  <Chip 
                    label={`${step.progress}%`}
                    size="small"
                    color={getStatusColor(step.status) as any}
                    sx={{ ml: 1 }}
                  />
                </Box>
              </StepLabel>
              
              <Collapse in={showProcessingDetails}>
                <StepContent>
                  {step.details && Object.keys(step.details).length > 0 && (
                    <Box sx={{ mt: 1, ml: 2 }}>
                      {Object.entries(step.details).map(([key, value]) => (
                        <Typography key={key} variant="caption" display="block" color="text.secondary">
                          {key.replace(/_/g, ' ')}: {String(value)}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  <Typography variant="caption" color="text.secondary" display="block">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </Typography>
                </StepContent>
              </Collapse>
            </Step>
          ))}
        </Stepper>

        {processingInsights && (
          <Box sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<AnalyticsIcon />}
              onClick={() => setShowInsightsDialog(true)}
              color="info"
            >
              View Data Insights
            </Button>
          </Box>
        )}
      </Paper>
    );
  };

  const renderInsightsDialog = () => (
    <Dialog 
      open={showInsightsDialog} 
      onClose={() => setShowInsightsDialog(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>Data Analysis Insights</DialogTitle>
      <DialogContent>
        {processingInsights && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>Overview</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Total Rows" 
                        secondary={processingInsights.overview.total_rows.toLocaleString()} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Total Columns" 
                        secondary={processingInsights.overview.total_columns} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Memory Usage" 
                        secondary={`${processingInsights.overview.memory_usage_mb} MB`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Completeness Score" 
                        secondary={`${processingInsights.overview.completeness_score}%`} 
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>Column Types</Typography>
                  <List dense>
                    {Object.entries(processingInsights.column_types).map(([type, count]) => (
                      <ListItem key={type}>
                        <ListItemText 
                          primary={type.replace('_', ' ')} 
                          secondary={`${count} columns`} 
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>Business Insights</Typography>
                  <List>
                    {processingInsights.business_insights.map((insight: string, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <AnalyticsIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={insight} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {processingInsights.recommendations.length > 0 && (
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Recommendations</Typography>
                    <List>
                      {processingInsights.recommendations.map((rec: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <InfoIcon fontSize="small" color="info" />
                          </ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowInsightsDialog(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Data
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload your data files to start analyzing. Supported formats: CSV, Excel, JSON, Parquet
      </Typography>

      {/* Connection Status */}
      <Alert 
        severity={isConnected ? "success" : "warning"} 
        sx={{ mb: 2 }}
        variant="outlined"
      >
        Real-time updates: {isConnected ? "Connected" : "Disconnected"}
      </Alert>

      {/* Upload Area */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          mb: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.2s',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive
            ? 'Drop your file here...'
            : 'Drag & drop a file here, or click to select'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Supported: CSV, Excel (.xls, .xlsx), JSON, Parquet • Max size: 100MB
        </Typography>
        <Button
          variant="contained"
          sx={{ mt: 2 }}
          disabled={uploadMutation.isLoading}
        >
          Select File
        </Button>
      </Paper>

      {/* Upload Progress */}
      {uploadMutation.isLoading && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Processing Upload...
          </Typography>
          <LinearProgress
            variant="determinate"
            value={uploadProgress}
            sx={{ mb: 2 }}
          />
          <Typography variant="body2" color="text.secondary">
            {uploadProgress}% complete - {uploadStatus}
          </Typography>
        </Paper>
      )}

      {/* Processing Steps */}
      {renderProcessingSteps()}

      {/* Upload Status */}
      {uploadStatus && !uploadMutation.isLoading && (
        <Alert
          severity={uploadMutation.isError ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setUploadStatus('')}
        >
          {uploadStatus}
        </Alert>
      )}

      {/* Sample Data Notice */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Try the demo:</strong> Upload the sample file from{' '}
          <code>data/samples/user_analytics.csv</code> to test the platform with user data.{' '}
          You can then ask questions like "How many active users do we have?"
        </Typography>
      </Alert>

      {/* Uploaded Files */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Your Data Sources
      </Typography>

      {sourcesLoading ? (
        <LinearProgress sx={{ mb: 3 }} />
      ) : !dataSources || dataSources.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No data sources uploaded yet. Upload your first file to get started!
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {dataSources.map((source) => (
            <Grid item xs={12} md={6} lg={4} key={source.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" noWrap sx={{ flex: 1, mr: 1 }}>
                      {source.name}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(source.status)}
                      label={source.status}
                      color={getStatusColor(source.status) as any}
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {source.filename}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Type: {source.file_type}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Uploaded: {formatDate(source.upload_date)}
                    </Typography>
                    {source.row_count && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {source.row_count.toLocaleString()} rows, {source.column_count} columns
                      </Typography>
                    )}
                  </Box>

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      disabled={source.status !== 'completed'}
                      onClick={() => {
                        window.location.href = `/query?dataset=${source.id}`;
                      }}
                    >
                      Query Data
                    </Button>
                    
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => {
                        if (window.confirm('Are you sure you want to delete this dataset?')) {
                          deleteMutation.mutate(source.id);
                        }
                      }}
                      disabled={deleteMutation.isLoading}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Insights Dialog */}
      {renderInsightsDialog()}
    </Box>
  );
};

export default RealTimeUploadPage;