import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Typography,
  Box,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Add as GenerateIcon,
  CheckCircle as VerifyIcon,
  Transform as ConvertIcon,
  ContentCut as SplitIcon,
  Assessment as EvaluateIcon,
  Analytics as AnalyzeIcon,
  Gavel as JudgeIcon,
  Folder as ResultsIcon,
  Code as ServerIcon,
  Settings as BackendIcon,
  Chat as ChatIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactElement;
  path: string;
  description: string;
  category:
    | 'overview'
    | 'tasks'
    | 'data'
    | 'evaluation'
    | 'analysis'
    | 'servers';
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/',
    description: 'Overview and quick actions',
    category: 'overview',
  },
  {
    id: 'server-files',
    label: 'MCP Servers',
    icon: <ServerIcon />,
    path: '/server-files',
    description: 'View MCP server files',
    category: 'servers',
  },
  {
    id: 'backend-files',
    label: 'Backend Files',
    icon: <BackendIcon />,
    path: '/backend-files',
    description: 'View backend application files',
    category: 'servers',
  },
  {
    id: 'mcp-chat',
    label: 'MCP Chat Client',
    icon: <ChatIcon />,
    path: '/mcp-chat',
    description: 'Chat with MCP servers',
    category: 'servers',
  },
  {
    id: 'generate-tasks',
    label: 'Generate Tasks',
    icon: <GenerateIcon />,
    path: '/generate-tasks',
    description: 'Create new evaluation tasks',
    category: 'tasks',
  },
  {
    id: 'verify-tasks',
    label: 'Verify Tasks',
    icon: <VerifyIcon />,
    path: '/verify-tasks',
    description: 'Validate generated tasks',
    category: 'tasks',
  },
  {
    id: 'convert-data',
    label: 'Convert Data',
    icon: <ConvertIcon />,
    path: '/convert-data',
    description: 'Transform data formats',
    category: 'data',
  },
  {
    id: 'split-data',
    label: 'Split Data',
    icon: <SplitIcon />,
    path: '/split-data',
    description: 'Create train/test splits',
    category: 'data',
  },
  {
    id: 'evaluate',
    label: 'Model Evaluation',
    icon: <EvaluateIcon />,
    path: '/evaluate',
    description: 'Run model evaluations',
    category: 'evaluation',
  },
  {
    id: 'analyze',
    label: 'Analyze Results',
    icon: <AnalyzeIcon />,
    path: '/analyze',
    description: 'Compare against ground truth',
    category: 'analysis',
  },
  {
    id: 'judge',
    label: 'LLM Judge',
    icon: <JudgeIcon />,
    path: '/judge',
    description: 'AI-powered evaluation',
    category: 'analysis',
  },
  {
    id: 'results',
    label: 'Results & Reports',
    icon: <ResultsIcon />,
    path: '/results',
    description: 'View evaluation results',
    category: 'analysis',
  },
];

const categoryLabels = {
  overview: 'Overview',
  servers: 'Server Management',
  tasks: 'Task Management',
  data: 'Data Processing',
  evaluation: 'Model Evaluation',
  analysis: 'Analysis & Reports',
};

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const groupedItems = menuItems.reduce(
    (acc, item) => {
      if (!acc[item.category]) {
        acc[item.category] = [];
      }
      acc[item.category].push(item);
      return acc;
    },
    {} as Record<string, MenuItem[]>
  );

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#fafafa',
          borderRight: '1px solid #e0e0e0',
        },
      }}
    >
      <Box sx={{ p: 2, mt: 8 }}>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontWeight: 500,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          Navigation
        </Typography>
      </Box>

      <List sx={{ px: 1 }}>
        {Object.entries(groupedItems).map(([category, items]) => (
          <Box key={category}>
            {category !== 'overview' && (
              <>
                <Divider sx={{ my: 1 }} />
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    px: 2,
                    py: 1,
                    fontWeight: 500,
                    fontSize: '0.75rem',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                  }}
                >
                  {categoryLabels[category as keyof typeof categoryLabels]}
                </Typography>
              </>
            )}

            {items.map(item => (
              <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  onClick={() => navigate(item.path)}
                  selected={location.pathname === item.path}
                  sx={{
                    borderRadius: '8px',
                    mx: 1,
                    '&.Mui-selected': {
                      backgroundColor: 'primary.main',
                      color: 'white',
                      '& .MuiListItemIcon-root': {
                        color: 'white',
                      },
                      '&:hover': {
                        backgroundColor: 'primary.dark',
                      },
                    },
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color:
                        location.pathname === item.path
                          ? 'white'
                          : 'primary.main',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    secondary={item.description}
                    primaryTypographyProps={{
                      fontSize: '0.9rem',
                      fontWeight: location.pathname === item.path ? 600 : 500,
                    }}
                    secondaryTypographyProps={{
                      fontSize: '0.75rem',
                      color:
                        location.pathname === item.path
                          ? 'rgba(255,255,255,0.7)'
                          : 'text.secondary',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </Box>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;
