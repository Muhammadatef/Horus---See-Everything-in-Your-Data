import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Alert,
  IconButton,
  Fade,
  Grow
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Send as SendIcon,
  AttachFile as AttachIcon,
  Analytics as AnalyticsIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Insights as InsightsIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Egyptian-themed styling
const EgyptianContainer = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
  minHeight: '100vh',
  padding: theme.spacing(3),
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23DAA520' fill-opacity='0.03'%3E%3Cpath d='M20 20c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10zm10 0c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10z'/%3E%3C/g%3E%3C/svg%3E")`,
    pointerEvents: 'none'
  }
}));

const ChatContainer = styled(Paper)(({ theme }) => ({
  maxWidth: 800,
  margin: '0 auto',
  borderRadius: theme.spacing(2),
  background: 'rgba(15, 15, 35, 0.95)',
  backdropFilter: 'blur(10px)',
  border: '2px solid rgba(218, 165, 32, 0.3)',
  boxShadow: '0 8px 32px rgba(218, 165, 32, 0.2)',
  position: 'relative',
  zIndex: 1
}));

const MessageBubble = styled(Box)<{ isUser?: boolean }>(({ theme, isUser }) => ({
  backgroundColor: isUser ? '#DAA520' : 'rgba(255, 255, 255, 0.1)',
  color: isUser ? 'white' : 'rgba(255, 255, 255, 0.9)',
  padding: theme.spacing(2),
  borderRadius: theme.spacing(2),
  marginBottom: theme.spacing(2),
  maxWidth: '80%',
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  boxShadow: isUser 
    ? '0 4px 16px rgba(218, 165, 32, 0.3)' 
    : '0 4px 16px rgba(0, 0, 0, 0.1)',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    width: 0,
    height: 0,
    border: '8px solid transparent',
    ...(isUser 
      ? {
          right: -16,
          top: 16,
          borderLeftColor: '#DAA520'
        }
      : {
          left: -16,
          top: 16,
          borderRightColor: 'rgba(255, 255, 255, 0.1)'
        })
  }
}));

const FollowUpButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(0.5),
  borderRadius: theme.spacing(3),
  textTransform: 'none',
  background: 'linear-gradient(45deg, #DAA520, #FFD700)',
  color: 'white',
  '&:hover': {
    background: 'linear-gradient(45deg, #B8860B, #DAA520)',
    transform: 'translateY(-1px)',
    boxShadow: '0 4px 12px rgba(218, 165, 32, 0.4)'
  }
}));

interface ConversationMessage {
  id: string;
  question: string;
  answer: string;
  isUser: boolean;
  timestamp: Date;
  followUpQuestions?: string[];
  visualization?: any;
  dataSummary?: any;
}

interface ConversationalAnalysisResponse {
  conversation_id: string;
  question: string;
  answer: string;
  data_summary?: any;
  visualization?: any;
  follow_up_questions?: string[];
  success: boolean;
  error?: string;
}

export const ConversationalInterface: React.FC = () => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const analyzeFileWithQuestion = async (file: File, question: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('question', question);
    formData.append('user_id', 'default');
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    // Use fetch with extended timeout for file analysis
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes timeout
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/conversational/analyze', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      return response.json() as Promise<ConversationalAnalysisResponse>;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  };

  const continueConversation = async (question: string) => {
    const formData = new FormData();
    formData.append('question', question);
    formData.append('conversation_id', conversationId!);
    formData.append('user_id', 'default');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes for follow-up questions
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/conversational/continue', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Conversation failed: ${response.statusText}`);
      }

      return response.json() as Promise<ConversationalAnalysisResponse>;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  };

  const handleSubmit = async (questionToSubmit?: string) => {
    const question = questionToSubmit || currentQuestion;
    if (!question.trim()) return;

    // For first message, require file upload
    if (messages.length === 0 && !selectedFile) {
      setError('Please upload a data file to start the conversation.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    // Add user message
    const userMessage: ConversationMessage = {
      id: Date.now().toString(),
      question,
      answer: '',
      isUser: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setCurrentQuestion('');

    try {
      let result: ConversationalAnalysisResponse;
      
      if (messages.length === 0 && selectedFile) {
        // First interaction with file
        result = await analyzeFileWithQuestion(selectedFile, question);
        setConversationId(result.conversation_id);
      } else {
        // Continue existing conversation
        result = await continueConversation(question);
      }

      if (result.success) {
        // Add AI response
        const aiMessage: ConversationMessage = {
          id: (Date.now() + 1).toString(),
          question: result.question,
          answer: result.answer,
          isUser: false,
          timestamp: new Date(),
          followUpQuestions: result.follow_up_questions,
          visualization: result.visualization,
          dataSummary: result.data_summary
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      // Remove the user message if analysis failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderVisualization = (visualization: any) => {
    if (!visualization) return null;

    return (
      <Box mt={2} p={2} bgcolor="rgba(218, 165, 32, 0.1)" borderRadius={2}>
        <Typography variant="h6" color="primary" gutterBottom>
          📊 Data Visualization
        </Typography>
        {visualization.insights && (
          <Box>
            {visualization.insights.map((insight: string, idx: number) => (
              <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                {insight}
              </Typography>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  return (
    <EgyptianContainer>
      <Box textAlign="center" mb={4}>
        <Typography 
          variant="h3" 
          component="h1" 
          sx={{ 
            color: '#DAA520', 
            fontWeight: 'bold',
            textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
            mb: 1
          }}
        >
          🔮 Horus AI Data Analyst
        </Typography>
        <Typography 
          variant="h6" 
          sx={{ 
            color: 'rgba(255, 255, 255, 0.8)',
            fontStyle: 'italic'
          }}
        >
          Upload your data and start a conversation • Just like ChatGPT, but for your business data
        </Typography>
      </Box>

      <ChatContainer elevation={8}>
        <Box p={3}>
          {/* Header */}
          <Box display="flex" alignItems="center" mb={3}>
            <PsychologyIcon sx={{ color: '#DAA520', mr: 1 }} />
            <Typography variant="h5" fontWeight="bold" color="primary">
              Conversational Data Analysis
            </Typography>
          </Box>

          {/* File Upload Section (only show if no conversation started) */}
          {messages.length === 0 && (
            <Card sx={{ mb: 3, bgcolor: 'rgba(218, 165, 32, 0.05)' }}>
              <CardContent>
                <Box textAlign="center">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept=".csv,.xlsx,.xls,.json"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={() => fileInputRef.current?.click()}
                    sx={{ mb: 2 }}
                  >
                    Choose Data File
                  </Button>
                  {selectedFile && (
                    <Chip 
                      label={selectedFile.name} 
                      color="primary" 
                      sx={{ ml: 2 }}
                      onDelete={() => setSelectedFile(null)}
                    />
                  )}
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Upload CSV, Excel, or JSON files to start analyzing your data
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Messages */}
          <Box 
            sx={{ 
              maxHeight: 500, 
              overflowY: 'auto', 
              mb: 3,
              display: 'flex',
              flexDirection: 'column',
              gap: 2
            }}
          >
            {messages.length === 0 && (
              <Box textAlign="center" py={4}>
                <AnalyticsIcon sx={{ fontSize: 48, color: '#DAA520', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Ready to analyze your data!
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upload a file and ask any question about your data. I'll provide insights, visualizations, and follow-up suggestions.
                </Typography>
              </Box>
            )}

            {messages.map((message, index) => (
              <Fade in={true} key={message.id} timeout={500 + index * 200}>
                <MessageBubble isUser={message.isUser}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {message.isUser ? message.question : message.answer}
                  </Typography>
                  
                  {/* Data Summary */}
                  {message.dataSummary && (
                    <Box mt={2} p={2} bgcolor="rgba(0,0,0,0.1)" borderRadius={1}>
                      <Typography variant="caption" display="block">
                        📁 {message.dataSummary.filename} • {message.dataSummary.total_rows} rows • {message.dataSummary.total_columns} columns
                      </Typography>
                    </Box>
                  )}
                  
                  {/* Visualization */}
                  {renderVisualization(message.visualization)}
                  
                  {/* Follow-up Questions */}
                  {message.followUpQuestions && message.followUpQuestions.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        💡 Try asking:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {message.followUpQuestions.map((question, idx) => (
                          <FollowUpButton
                            key={idx}
                            size="small"
                            onClick={() => handleSubmit(question)}
                            disabled={isAnalyzing}
                          >
                            {question}
                          </FollowUpButton>
                        ))}
                      </Box>
                    </Box>
                  )}
                </MessageBubble>
              </Fade>
            ))}

            {isAnalyzing && (
              <Grow in={true}>
                <MessageBubble>
                  <Box display="flex" alignItems="center" gap={2}>
                    <CircularProgress size={20} sx={{ color: '#DAA520' }} />
                    <Typography variant="body2" color="text.secondary">
                      Analyzing your data and generating insights...
                    </Typography>
                  </Box>
                </MessageBubble>
              </Grow>
            )}
          </Box>

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Input Section */}
          <Box display="flex" gap={2} alignItems="flex-end">
            <TextField
              fullWidth
              multiline
              maxRows={3}
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              placeholder={
                messages.length === 0 
                  ? "Upload a file and ask: 'How many customers do I have?' or 'Show me sales trends'"
                  : "Ask a follow-up question about your data..."
              }
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              disabled={isAnalyzing}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  '&:hover fieldset': {
                    borderColor: '#DAA520',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#DAA520',
                  },
                }
              }}
            />
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => handleSubmit()}
              disabled={isAnalyzing || !currentQuestion.trim() || (messages.length === 0 && !selectedFile)}
              sx={{
                background: 'linear-gradient(45deg, #DAA520, #FFD700)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #B8860B, #DAA520)',
                },
                minWidth: 120,
                height: 56,
                borderRadius: 2
              }}
            >
              {isAnalyzing ? 'Analyzing...' : 'Send'}
            </Button>
          </Box>

          {/* Tips */}
          {messages.length === 0 && (
            <Box mt={3} p={2} bgcolor="rgba(218, 165, 32, 0.05)" borderRadius={2}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <TrendingUpIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                <strong>Pro Tips:</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Ask specific questions: "How many active users do I have?"<br/>
                • Request comparisons: "Compare sales between regions"<br/>
                • Explore trends: "Show me monthly growth patterns"<br/>
                • Get insights: "What anomalies do you see in this data?"
              </Typography>
            </Box>
          )}
        </Box>
      </ChatContainer>
    </EgyptianContainer>
  );
};