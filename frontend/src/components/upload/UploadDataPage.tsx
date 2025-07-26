import React, { useState } from 'react';
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
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { uploadApi, dataApi, formatFileSize, formatDate } from '../../services/api';

const UploadDataPage: React.FC = () => {
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const queryClient = useQueryClient();

  // Get upload history
  const { data: dataSources, isLoading: sourcesLoading } = useQuery(
    'dataSources',
    dataApi.getSources
  );

  // Upload mutation
  const uploadMutation = useMutation(uploadApi.uploadFile, {
    onSuccess: (data) => {
      setUploadStatus(`Upload successful: ${data.message}`);
      setUploadProgress(100);
      // Refetch data sources
      queryClient.invalidateQueries('dataSources');
      queryClient.invalidateQueries('datasets');
    },
    onError: (error: any) => {
      setUploadStatus(`Upload failed: ${error.response?.data?.detail || error.message}`);
      setUploadProgress(0);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation(dataApi.deleteDataset, {
    onSuccess: () => {
      queryClient.invalidateQueries('dataSources');
      queryClient.invalidateQueries('datasets');
    },
  });

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadStatus('Uploading file...');
    setUploadProgress(25);
    
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
      case 'processing':
        return <InfoIcon />;
      case 'failed':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Data
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload your data files to start analyzing. Supported formats: CSV, Excel, JSON, Parquet
      </Typography>

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
            {uploadProgress}% complete
          </Typography>
        </Paper>
      )}

      {/* Upload Status */}
      {uploadStatus && (
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
                      color={getStatusColor(source.status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
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
                        // Navigate to query page with this dataset
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

      {/* Upload Instructions */}
      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Upload Instructions
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemIcon>
              <CheckIcon color="success" />
            </ListItemIcon>
            <ListItemText
              primary="Supported Formats"
              secondary="CSV, Excel (.xls, .xlsx), JSON, Parquet files"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <CheckIcon color="success" />
            </ListItemIcon>
            <ListItemText
              primary="Automatic Processing"
              secondary="Files are automatically cleaned, validated, and prepared for analysis"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <CheckIcon color="success" />
            </ListItemIcon>
            <ListItemText
              primary="Instant Analysis"
              secondary="Once processed, you can immediately start asking questions about your data"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <CheckIcon color="success" />
            </ListItemIcon>
            <ListItemText
              primary="Local Storage"
              secondary="All data stays on your machine - complete privacy and security"
            />
          </ListItem>
        </List>
      </Paper>
    </Box>
  );
};

export default UploadDataPage;