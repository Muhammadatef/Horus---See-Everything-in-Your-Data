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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  Lightbulb as LightbulbIcon,
  History as HistoryIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSearchParams } from 'react-router-dom';
import { dataApi, queryApi, QueryRequest, QueryResponse } from '../../services/api';
import ChartVisualization from '../visualization/ChartVisualization';

const QueryDataPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null);

  // Get datasets
  const { data: datasets, isLoading: datasetsLoading } = useQuery(
    'datasets',
    dataApi.getDatasets
  );

  // Get suggestions for selected dataset
  const { data: suggestions } = useQuery(
    ['suggestions', selectedDataset],
    () => queryApi.getSuggestions(selectedDataset),
    {
      enabled: !!selectedDataset,
    }
  );

  // Get query history for selected dataset
  const { data: queryHistory } = useQuery(
    ['queryHistory', selectedDataset],
    () => queryApi.getHistory(selectedDataset),
    {
      enabled: !!selectedDataset,
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  // Query mutation
  const queryMutation = useMutation(queryApi.askQuestion, {
    onSuccess: (data) => {
      setCurrentResponse(data);
      // Refresh query history
      queryClient.invalidateQueries(['queryHistory', selectedDataset]);
    },
  });

  // Handle dataset selection from URL params
  useEffect(() => {
    const datasetParam = searchParams.get('dataset');
    if (datasetParam && datasets) {
      const dataset = datasets.find(d => d.id === datasetParam);
      if (dataset) {
        setSelectedDataset(dataset.id);
      }
    } else if (datasets && datasets.length > 0 && !selectedDataset) {
      // Auto-select first dataset if none selected
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets, searchParams, selectedDataset]);

  const handleSubmitQuestion = () => {
    if (!selectedDataset || !question.trim()) return;

    const request: QueryRequest = {
      dataset_id: selectedDataset,
      question: question.trim(),
    };

    queryMutation.mutate(request);
  };

  const handleSuggestionClick = (suggestionText: string) => {
    setQuestion(suggestionText);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmitQuestion();
    }
  };

  if (datasetsLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Query Data
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (!datasets || datasets.length === 0) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Query Data
        </Typography>
        <Alert severity="info">
          <Typography>
            No datasets available. Please{' '}
            <Button
              variant="text"
              onClick={() => window.location.href = '/upload'}
              sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
            >
              upload some data
            </Button>{' '}
            first to start asking questions.
          </Typography>
        </Alert>
      </Box>
    );
  }

  const selectedDatasetInfo = datasets.find(d => d.id === selectedDataset);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Query Data
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Ask questions about your data in natural language and get instant insights with visualizations.
      </Typography>

      {/* Dataset Selection */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Select Dataset</InputLabel>
            <Select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              label="Select Dataset"
            >
              {datasets.map((dataset) => (
                <MenuItem key={dataset.id} value={dataset.id}>
                  {dataset.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {selectedDatasetInfo && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent sx={{ py: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Selected Dataset
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedDatasetInfo.name}
                </Typography>
                {selectedDatasetInfo.description && (
                  <Typography variant="caption" color="text.secondary">
                    {selectedDatasetInfo.description}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Question Input */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Ask a Question
        </Typography>
        
        <Box display="flex" gap={2} alignItems="flex-end">
          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={4}
            placeholder="e.g., How many active users do we have?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!selectedDataset || queryMutation.isLoading}
            sx={{ mb: 0 }}
          />
          <Button
            variant="contained"
            onClick={handleSubmitQuestion}
            disabled={!selectedDataset || !question.trim() || queryMutation.isLoading}
            startIcon={<SendIcon />}
            sx={{ minWidth: 120, height: 'fit-content' }}
          >
            {queryMutation.isLoading ? 'Asking...' : 'Ask'}
          </Button>
        </Box>

        {queryMutation.isLoading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              Processing your question using local AI...
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Suggested Questions */}
      {suggestions && suggestions.suggestions && suggestions.suggestions.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" alignItems="center" mb={2}>
            <LightbulbIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">
              Suggested Questions
            </Typography>
          </Box>
          
          <Grid container spacing={1}>
            {suggestions.suggestions.map((suggestion: string, index: number) => (
              <Grid item key={index}>
                <Chip
                  label={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  clickable
                  variant="outlined"
                  sx={{
                    '&:hover': {
                      backgroundColor: 'primary.main',
                      color: 'white',
                    },
                  }}
                />
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Current Response */}
      {currentResponse && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Answer
          </Typography>
          
          {/* Question */}
          <Box sx={{ mb: 2, p: 2, backgroundColor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Question:
            </Typography>
            <Typography variant="body1">
              {currentResponse.question}
            </Typography>
          </Box>

          {/* Answer */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" color="primary" gutterBottom>
              {currentResponse.answer}
            </Typography>
            
            {!currentResponse.success && currentResponse.error_message && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {currentResponse.error_message}
              </Alert>
            )}
          </Box>

          {/* Visualization */}
          {currentResponse.success && currentResponse.visualization && (
            <Box sx={{ mb: 3 }}>
              <ChartVisualization config={currentResponse.visualization} />
            </Box>
          )}

          {/* Technical Details */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center">
                <CodeIcon sx={{ mr: 1 }} />
                <Typography>Technical Details</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Execution Time
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {currentResponse.execution_time_ms} ms
                  </Typography>
                </Grid>
                
                {currentResponse.sql && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Generated SQL
                    </Typography>
                    <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography
                        variant="body2"
                        component="pre"
                        sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}
                      >
                        {currentResponse.sql}
                      </Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Paper>
      )}

      {/* Query History */}
      {queryHistory && queryHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="center" mb={2}>
            <HistoryIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">
              Recent Questions
            </Typography>
          </Box>
          
          <List>
            {queryHistory.slice(0, 5).map((query: any, index: number) => (
              <React.Fragment key={query.id}>
                <ListItem
                  button
                  onClick={() => setQuestion(query.question)}
                  sx={{
                    borderRadius: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemText
                    primary={query.question}
                    secondary={
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" color="text.secondary">
                          {new Date(query.created_at).toLocaleString()}
                        </Typography>
                        <Chip
                          size="small"
                          label={query.success ? 'Success' : 'Failed'}
                          color={query.success ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </Box>
                    }
                  />
                </ListItem>
                {index < Math.min(queryHistory.length, 5) - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Demo Instructions */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Try these example questions:</strong>
          <br />
          • "How many active users do we have?"
          <br />
          • "Show me user distribution by region"  
          <br />
          • "What's our average monthly spending?"
          <br />
          • "How many premium users are there?"
        </Typography>
      </Alert>
    </Box>
  );
};

export default QueryDataPage;