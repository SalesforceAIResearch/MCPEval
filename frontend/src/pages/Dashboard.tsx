import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as GenerateIcon,
  CheckCircle as VerifyIcon,
  Assessment as EvaluateIcon,
  Analytics as AnalyzeIcon,
  PlayArrow,
  Refresh,
  MoreVert,
} from '@mui/icons-material';

interface QuickActionCard {
  title: string;
  description: string;
  icon: React.ReactElement;
  action: string;
  path: string;
  color: string;
}

interface RecentActivity {
  id: string;
  type: string;
  title: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  progress?: number;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(true);

  const quickActions: QuickActionCard[] = [
    {
      title: 'Generate Tasks',
      description: 'Create new evaluation tasks for MCP servers',
      icon: <GenerateIcon sx={{ fontSize: 32 }} />,
      action: 'Generate',
      path: '/generate-tasks',
      color: '#4caf50',
    },
    {
      title: 'Verify Tasks',
      description: 'Validate generated tasks against servers',
      icon: <VerifyIcon sx={{ fontSize: 32 }} />,
      action: 'Verify',
      path: '/verify-tasks',
      color: '#2196f3',
    },
    {
      title: 'Evaluate Models',
      description: 'Run comprehensive model evaluations',
      icon: <EvaluateIcon sx={{ fontSize: 32 }} />,
      action: 'Evaluate',
      path: '/evaluate',
      color: '#ff9800',
    },
    {
      title: 'Analyze Results',
      description: 'Deep dive into evaluation metrics',
      icon: <AnalyzeIcon sx={{ fontSize: 32 }} />,
      action: 'Analyze',
      path: '/analyze',
      color: '#9c27b0',
    },
  ];

  // Fetch recent activities from API
  const fetchRecentActivities = async () => {
    try {
      const response = await axios.get('/api/recent-activities');
      setRecentActivities(response.data.activities || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch recent activities:', error);

      // Fallback to demo data if API fails
      const fallbackActivities: RecentActivity[] = [
        {
          id: 'demo-1',
          type: 'Demo Data',
          title: 'API Connection Failed - Showing Demo',
          status: 'pending',
          timestamp: 'Demo mode',
        },
      ];
      setRecentActivities(fallbackActivities);
      setIsLoading(false);
    }
  };

  // Set up real-time updates
  useEffect(() => {
    // Initial fetch
    fetchRecentActivities();

    // Update every 5 seconds
    const interval = setInterval(() => {
      fetchRecentActivities();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#4caf50';
      case 'running':
        return '#2196f3';
      case 'failed':
        return '#f44336';
      case 'pending':
        return '#ff9800';
      default:
        return '#9e9e9e';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'running':
        return 'Running';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to MCPEval
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Your comprehensive MCP evaluation framework dashboard
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={3}>
          {quickActions.map(action => (
            <Grid item xs={12} sm={6} md={3} key={action.title}>
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                  },
                }}
                onClick={() => navigate(action.path)}
              >
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Avatar
                    sx={{
                      bgcolor: action.color,
                      width: 64,
                      height: 64,
                      mx: 'auto',
                      mb: 2,
                    }}
                  >
                    {action.icon}
                  </Avatar>
                  <Typography variant="h6" gutterBottom>
                    {action.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 2 }}
                  >
                    {action.description}
                  </Typography>
                  <Button
                    variant="contained"
                    size="small"
                    sx={{
                      backgroundColor: action.color,
                      '&:hover': {
                        backgroundColor: action.color,
                        filter: 'brightness(0.9)',
                      },
                    }}
                    startIcon={<PlayArrow />}
                  >
                    {action.action}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Recent Activities */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 2,
                }}
              >
                <Typography variant="h6">
                  Recent Activities
                  {isLoading && (
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      sx={{ ml: 1 }}
                    >
                      (Loading...)
                    </Typography>
                  )}
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small" onClick={fetchRecentActivities}>
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </Box>

              {recentActivities.length === 0 && !isLoading ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No recent activities found.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Start generating tasks or running evaluations to see
                    activities here.
                  </Typography>
                </Box>
              ) : (
                recentActivities.map(activity => (
                  <Box
                    key={activity.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      py: 2,
                      borderBottom: '1px solid #f0f0f0',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Avatar
                      sx={{
                        bgcolor: getStatusColor(activity.status),
                        width: 40,
                        height: 40,
                        mr: 2,
                      }}
                    >
                      {activity.type.charAt(0)}
                    </Avatar>

                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {activity.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {activity.type} • {activity.timestamp}
                      </Typography>
                      {activity.status === 'running' && activity.progress && (
                        <Box sx={{ mt: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={activity.progress}
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ mt: 0.5 }}
                          >
                            {activity.progress}% completed
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={getStatusLabel(activity.status)}
                        size="small"
                        sx={{
                          backgroundColor: getStatusColor(activity.status),
                          color: 'white',
                          fontWeight: 500,
                        }}
                      />
                      <IconButton size="small">
                        <MoreVert />
                      </IconButton>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Overview */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Overview
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Active Tasks
                </Typography>
                <Typography variant="h4" color="primary">
                  24
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Models Evaluated
                </Typography>
                <Typography variant="h4" color="secondary">
                  8
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
                <Typography variant="h4" color="success.main">
                  87%
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Links
              </Typography>

              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1, justifyContent: 'flex-start' }}
                onClick={() => navigate('/results')}
              >
                View All Results
              </Button>

              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1, justifyContent: 'flex-start' }}
                onClick={() => navigate('/convert-data')}
              >
                Data Conversion
              </Button>

              <Button
                fullWidth
                variant="outlined"
                sx={{ justifyContent: 'flex-start' }}
                onClick={() => navigate('/split-data')}
              >
                Split Datasets
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
