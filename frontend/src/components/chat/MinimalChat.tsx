import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Paper, Alert, CircularProgress } from '@mui/material';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export const MinimalChat: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setFile(event.target.files[0]);
      setError('');
    }
  };

  const handleSubmit = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    // For first message, require file upload
    if (!conversationId && !file) {
      setError('Please select a file for your first question');
      return;
    }

    setLoading(true);
    setError('');
    
    // Add user message to UI immediately
    const userMessage: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      const formData = new FormData();
      formData.append('question', question);
      formData.append('user_id', 'test');
      
      let apiUrl = 'http://localhost:8005/api/v1/conversational/';
      
      if (conversationId) {
        // Continue existing conversation
        formData.append('conversation_id', conversationId);
        apiUrl += 'continue';
      } else {
        // Start new conversation
        if (file) {
          formData.append('file', file);
        }
        apiUrl += 'analyze';
      }

      const res = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Failed: ${res.statusText}`);
      }

      const data = await res.json();
      if (data.success) {
        // Add assistant response to messages
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.answer,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // Store conversation ID for follow-up questions
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
      } else {
        setError(data.error || 'Analysis failed');
        // Remove the user message if request failed
        setMessages(prev => prev.slice(0, -1));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      // Remove the user message if request failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setQuestion(''); // Clear input after sending
    }
  };

  return (
    <Box sx={{ p: 4, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom sx={{ color: '#DAA520' }}>
        💬 Horus AI Chat (Minimal)
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!conversationId && (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'rgba(15, 15, 35, 0.95)' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
            Upload File
          </Typography>
          <input
            type="file"
            accept=".csv,.xlsx,.json"
            onChange={handleFileChange}
            style={{ marginBottom: '16px', color: 'white' }}
          />
          {file && (
            <Typography variant="body2" sx={{ color: '#DAA520' }}>
              Selected: {file.name}
            </Typography>
          )}
        </Paper>
      )}

      {/* Conversation History */}
      {messages.length > 0 && (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: 'rgba(15, 15, 35, 0.95)', maxHeight: '400px', overflow: 'auto' }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#DAA520' }}>
            🤖 Conversation with Horus AI
          </Typography>
          {messages.map((message, index) => (
            <Box key={index} sx={{ mb: 2 }}>
              <Typography 
                variant="subtitle2" 
                sx={{ 
                  color: message.role === 'user' ? '#FFD700' : '#DAA520', 
                  fontWeight: 'bold',
                  mb: 1 
                }}
              >
                {message.role === 'user' ? '👤 You:' : '🤖 Horus:'}
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  color: 'white', 
                  whiteSpace: 'pre-wrap',
                  pl: 2,
                  borderLeft: `2px solid ${message.role === 'user' ? '#FFD700' : '#DAA520'}`,
                  mb: 1
                }}
              >
                {message.content}
              </Typography>
            </Box>
          ))}
        </Paper>
      )}

      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'rgba(15, 15, 35, 0.95)' }}>
        <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
          {conversationId ? 'Continue Conversation' : 'Ask Question'}
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={2}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={conversationId ? "Ask a follow-up question..." : "Ask anything about your data..."}
          sx={{
            mb: 2,
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              '& fieldset': { borderColor: '#DAA520' },
              '&:hover fieldset': { borderColor: '#FFD700' },
              '&.Mui-focused fieldset': { borderColor: '#FFD700' },
            },
            '& .MuiInputBase-input::placeholder': {
              color: 'rgba(255, 255, 255, 0.7)',
              opacity: 1,
            },
          }}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading || (!conversationId && !file) || !question.trim()}
            sx={{
              backgroundColor: '#DAA520',
              '&:hover': { backgroundColor: '#FFD700' },
              '&:disabled': { backgroundColor: 'rgba(218, 165, 32, 0.3)' },
            }}
          >
            {loading ? <CircularProgress size={20} /> : conversationId ? 'Send' : 'Start Analysis'}
          </Button>
          
          {conversationId && (
            <Button
              variant="outlined"
              onClick={() => {
                setMessages([]);
                setConversationId(null);
                setFile(null);
                setQuestion('');
                setError('');
              }}
              sx={{
                borderColor: '#DAA520',
                color: '#DAA520',
                '&:hover': { borderColor: '#FFD700', color: '#FFD700' },
              }}
            >
              New Chat
            </Button>
          )}
        </Box>
      </Paper>
    </Box>
  );
};