import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Fade,
  CircularProgress,
  Menu,
  MenuItem,
  Divider,
  keyframes,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachIcon,
  Close as CloseIcon,
  UploadFile as UploadFileIcon,
  InsertChart as ChartIcon,
  TableChart as TableIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { dataApi, queryApi, uploadApi } from '../../services/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachedFile?: {
    name: string;
    id: string;
    type: string;
  };
  visualization?: any;
  isLoading?: boolean;
}

interface ChatInterfaceProps {
  onFileUpload?: (file: File) => void;
}

// Enhanced Egyptian animations for chat interface
const floatingGlow = keyframes`
  0%, 100% {
    transform: translateY(0px) scale(1);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-10px) scale(1.1);
    opacity: 1;
  }
`;

const shimmerText = keyframes`
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
`;

const pulseGold = keyframes`
  0%, 100% {
    box-shadow: 0 0 5px rgba(184, 134, 11, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(184, 134, 11, 0.8), 0 0 30px rgba(218, 165, 32, 0.4);
  }
`;

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onFileUpload }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m Horus, your AI business intelligence assistant. Upload a data file and ask me questions about your data, and I\'ll provide insights with visualizations.',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [datasetDialogOpen, setDatasetDialogOpen] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [attachMenuAnchor, setAttachMenuAnchor] = useState<null | HTMLElement>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Get available datasets
  const { data: datasets } = useQuery('datasets', dataApi.getDatasets);

  // Auto-select dataset if only one is available and none is selected
  useEffect(() => {
    if (datasets && datasets.length === 1 && !selectedDataset) {
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets, selectedDataset]);


  // Query mutation
  const queryMutation = useMutation(queryApi.askQuestion, {
    onSuccess: (data) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === 'loading' 
            ? {
                ...msg,
                id: Date.now().toString(),
                content: data.answer || 'Here are the results from your query.',
                isLoading: false,
                visualization: data.visualization,
              }
            : msg
        )
      );
    },
    onError: (error: any) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === 'loading' 
            ? {
                ...msg,
                id: Date.now().toString(),
                content: `Sorry, I couldn't process your query: ${error.response?.data?.detail || error.message}`,
                isLoading: false,
              }
            : msg
        )
      );
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    // Handle file upload first if there's an attached file
    if (attachedFile && !selectedDataset) {
      const uploadMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: inputValue,
        timestamp: new Date(),
        attachedFile: {
          name: attachedFile.name,
          id: 'uploading',
          type: attachedFile.type,
        },
      };
      setMessages(prev => [...prev, uploadMessage]);

      const loadingMessage: Message = {
        id: 'loading',
        type: 'assistant',
        content: 'Processing your file and analyzing your question...',
        timestamp: new Date(),
        isLoading: true,
      };
      setMessages(prev => [...prev, loadingMessage]);

      // Store the question to process after upload
      const questionToProcess = inputValue;
      setInputValue('');

      // Upload file and then process the question
      try {
        const uploadResult = await uploadApi.uploadFile(attachedFile);
        
        // Wait for processing and get the dataset
        setTimeout(async () => {
          try {
            const updatedDatasets = await dataApi.getDatasets();
            if (updatedDatasets && updatedDatasets.length > 0) {
              // Find dataset by filename match or take the most recent
              let targetDataset = updatedDatasets.find(ds => 
                ds.name.toLowerCase().includes(attachedFile?.name?.toLowerCase().replace('.csv', '') || '')
              );
              
              if (!targetDataset) {
                targetDataset = updatedDatasets[0]; // Most recent
              }
              
              setSelectedDataset(targetDataset.id);
              
              // Now process the original question
              try {
                const queryResult = await queryApi.askQuestion({
                  dataset_id: targetDataset.id,
                  question: questionToProcess,
                });

                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === 'loading' 
                      ? {
                          ...msg,
                          id: Date.now().toString(),
                          content: queryResult.answer || 'Here are the results from your query.',
                          isLoading: false,
                          visualization: queryResult.visualization,
                        }
                      : msg
                  )
                );
              } catch (queryError: any) {
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === 'loading' 
                      ? {
                          ...msg,
                          id: Date.now().toString(),
                          content: `I've processed your file successfully, but couldn't answer your question: ${queryError.response?.data?.detail || queryError.message}`,
                          isLoading: false,
                        }
                      : msg
                  )
                );
              }
            }
          } catch (error) {
            console.error('Error getting datasets after upload:', error);
            setMessages(prev => 
              prev.map(msg => 
                msg.id === 'loading' 
                  ? {
                      ...msg,
                      id: Date.now().toString(),
                      content: 'File uploaded successfully, but there was an error processing your question. Please try asking again.',
                      isLoading: false,
                    }
                  : msg
              )
            );
          }
        }, 4000); // Wait 4 seconds for processing
        
      } catch (uploadError: any) {
        setMessages(prev => 
          prev.map(msg => 
            msg.id === 'loading' 
              ? {
                  ...msg,
                  id: Date.now().toString(),
                  content: `Sorry, there was an error processing your file: ${uploadError.response?.data?.detail || uploadError.message}`,
                  isLoading: false,
                }
              : msg
          )
        );
      }
      
      setAttachedFile(null);
      return;
    }

    // Handle query
    if (selectedDataset) {
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: inputValue,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      const loadingMessage: Message = {
        id: 'loading',
        type: 'assistant',
        content: 'Analyzing your data...',
        timestamp: new Date(),
        isLoading: true,
      };
      setMessages(prev => [...prev, loadingMessage]);

      queryMutation.mutate({
        dataset_id: selectedDataset,
        question: inputValue,
      });

      setInputValue('');
    } else {
      // No dataset selected
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: inputValue,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      const responseMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Please upload a data file first or select an existing dataset so I can answer questions about your data.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, responseMessage]);
      setInputValue('');
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setAttachedFile(file);
      setAttachMenuAnchor(null);
    }
  };

  const handleDatasetSelect = (datasetId: string) => {
    setSelectedDataset(datasetId);
    setDatasetDialogOpen(false);
  };

  const renderVisualization = (visualization: any) => {
    if (!visualization) return null;

    const { type, config, insights, data_summary } = visualization;

    const renderChart = () => {
      if (type === 'kpi' || type === 'metric_card') {
        // Render KPI cards
        const kpiValue = config?.value || data_summary?.rows || 0;
        const kpiLabel = config?.label || 'Total Records';
        const kpiSubtitle = config?.subtitle || '';
        const kpiPercentage = config?.percentage;
        const kpiTotal = config?.total;
        
        return (
          <Box display="flex" gap={3} flexWrap="wrap">
            <Paper
              sx={{
                p: 4,
                minWidth: 280,
                background: 'linear-gradient(135deg, rgba(184, 134, 11, 0.2), rgba(218, 165, 32, 0.1))',
                border: '2px solid rgba(184, 134, 11, 0.4)',
                borderRadius: 4,
                textAlign: 'center',
                animation: `${pulseGold} 3s ease-in-out infinite`,
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '\"\"',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  background: 'linear-gradient(90deg, #DAA520, #B8860B, #FFD700)',
                },
              }}
            >
              <Typography
                variant="h1"
                sx={{
                  color: '#DAA520',
                  fontWeight: 900,
                  fontSize: '3.5rem',
                  textShadow: '0 0 20px rgba(184, 134, 11, 0.8)',
                  mb: 1,
                  lineHeight: 1,
                }}
              >
                {typeof kpiValue === 'number' ? kpiValue.toLocaleString() : kpiValue}
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  color: 'rgba(255, 255, 255, 0.95)',
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  fontWeight: 600,
                  mb: kpiSubtitle ? 1 : 0,
                }}
              >
                {kpiLabel}
              </Typography>
              {kpiSubtitle && (
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '1rem',
                    fontStyle: 'italic',
                  }}
                >
                  {kpiSubtitle}
                </Typography>
              )}
              {kpiPercentage !== undefined && (
                <Box
                  sx={{
                    mt: 2,
                    p: 2,
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: 2,
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <Typography
                    variant="h6"
                    sx={{
                      color: '#DAA520',
                      fontWeight: 'bold',
                    }}
                  >
                    {kpiPercentage}% Activation Rate
                  </Typography>
                </Box>
              )}
            </Paper>
            
            {/* Additional metrics if available */}
            {kpiTotal && kpiTotal !== kpiValue && (
              <Paper
                sx={{
                  p: 3,
                  minWidth: 200,
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(184, 134, 11, 0.05))',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: 3,
                  textAlign: 'center',
                }}
              >
                <Typography
                  variant="h2"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontWeight: 'bold',
                    mb: 1,
                  }}
                >
                  {kpiTotal.toLocaleString()}
                </Typography>
                <Typography
                  variant="h6"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  Total Users
                </Typography>
              </Paper>
            )}
          </Box>
        );
      }

      if (type === 'bar_chart') {
        // Simple bar chart visualization
        const chartConfig = config || {};
        const series = chartConfig.series?.[0] || {};
        const xAxisData = chartConfig.xAxis?.data || [];
        const seriesData = series.data || [];

        return (
          <Box>
            <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 2 }}>
              {chartConfig.title?.text || 'Data Distribution'}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'end', height: 200 }}>
              {xAxisData.map((label: string, index: number) => {
                const value = seriesData[index] || 0;
                const maxValue = Math.max(...seriesData);
                const height = maxValue > 0 ? (value / maxValue) * 150 : 10;
                
                return (
                  <Box key={index} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 60 }}>
                    <Typography variant="caption" sx={{ color: '#DAA520', mb: 1, fontWeight: 'bold' }}>
                      {value}
                    </Typography>
                    <Box
                      sx={{
                        width: 40,
                        height: `${height}px`,
                        background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                        borderRadius: '4px 4px 0 0',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'scaleY(1.1)',
                          boxShadow: '0 0 15px rgba(184, 134, 11, 0.6)',
                        },
                      }}
                    />
                    <Typography
                      variant="caption"
                      sx={{
                        color: 'rgba(255, 255, 255, 0.7)',
                        mt: 1,
                        fontSize: '0.7rem',
                        textAlign: 'center',
                        maxWidth: 60,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {label}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </Box>
        );
      }

      // Default fallback
      return (
        <Box
          sx={{
            height: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 2,
            border: '1px dashed rgba(255, 255, 255, 0.2)',
          }}
        >
          <Typography sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            {type ? `${type} visualization` : 'Data visualization'}
          </Typography>
        </Box>
      );
    };

    return (
      <Box
        sx={{
          mt: 2,
          p: 3,
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(184, 134, 11, 0.03) 100%)',
          borderRadius: 4,
          border: '1px solid rgba(184, 134, 11, 0.2)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 32px rgba(184, 134, 11, 0.1)',
        }}
      >
        <Box display="flex" alignItems="center" gap={1} mb={3}>
          <ChartIcon sx={{ color: '#DAA520', fontSize: '1.5rem' }} />
          <Typography
            variant="h6"
            sx={{
              color: 'rgba(255, 255, 255, 0.95)',
              fontWeight: 600,
              textShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
            }}
          >
            📊 Data Visualization
          </Typography>
        </Box>

        {renderChart()}

        {/* Insights section */}
        {insights && insights.length > 0 && (
          <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(184, 134, 11, 0.2)' }}>
            <Typography
              variant="subtitle1"
              sx={{
                color: '#DAA520',
                fontWeight: 600,
                mb: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              💡 Insights
            </Typography>
            {insights.map((insight: string, index: number) => (
              <Typography
                key={index}
                variant="body2"
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  mb: 0.5,
                  fontSize: '0.9rem',
                  '&:before': {
                    content: '"• "',
                    color: '#DAA520',
                    fontWeight: 'bold',
                  },
                }}
              >
                {insight}
              </Typography>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '800px',
        mx: 'auto',
        position: 'relative',
      }}
    >
      {/* Chat Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 3,
          pb: 1,
        }}
      >
        {messages.map((message, index) => (
          <Fade in key={message.id} timeout={300} style={{ transitionDelay: `${index * 100}ms` }}>
            <Box
              sx={{
                display: 'flex',
                mb: 3,
                alignItems: 'flex-start',
                gap: 2,
              }}
            >
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  background: message.type === 'user' 
                    ? 'linear-gradient(135deg, #4A5568, #718096, #A0AEC0)' 
                    : 'linear-gradient(135deg, #DAA520, #B8860B, #FFD700)',
                  fontSize: message.type === 'assistant' ? '18px' : '16px',
                  border: message.type === 'assistant' ? '2px solid rgba(184, 134, 11, 0.3)' : '2px solid rgba(255, 255, 255, 0.1)',
                  boxShadow: message.type === 'assistant' 
                    ? '0 0 15px rgba(184, 134, 11, 0.4)' 
                    : '0 4px 12px rgba(0, 0, 0, 0.15)',
                  animation: message.type === 'assistant' ? `${floatingGlow} 3s ease-in-out infinite` : 'none',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    boxShadow: message.type === 'assistant' 
                      ? '0 0 25px rgba(184, 134, 11, 0.8)' 
                      : '0 6px 20px rgba(0, 0, 0, 0.3)',
                  },
                }}
              >
                {message.type === 'user' ? '👤' : '𓂀'}
              </Avatar>
              
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Paper
                  sx={{
                    p: 3,
                    background: message.type === 'user' 
                      ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%)' 
                      : 'linear-gradient(135deg, rgba(184, 134, 11, 0.12) 0%, rgba(218, 165, 32, 0.06) 100%)',
                    border: message.type === 'user'
                      ? '1px solid rgba(255, 255, 255, 0.15)'
                      : '1px solid rgba(184, 134, 11, 0.25)',
                    borderRadius: 4,
                    backdropFilter: 'blur(25px)',
                    boxShadow: message.type === 'user'
                      ? '0 8px 32px rgba(0, 0, 0, 0.1)'
                      : '0 8px 32px rgba(184, 134, 11, 0.15)',
                    position: 'relative',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: message.type === 'user'
                        ? '0 12px 48px rgba(0, 0, 0, 0.15)'
                        : '0 12px 48px rgba(184, 134, 11, 0.25)',
                      border: message.type === 'user'
                        ? '1px solid rgba(255, 255, 255, 0.2)'
                        : '1px solid rgba(184, 134, 11, 0.4)',
                    },
                    '&::before': message.type === 'assistant' ? {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(184, 134, 11, 0.1), transparent)',
                      animation: `${shimmerText} 3s ease-in-out infinite`,
                    } : {},
                  }}
                >
                  {message.attachedFile && (
                    <Chip
                      icon={<UploadFileIcon />}
                      label={message.attachedFile.name}
                      sx={{
                        mb: 2,
                        background: 'rgba(76, 175, 80, 0.2)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(76, 175, 80, 0.3)',
                      }}
                    />
                  )}
                  
                  <Typography
                    sx={{
                      color: 'rgba(255, 255, 255, 0.95)',
                      lineHeight: 1.7,
                      fontSize: '1rem',
                      fontWeight: message.type === 'assistant' ? 400 : 500,
                      letterSpacing: '0.01em',
                      textShadow: message.type === 'assistant' 
                        ? '0 1px 3px rgba(0, 0, 0, 0.3)'
                        : 'none',
                      position: 'relative',
                      zIndex: 1,
                    }}
                  >
                    {message.content}
                  </Typography>

                  {message.isLoading && (
                    <Box display="flex" alignItems="center" gap={2} mt={2}>
                      <CircularProgress size={16} sx={{ color: '#DAA520' }} />
                      <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                        Processing...
                      </Typography>
                    </Box>
                  )}

                  {message.visualization && renderVisualization(message.visualization)}
                </Paper>
              </Box>
            </Box>
          </Fade>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          p: 3,
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(184, 134, 11, 0.02) 100%)',
          borderTop: '1px solid rgba(184, 134, 11, 0.15)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(184, 134, 11, 0.5), transparent)',
            animation: `${shimmerText} 4s ease-in-out infinite`,
          },
        }}
      >
        {/* File Attachment Preview */}
        {attachedFile && (
          <Box sx={{ mb: 2 }}>
            <Chip
              icon={<UploadFileIcon />}
              label={attachedFile.name}
              onDelete={() => setAttachedFile(null)}
              sx={{
                background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(56, 142, 60, 0.15))',
                color: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid rgba(76, 175, 80, 0.4)',
                backdropFilter: 'blur(10px)',
                animation: `${pulseGold} 2s ease-in-out infinite`,
                '& .MuiChip-deleteIcon': {
                  color: 'rgba(255, 255, 255, 0.8)',
                  '&:hover': {
                    color: 'rgba(255, 255, 255, 1)',
                  },
                },
              }}
            />
          </Box>
        )}

        {/* Dataset Selection */}
        {selectedDataset && (
          <Box sx={{ mb: 2 }}>
            <Chip
              icon={<TableIcon />}
              label={`Dataset: ${datasets?.find(d => d.id === selectedDataset)?.name || 'Selected'}`}
              onDelete={() => setSelectedDataset(null)}
              sx={{
                background: 'linear-gradient(135deg, rgba(184, 134, 11, 0.25), rgba(218, 165, 32, 0.15))',
                color: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid rgba(184, 134, 11, 0.4)',
                backdropFilter: 'blur(10px)',
                animation: `${pulseGold} 2s ease-in-out infinite`,
                '& .MuiChip-deleteIcon': {
                  color: 'rgba(255, 255, 255, 0.8)',
                  '&:hover': {
                    color: 'rgba(255, 255, 255, 1)',
                  },
                },
              }}
            />
          </Box>
        )}

        {/* Input Field */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            alignItems: 'flex-end',
          }}
        >
          <IconButton
            onClick={(e) => setAttachMenuAnchor(e.currentTarget)}
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              '&:hover': {
                background: 'rgba(184, 134, 11, 0.1)',
                color: '#DAA520',
              },
            }}
          >
            <AttachIcon />
          </IconButton>

          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask me about your data... 𓂀"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(184, 134, 11, 0.03) 100%)',
                borderRadius: 4,
                backdropFilter: 'blur(15px)',
                transition: 'all 0.3s ease',
                '& fieldset': {
                  borderColor: 'rgba(184, 134, 11, 0.25)',
                  borderWidth: '1.5px',
                },
                '&:hover': {
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(184, 134, 11, 0.06) 100%)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 8px 25px rgba(184, 134, 11, 0.15)',
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(184, 134, 11, 0.6)',
                  boxShadow: '0 0 0 1px rgba(184, 134, 11, 0.2)',
                },
                '&.Mui-focused': {
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(184, 134, 11, 0.08) 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 12px 35px rgba(184, 134, 11, 0.25)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#DAA520',
                  borderWidth: '2px',
                  boxShadow: '0 0 0 2px rgba(184, 134, 11, 0.15)',
                },
              },
              '& .MuiInputBase-input': {
                color: 'rgba(255, 255, 255, 0.95)',
                fontSize: '1rem',
                lineHeight: 1.6,
                padding: '16px',
                '&::placeholder': {
                  color: 'rgba(255, 255, 255, 0.6)',
                  fontStyle: 'italic',
                },
              },
            }}
          />

          <IconButton
            onClick={handleSend}
            disabled={!inputValue.trim()}
            sx={{
              width: 56,
              height: 56,
              background: inputValue.trim() 
                ? 'linear-gradient(135deg, #DAA520, #B8860B, #FFD700)' 
                : 'rgba(255, 255, 255, 0.08)',
              color: 'white',
              border: inputValue.trim()
                ? '2px solid rgba(184, 134, 11, 0.3)'
                : '2px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
              transition: 'all 0.3s ease',
              animation: inputValue.trim() ? `${pulseGold} 2s ease-in-out infinite` : 'none',
              '&:hover': {
                background: inputValue.trim() 
                  ? 'linear-gradient(135deg, #FFD700, #DAA520, #B8860B)' 
                  : 'rgba(255, 255, 255, 0.12)',
                transform: inputValue.trim() ? 'scale(1.05)' : 'scale(1.02)',
                boxShadow: inputValue.trim()
                  ? '0 8px 25px rgba(184, 134, 11, 0.4)'
                  : '0 4px 15px rgba(255, 255, 255, 0.1)',
              },
              '&.Mui-disabled': {
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'rgba(255, 255, 255, 0.3)',
                border: '2px solid rgba(255, 255, 255, 0.05)',
                animation: 'none',
              },
            }}
          >
            <SendIcon sx={{ fontSize: '1.2rem' }} />
          </IconButton>
        </Box>
      </Box>

      {/* Attachment Menu */}
      <Menu
        anchorEl={attachMenuAnchor}
        open={Boolean(attachMenuAnchor)}
        onClose={() => setAttachMenuAnchor(null)}
        PaperProps={{
          sx: {
            background: 'rgba(15, 15, 35, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <MenuItem onClick={() => fileInputRef.current?.click()}>
          <UploadFileIcon sx={{ mr: 2 }} />
          Upload New File
        </MenuItem>
        <MenuItem onClick={() => setDatasetDialogOpen(true)}>
          <TableIcon sx={{ mr: 2 }} />
          Select Existing Dataset
        </MenuItem>
      </Menu>

      {/* Dataset Selection Dialog */}
      <Dialog
        open={datasetDialogOpen}
        onClose={() => setDatasetDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(15, 15, 35, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Select Dataset</Typography>
            <IconButton onClick={() => setDatasetDialogOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <List>
            {datasets?.map((dataset) => (
              <ListItemButton
                key={dataset.id}
                onClick={() => handleDatasetSelect(dataset.id)}
                sx={{
                  borderRadius: 2,
                  mb: 1,
                  '&:hover': {
                    background: 'rgba(184, 134, 11, 0.1)',
                  },
                }}
              >
                <ListItemText
                  primary={dataset.name}
                  secondary={dataset.description}
                  primaryTypographyProps={{
                    sx: { color: 'rgba(255, 255, 255, 0.9)' },
                  }}
                  secondaryTypographyProps={{
                    sx: { color: 'rgba(255, 255, 255, 0.6)' },
                  }}
                />
              </ListItemButton>
            ))}
            {(!datasets || datasets.length === 0) && (
              <Typography sx={{ color: 'rgba(255, 255, 255, 0.6)', textAlign: 'center', py: 2 }}>
                No datasets available. Upload a file first.
              </Typography>
            )}
          </List>
        </DialogContent>
      </Dialog>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        hidden
        accept=".csv,.xlsx,.xls,.json,.parquet"
        onChange={handleFileSelect}
      />
    </Box>
  );
};

export default ChatInterface;