import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  GitHub,
  Settings,
  Notifications,
  AccountCircle,
} from '@mui/icons-material';

const Header: React.FC = () => {
  return (
    <AppBar
      position="sticky"
      sx={{
        backgroundColor: 'white',
        color: 'text.primary',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        zIndex: theme => theme.zIndex.drawer - 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography
            variant="h5"
            component="div"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(45deg, #1976d2, #9c27b0)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mr: 2,
            }}
          >
            MCPEval
          </Typography>
          <Chip label="v1.0.0" size="small" variant="outlined" sx={{ mr: 2 }} />
          <Typography variant="body2" color="text.secondary">
            MCP Evaluation Framework
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="GitHub Repository">
            <IconButton
              color="inherit"
              onClick={() =>
                window.open(
                  'https://github.com/your-repo/mcp-eval-llm',
                  '_blank'
                )
              }
            >
              <GitHub />
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Notifications />
            </IconButton>
          </Tooltip>

          <Tooltip title="Settings">
            <IconButton color="inherit">
              <Settings />
            </IconButton>
          </Tooltip>

          <Tooltip title="Profile">
            <IconButton color="inherit">
              <AccountCircle />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
