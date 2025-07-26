import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  LinearProgress,
  Alert,
  Divider,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Fade,
  Skeleton,
} from '@mui/material';
import {
  Send as SendIcon,
  History as HistoryIcon,
  Lightbulb as LightbulbIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon,
  SmartToy as SmartToyIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { dataApi, queryApi } from '../../services/api';
import { useWebSocket } from '../../hooks/useWebSocket';
import EnhancedVisualization from '../visualization/EnhancedVisualization';

interface QueryUpdate {
  type: string;
  query_id: string;
  status: string;
  progress: number;
  message: string;
  results?: any;
}

const RealTimeQueryPage: React.FC = () => {
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [queryStatus, setQueryStatus] = useState<string>('');
  const [queryProgress, setQueryProgress] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [processingSteps, setProcessingSteps] = useState<QueryUpdate[]>([]);
  const [showSQL, setShowSQL] = useState(false);

  const queryClient = useQueryClient();

  // WebSocket connection for real-time query updates
  const { isConnected, lastMessage } = useWebSocket('default', {
    onMessage: (message) => {
      if (message.type === 'query_update') {
        handleQueryUpdate(message as QueryUpdate);
      }
    },
  });

  // Get available datasets
  const { data: datasets, isLoading: datasetsLoading } = useQuery(
    'datasets',
    dataApi.getDatasets
  );

  // Get query history for selected dataset
  const { data: queryHistory } = useQuery(
    ['queryHistory', selectedDataset],
    () => selectedDataset ? queryApi.getHistory(selectedDataset) : [],
    { enabled: !!selectedDataset }
  );

  // Get query suggestions
  const { data: querySuggestions } = useQuery(
    ['querySuggestions', selectedDataset, question],
    () => selectedDataset ? queryApi.getSuggestions(selectedDataset) : { suggestions: [] },
    { 
      enabled: !!selectedDataset,
      staleTime: 30000 // Cache for 30 seconds
    }
  );

  // Query mutation
  const queryMutation = useMutation(queryApi.askQuestion, {
    onSuccess: (data) => {
      setQueryResult(data);
      setIsProcessing(false);
      setQueryProgress(100);
      setQueryStatus('Query completed successfully!');
      queryClient.invalidateQueries(['queryHistory', selectedDataset]);
    },
    onError: (error: any) => {
      setIsProcessing(false);
      setQueryProgress(0);
      setQueryStatus(`Query failed: ${error.response?.data?.detail || error.message}`);
      setProcessingSteps([]);
    },
  });

  const handleQueryUpdate = (update: QueryUpdate) => {
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

    setQueryProgress(update.progress);
    setQueryStatus(update.message);

    // Handle completion
    if (update.status === 'completed' && update.results) {
      setQueryResult(update.results);
      setIsProcessing(false);
      queryClient.invalidateQueries(['queryHistory', selectedDataset]);
    }

    // Handle errors
    if (update.status === 'failed') {
      setIsProcessing(false);
      setQueryStatus(`❌ Query failed: ${update.message}`);
    }
  };

  const handleSubmitQuery = () => {
    if (!selectedDataset || !question.trim()) return;

    setIsProcessing(true);
    setQueryProgress(0);
    setQueryResult(null);
    setProcessingSteps([]);
    setQueryStatus('Starting query processing...');

    queryMutation.mutate({
      dataset_id: selectedDataset,
      question: question.trim()
    });
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion);
  };

  const handleHistoryClick = (historyItem: any) => {
    setQuestion(historyItem.question);
    if (historyItem.results) {
      setQueryResult(historyItem);
    }
  };

  // Update suggestions when query suggestions change
  useEffect(() => {
    if (querySuggestions?.suggestions) {
      setSuggestions(querySuggestions.suggestions);
    }
  }, [querySuggestions]);

  const renderQueryInterface = () => (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom display="flex" alignItems="center">
        <SmartToyIcon sx={{ mr: 1 }} />
        Ask Questions About Your Data
      </Typography>

      {/* Dataset Selection */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Typography variant="subtitle2" gutterBottom>
            Select Dataset
          </Typography>
          {datasetsLoading ? (
            <Skeleton variant="rectangular" height={56} />
          ) : (
            <Grid container spacing={1}>
              {datasets?.map((dataset: any) => (
                <Grid item key={dataset.id}>
                  <Chip
                    label={dataset.name}
                    onClick={() => setSelectedDataset(dataset.id)}
                    color={selectedDataset === dataset.id ? 'primary' : 'default'}
                    variant={selectedDataset === dataset.id ? 'filled' : 'outlined'}
                    clickable
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>
      </Grid>

      {/* Question Input */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          multiline
          minRows={3}
          maxRows={6}
          label="Ask a question about your data..."
          placeholder="e.g., How many active users do we have? Show me sales trends over time."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={!selectedDataset || isProcessing}
          sx={{ mb: 2 }}
        />
        
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={handleSubmitQuery}
              disabled={!selectedDataset || !question.trim() || isProcessing}
              sx={{ mr: 2 }}
            >
              {isProcessing ? 'Processing...' : 'Ask Question'}
            </Button>
            
            <Chip 
              label={isConnected ? "Real-time updates active" : "Offline mode"}
              color={isConnected ? "success" : "warning"}
              variant="outlined"
              size="small"
            />
          </Box>

          {queryResult && (
            <IconButton
              onClick={() => setShowSQL(!showSQL)}
              color="primary"
              title="Toggle SQL view"
            >
              <CodeIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Processing Status */}
      {isProcessing && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" gutterBottom>
            {queryStatus}
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={queryProgress} 
            sx={{ mb: 1 }} 
          />
          <Typography variant="caption" color="text.secondary">
            {queryProgress}% complete
          </Typography>
        </Box>
      )}

      {/* Processing Steps */}
      {processingSteps.length > 0 && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">
              Processing Details ({processingSteps.length} steps)
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {processingSteps.map((step, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={step.message}
                    secondary={`${step.progress}% - ${step.status}`}
                  />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
    </Paper>
  );

  const renderSuggestions = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom display="flex" alignItems="center">
          <LightbulbIcon sx={{ mr: 1 }} />
          Suggested Questions
        </Typography>
        
        {suggestions.length === 0 && selectedDataset ? (
          <Typography variant="body2" color="text.secondary">
            No suggestions available. Try selecting a dataset first.
          </Typography>
        ) : (
          <List dense>
            {suggestions.slice(0, 8).map((suggestion, index) => (
              <ListItem key={index} disablePadding>
                <ListItemButton
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={isProcessing}
                >
                  <ListItemText primary={suggestion} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );

  const renderQueryHistory = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom display="flex" alignItems="center">
          <HistoryIcon sx={{ mr: 1 }} />
          Recent Questions
        </Typography>
        
        {!queryHistory || queryHistory.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No previous questions. Ask your first question above!
          </Typography>
        ) : (
          <List dense>
            {queryHistory.slice(0, 10).map((item: any, index: number) => (
              <ListItem key={index} disablePadding>
                <ListItemButton
                  onClick={() => handleHistoryClick(item)}
                  disabled={isProcessing}
                >
                  <ListItemText
                    primary={item.question}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          label={item.success ? 'Success' : 'Failed'}
                          color={item.success ? 'success' : 'error'}
                          size="small"
                        />
                        <Typography variant="caption">
                          {item.execution_time_ms}ms
                        </Typography>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );

  const renderQueryResults = () => {
    if (!queryResult) return null;

    return (
      <Fade in={true}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom display="flex" alignItems="center">
            <AnalyticsIcon sx={{ mr: 1 }} />
            Query Results
          </Typography>

          {/* Natural Language Answer */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body1">
              <strong>Answer:</strong> {queryResult.answer}
            </Typography>
          </Alert>

          {/* SQL Query (collapsible) */}
          {queryResult.sql && (
            <Accordion expanded={showSQL} onChange={() => setShowSQL(!showSQL)}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="body2">Generated SQL Query</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.85rem' }}>
                    {queryResult.sql}
                  </Typography>
                </Paper>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Visualization */}
          {queryResult.visualization && (
            <Box sx={{ mt: 3 }}>
              <EnhancedVisualization
                visualization={queryResult.visualization}
                title="Data Visualization"
                showInsights={true}
              />
            </Box>
          )}

          {/* Execution Metadata */}
          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Execution Time
                </Typography>
                <Typography variant="body2">
                  {queryResult.execution_time_ms}ms
                </Typography>
              </Grid>
              {queryResult.results && (
                <>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Rows Returned
                    </Typography>
                    <Typography variant="body2">
                      {queryResult.results.data?.length || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Columns
                    </Typography>
                    <Typography variant="body2">
                      {queryResult.results.columns?.length || 0}
                    </Typography>
                  </Grid>
                </>
              )}
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  label={queryResult.success ? 'Success' : 'Failed'}
                  color={queryResult.success ? 'success' : 'error'}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Fade>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Query Your Data
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Ask questions about your data in natural language and get instant insights with visualizations.
      </Typography>

      <Grid container spacing={3}>
        {/* Main Query Interface */}
        <Grid item xs={12} lg={8}>
          {renderQueryInterface()}
          {renderQueryResults()}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {renderSuggestions()}
          {renderQueryHistory()}
        </Grid>
      </Grid>
    </Box>
  );
};

export default RealTimeQueryPage;