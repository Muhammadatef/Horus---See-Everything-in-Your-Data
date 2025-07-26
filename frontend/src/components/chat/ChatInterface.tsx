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

    return (
      <Box
        sx={{
          mt: 2,
          p: 3,
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: 3,
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <ChartIcon sx={{ color: '#DAA520' }} />
          <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            Data Visualization
          </Typography>
        </Box>
        {/* Placeholder for chart rendering */}
        <Box
          sx={{
            height: 300,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 2,
            border: '1px dashed rgba(255, 255, 255, 0.2)',
          }}
        >
          <Typography sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            Chart visualization would render here
          </Typography>
        </Box>
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
                  width: 32,
                  height: 32,
                  background: message.type === 'user' 
                    ? 'linear-gradient(135deg, #666, #888)' 
                    : 'linear-gradient(135deg, #DAA520, #B8860B)',
                  fontSize: message.type === 'assistant' ? '16px' : '14px',
                }}
              >
                {message.type === 'user' ? 'U' : '𓂀'}
              </Avatar>
              
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Paper
                  sx={{
                    p: 3,
                    background: message.type === 'user' 
                      ? 'rgba(255, 255, 255, 0.08)' 
                      : 'rgba(184, 134, 11, 0.08)',
                    border: message.type === 'user'
                      ? '1px solid rgba(255, 255, 255, 0.1)'
                      : '1px solid rgba(184, 134, 11, 0.2)',
                    borderRadius: 3,
                    backdropFilter: 'blur(20px)',
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
                      color: 'rgba(255, 255, 255, 0.9)',
                      lineHeight: 1.6,
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
          background: 'rgba(255, 255, 255, 0.02)',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
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
                background: 'rgba(76, 175, 80, 0.2)',
                color: 'rgba(255, 255, 255, 0.9)',
                border: '1px solid rgba(76, 175, 80, 0.3)',
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
                background: 'rgba(33, 150, 243, 0.2)',
                color: 'rgba(255, 255, 255, 0.9)',
                border: '1px solid rgba(33, 150, 243, 0.3)',
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
            placeholder="Ask me about your data..."
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 3,
                '& fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(184, 134, 11, 0.5)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#DAA520',
                },
              },
              '& .MuiInputBase-input': {
                color: 'rgba(255, 255, 255, 0.9)',
                '&::placeholder': {
                  color: 'rgba(255, 255, 255, 0.5)',
                },
              },
            }}
          />

          <IconButton
            onClick={handleSend}
            disabled={!inputValue.trim()}
            sx={{
              background: inputValue.trim() ? 'linear-gradient(135deg, #DAA520, #B8860B)' : 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              '&:hover': {
                background: inputValue.trim() ? 'linear-gradient(135deg, #B8860B, #DAA520)' : 'rgba(255, 255, 255, 0.1)',
              },
              '&.Mui-disabled': {
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'rgba(255, 255, 255, 0.3)',
              },
            }}
          >
            <SendIcon />
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