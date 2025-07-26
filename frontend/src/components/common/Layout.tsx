import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
  AppBar,
  Toolbar,
  Fade,
  Grow,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  Dashboard as DashboardIcon,
  Close as CloseIcon,
  ChatBubbleOutline as ChatIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

// Egyptian Background Animation Component
const EgyptianBackground: React.FC = () => {
  const hieroglyphs = ['𓂀', '𓁢', '𓊪', '𓊤', '𓊨', '𓊧', '𓊩', '𓊬', '𓊮', '𓊯', '𓊰', '𓊱', '𓊲', '𓊳'];
  
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
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)',
      }}
    >
      {/* Animated Egyptian symbols */}
      {Array.from({ length: 20 }).map((_, i) => (
        <Box
          key={i}
          sx={{
            position: 'absolute',
            color: 'rgba(184, 134, 11, 0.1)',
            fontSize: Math.random() * 40 + 20,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `float ${Math.random() * 6 + 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 2}s`,
            '@keyframes float': {
              '0%, 100%': {
                transform: 'translateY(0px) rotate(0deg)',
                opacity: 0.1,
              },
              '50%': {
                transform: `translateY(-${Math.random() * 30 + 10}px) rotate(${Math.random() * 10 - 5}deg)`,
                opacity: 0.3,
              },
            },
          }}
        >
          {hieroglyphs[Math.floor(Math.random() * hieroglyphs.length)]}
        </Box>
      ))}
      
      {/* Glowing particles */}
      {Array.from({ length: 50 }).map((_, i) => (
        <Box
          key={`particle-${i}`}
          sx={{
            position: 'absolute',
            width: '2px',
            height: '2px',
            background: 'rgba(184, 134, 11, 0.6)',
            borderRadius: '50%',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `twinkle ${Math.random() * 4 + 2}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 3}s`,
            '@keyframes twinkle': {
              '0%, 100%': {
                opacity: 0,
                transform: 'scale(0.5)',
              },
              '50%': {
                opacity: 1,
                transform: 'scale(1.5)',
              },
            },
          }}
        />
      ))}
    </Box>
  );
};

// Modern Sidebar Component
const ModernSidebar: React.FC<{
  open: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
  currentPath: string;
}> = ({ open, onClose, onNavigate, currentPath }) => {
  const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/', description: 'Dashboard overview' },
    { text: 'Chat with Horus', icon: <ChatIcon />, path: '/chat', description: 'AI-powered data conversations' },
    { text: 'Upload Data', icon: <UploadIcon />, path: '/upload', description: 'Upload and process files' },
    { text: 'Query Data', icon: <SearchIcon />, path: '/query', description: 'Advanced query interface' },
    { text: 'Analytics', icon: <DashboardIcon />, path: '/dashboard', description: 'View insights and charts' },
  ];

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: 280,
          background: 'linear-gradient(180deg, rgba(15, 15, 35, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
          border: 'none',
          borderRight: '1px solid rgba(184, 134, 11, 0.2)',
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <Box
              sx={{
                fontSize: '32px',
                background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 10px rgba(184, 134, 11, 0.5))',
              }}
            >
              𓂀
            </Box>
            <Typography
              variant="h6"
              sx={{
                background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 700,
                letterSpacing: '0.5px',
              }}
            >
              Horus AI
            </Typography>
          </Box>
          <IconButton onClick={onClose} sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            <CloseIcon />
          </IconButton>
        </Box>

        <List sx={{ mt: 2 }}>
          {menuItems.map((item, index) => (
            <Grow in timeout={300 + index * 100} key={item.path}>
              <ListItem
                button
                onClick={() => {
                  onNavigate(item.path);
                  onClose();
                }}
                sx={{
                  mb: 1,
                  borderRadius: 2,
                  background: currentPath === item.path 
                    ? 'linear-gradient(135deg, rgba(184, 134, 11, 0.2), rgba(218, 165, 32, 0.1))'
                    : 'transparent',
                  border: currentPath === item.path 
                    ? '1px solid rgba(184, 134, 11, 0.3)'
                    : '1px solid transparent',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: 'linear-gradient(135deg, rgba(184, 134, 11, 0.1), rgba(218, 165, 32, 0.05))',
                    border: '1px solid rgba(184, 134, 11, 0.2)',
                    transform: 'translateX(4px)',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: currentPath === item.path ? '#DAA520' : 'rgba(255, 255, 255, 0.7)',
                    minWidth: 40,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  secondary={item.description}
                  primaryTypographyProps={{
                    sx: {
                      color: currentPath === item.path ? '#DAA520' : 'rgba(255, 255, 255, 0.9)',
                      fontWeight: currentPath === item.path ? 600 : 400,
                      fontSize: '0.95rem',
                    },
                  }}
                  secondaryTypographyProps={{
                    sx: {
                      color: 'rgba(255, 255, 255, 0.5)',
                      fontSize: '0.8rem',
                    },
                  }}
                />
              </ListItem>
            </Grow>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ minHeight: '100vh', position: 'relative' }}>
      {/* Egyptian Background Animation */}
      <EgyptianBackground />
      
      {/* Top Navigation Bar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          background: 'rgba(15, 15, 35, 0.8)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(184, 134, 11, 0.2)',
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setSidebarOpen(true)}
            sx={{
              mr: 2,
              color: 'rgba(255, 255, 255, 0.9)',
              '&:hover': {
                background: 'rgba(184, 134, 11, 0.1)',
              },
            }}
          >
            <MenuIcon />
          </IconButton>

          <Box display="flex" alignItems="center" gap={2} flexGrow={1}>
            <Box
              sx={{
                fontSize: '28px',
                background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 10px rgba(184, 134, 11, 0.5))',
              }}
            >
              𓂀
            </Box>
            <Typography
              variant="h6"
              sx={{
                background: 'linear-gradient(135deg, #DAA520, #B8860B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 700,
                letterSpacing: '0.5px',
              }}
            >
              Horus AI-BI Platform
            </Typography>
          </Box>

          <Typography
            variant="caption"
            sx={{
              color: 'rgba(255, 255, 255, 0.6)',
              fontStyle: 'italic',
            }}
          >
            All-seeing data intelligence
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Modern Sidebar */}
      <ModernSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNavigate={handleNavigation}
        currentPath={location.pathname}
      />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          pt: 8, // Account for AppBar
          minHeight: '100vh',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <Fade in timeout={500}>
          <Box
            sx={{
              maxWidth: '1400px',
              mx: 'auto',
              px: { xs: 2, sm: 3, md: 4 },
              py: 4,
            }}
          >
            {children}
          </Box>
        </Fade>
      </Box>
    </Box>
  );
};

export default Layout;