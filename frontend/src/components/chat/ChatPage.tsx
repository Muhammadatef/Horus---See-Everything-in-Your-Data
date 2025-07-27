import React from 'react';
import {
  Box,
  Container,
  Typography,
  Fade,
  keyframes,
} from '@mui/material';
import { MinimalChat } from './MinimalChat';

// Egyptian Background Animation Component
const EgyptianChatBackground: React.FC = () => {
  const hieroglyphs = [
    '𓂀', '𓁢', '𓊪', '𓊤', '𓊨', '𓊧', '𓊩', '𓊬', '𓊮', '𓊯', '𓊰', '𓊱', '𓊲', '𓊳',
    '𓋹', '𓌻', '𓍯', '𓎆', '𓏏', '𓏛', '𓐍', '𓅓', '𓈖', '𓉐', '𓋴', '𓌳', '𓍘', '𓎗',
    '𓂧', '𓃀', '𓄿', '𓆑', '𓇯', '𓈎', '𓉻', '𓊽', '𓋼', '𓌾', '𓍿', '𓎯', '𓏰', '𓐰',
  ];

  const ancientSymbols = ['⚱', '🏺', '🔱', '☥', '🐍', '🦅', '🐪', '🌙', '⭐', '☀'];

  // Floating animation keyframes
  const floatAnimation = keyframes`
    0%, 100% {
      transform: translateY(0px) rotate(0deg);
      opacity: 0.1;
    }
    25% {
      transform: translateY(-20px) rotate(5deg);
      opacity: 0.3;
    }
    50% {
      transform: translateY(-15px) rotate(-3deg);
      opacity: 0.4;
    }
    75% {
      transform: translateY(-25px) rotate(7deg);
      opacity: 0.2;
    }
  `;

  const pulseAnimation = keyframes`
    0%, 100% {
      opacity: 0.1;
      transform: scale(1);
    }
    50% {
      opacity: 0.6;
      transform: scale(1.2);
    }
  `;

  const slideAnimation = keyframes`
    0% {
      transform: translateX(-100px) rotate(0deg);
      opacity: 0;
    }
    50% {
      opacity: 0.3;
    }
    100% {
      transform: translateX(100vw) rotate(360deg);
      opacity: 0;
    }
  `;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        overflow: 'hidden',
        background: `
          radial-gradient(circle at 20% 80%, rgba(184, 134, 11, 0.1) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(218, 165, 32, 0.08) 0%, transparent 50%),
          radial-gradient(circle at 40% 40%, rgba(184, 134, 11, 0.05) 0%, transparent 50%),
          linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 25%, #16213e 50%, #0f0f23 100%)
        `,
      }}
    >
      {/* Large Floating Hieroglyphs */}
      {Array.from({ length: 15 }).map((_, i) => (
        <Box
          key={`large-${i}`}
          sx={{
            position: 'absolute',
            color: 'rgba(184, 134, 11, 0.15)',
            fontSize: `${Math.random() * 50 + 30}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `${floatAnimation} ${Math.random() * 8 + 6}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 5}s`,
            fontWeight: 'bold',
            textShadow: '0 0 20px rgba(184, 134, 11, 0.3)',
          }}
        >
          {hieroglyphs[Math.floor(Math.random() * hieroglyphs.length)]}
        </Box>
      ))}

      {/* Medium Floating Symbols */}
      {Array.from({ length: 20 }).map((_, i) => (
        <Box
          key={`medium-${i}`}
          sx={{
            position: 'absolute',
            color: 'rgba(218, 165, 32, 0.12)',
            fontSize: `${Math.random() * 30 + 20}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `${floatAnimation} ${Math.random() * 10 + 8}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 6}s`,
            filter: 'blur(0.5px)',
          }}
        >
          {hieroglyphs[Math.floor(Math.random() * hieroglyphs.length)]}
        </Box>
      ))}

      {/* Small Pulsing Particles */}
      {Array.from({ length: 30 }).map((_, i) => (
        <Box
          key={`small-${i}`}
          sx={{
            position: 'absolute',
            color: 'rgba(184, 134, 11, 0.08)',
            fontSize: `${Math.random() * 20 + 12}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `${pulseAnimation} ${Math.random() * 4 + 3}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 3}s`,
          }}
        >
          {hieroglyphs[Math.floor(Math.random() * hieroglyphs.length)]}
        </Box>
      ))}

      {/* Sliding Ancient Symbols */}
      {Array.from({ length: 8 }).map((_, i) => (
        <Box
          key={`sliding-${i}`}
          sx={{
            position: 'absolute',
            color: 'rgba(218, 165, 32, 0.2)',
            fontSize: `${Math.random() * 25 + 15}px`,
            top: `${Math.random() * 80 + 10}%`,
            animation: `${slideAnimation} ${Math.random() * 20 + 15}s linear infinite`,
            animationDelay: `${Math.random() * 10}s`,
            filter: 'drop-shadow(0 0 10px rgba(184, 134, 11, 0.3))',
          }}
        >
          {ancientSymbols[Math.floor(Math.random() * ancientSymbols.length)]}
        </Box>
      ))}

      {/* Glowing Orbs */}
      {Array.from({ length: 12 }).map((_, i) => (
        <Box
          key={`orb-${i}`}
          sx={{
            position: 'absolute',
            width: `${Math.random() * 8 + 4}px`,
            height: `${Math.random() * 8 + 4}px`,
            background: `radial-gradient(circle, rgba(184, 134, 11, 0.8) 0%, rgba(218, 165, 32, 0.4) 50%, transparent 100%)`,
            borderRadius: '50%',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `${pulseAnimation} ${Math.random() * 6 + 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 4}s`,
            boxShadow: '0 0 20px rgba(184, 134, 11, 0.5)',
          }}
        />
      ))}

      {/* Sacred Geometry Lines */}
      <Box
        sx={{
          position: 'absolute',
          top: '20%',
          left: '10%',
          width: '80%',
          height: '60%',
          background: `
            linear-gradient(45deg, transparent 49%, rgba(184, 134, 11, 0.1) 50%, transparent 51%),
            linear-gradient(-45deg, transparent 49%, rgba(218, 165, 32, 0.08) 50%, transparent 51%)
          `,
          backgroundSize: '100px 100px',
          opacity: 0.3,
          animation: `${floatAnimation} 20s ease-in-out infinite`,
        }}
      />
    </Box>
  );
};

const ChatPage: React.FC = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Egyptian Animated Background */}
      <EgyptianChatBackground />

      {/* Modern Header with Glassmorphism */}
      <Fade in timeout={800}>
        <Box
          sx={{
            textAlign: 'center',
            py: 3,
            background: 'rgba(15, 15, 35, 0.8)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(184, 134, 11, 0.2)',
            boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
            position: 'relative',
            zIndex: 10,
          }}
        >
          <Box display="flex" alignItems="center" justifyContent="center" gap={3} mb={2}>
            <Box
              sx={{
                fontSize: '3rem',
                background: 'linear-gradient(135deg, #DAA520, #B8860B, #FFD700)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 20px rgba(184, 134, 11, 0.8))',
                animation: 'pulse 3s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': {
                    filter: 'drop-shadow(0 0 20px rgba(184, 134, 11, 0.8))',
                    transform: 'scale(1)',
                  },
                  '50%': {
                    filter: 'drop-shadow(0 0 30px rgba(184, 134, 11, 1))',
                    transform: 'scale(1.05)',
                  },
                },
              }}
            >
              𓂀
            </Box>
            <Box>
              <Typography
                variant="h3"
                sx={{
                  background: 'linear-gradient(135deg, #DAA520, #B8860B, #FFD700)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                  textShadow: '0 0 30px rgba(184, 134, 11, 0.5)',
                }}
              >
                Horus AI Chat
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  fontWeight: 300,
                  fontStyle: 'italic',
                  mt: 0.5,
                }}
              >
                All-seeing Data Intelligence
              </Typography>
            </Box>
          </Box>
          
          <Typography
            variant="body1"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              maxWidth: '700px',
              mx: 'auto',
              lineHeight: 1.6,
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
              p: 2,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            }}
          >
            🏺 Upload your data files and ask questions in natural language. 
            I'll analyze your data and provide insights with visualizations 
            using the wisdom of ancient Egypt and modern AI. 𓂀
          </Typography>
        </Box>
      </Fade>

      {/* Chat Interface Container with Modern Styling */}
      <Box 
        sx={{ 
          flex: 1, 
          display: 'flex',
          position: 'relative',
          zIndex: 5,
        }}
      >
        <Container 
          maxWidth="lg" 
          sx={{ 
            display: 'flex', 
            flex: 1,
            py: 2,
          }}
        >
          <Box
            sx={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.02)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 4,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
              overflow: 'hidden',
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '2px',
                background: 'linear-gradient(90deg, transparent, #DAA520, #B8860B, #DAA520, transparent)',
                animation: 'shimmer 3s ease-in-out infinite',
                '@keyframes shimmer': {
                  '0%, 100%': { opacity: 0.5 },
                  '50%': { opacity: 1 },
                },
              },
            }}
          >
            <MinimalChat />
          </Box>
        </Container>
      </Box>

      {/* Bottom Accent with Egyptian Pattern */}
      <Box
        sx={{
          height: '4px',
          background: `
            linear-gradient(90deg, 
              transparent 0%, 
              rgba(184, 134, 11, 0.3) 25%, 
              rgba(218, 165, 32, 0.5) 50%, 
              rgba(184, 134, 11, 0.3) 75%, 
              transparent 100%
            )
          `,
          animation: 'flow 4s ease-in-out infinite',
          '@keyframes flow': {
            '0%, 100%': {
              backgroundPosition: '0% 50%',
            },
            '50%': {
              backgroundPosition: '100% 50%',
            },
          },
        }}
      />
    </Box>
  );
};

export default ChatPage;