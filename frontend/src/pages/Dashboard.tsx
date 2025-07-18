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
  AutoAwesome as AutoIcon,
  Gavel as JudgeIcon,
  Description as ReportIcon,
  History as ActivitiesIcon,
} from '@mui/icons-material';

interface QuickActionCard {
  title: string;
  description: string;
  icon: React.ReactElement;
  action: string;
  path: string;
  color: string;
  size?: 'small' | 'large';
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
      title: 'Auto Workflow',
      description:
        'Complete automated evaluation pipeline from task generation to analysis',
      icon: <AutoIcon sx={{ fontSize: 40 }} />,
      action: 'Start Auto',
      path: '/auto-workflow',
      color: '#673ab7',
      size: 'large',
    },
    {
      title: 'Generate Tasks',
      description: 'Create new evaluation tasks for MCP servers',
      icon: <GenerateIcon sx={{ fontSize: 28 }} />,
      action: 'Generate',
      path: '/generate-tasks',
      color: '#4caf50',
      size: 'small',
    },
    {
      title: 'Verify Tasks',
      description: 'Validate generated tasks against servers',
      icon: <VerifyIcon sx={{ fontSize: 28 }} />,
      action: 'Verify',
      path: '/verify-tasks',
      color: '#2196f3',
      size: 'small',
    },
    {
      title: 'Evaluate Models',
      description: 'Run comprehensive model evaluations',
      icon: <EvaluateIcon sx={{ fontSize: 28 }} />,
      action: 'Evaluate',
      path: '/evaluate',
      color: '#ff9800',
      size: 'small',
    },
    {
      title: 'LLM Judge',
      description: 'AI-powered evaluation and scoring',
      icon: <JudgeIcon sx={{ fontSize: 28 }} />,
      action: 'Judge',
      path: '/judge',
      color: '#e91e63',
      size: 'small',
    },
    {
      title: 'Generate Reports',
      description: 'Create AI-powered analysis reports from evaluation results',
      icon: <ReportIcon sx={{ fontSize: 28 }} />,
      action: 'Generate',
      path: '/generate-report',
      color: '#795548',
      size: 'small',
    },
    {
      title: 'Analyze Results',
      description: 'Deep dive into evaluation metrics',
      icon: <AnalyzeIcon sx={{ fontSize: 28 }} />,
      action: 'Analyze',
      path: '/analyze',
      color: '#9c27b0',
      size: 'small',
    },
  ];

  // Fetch recent activities from API
  const fetchRecentActivities = async () => {
    try {
      const response = await axios.get('/api/recent-activities');
      if (response.data.success) {
        setRecentActivities(response.data.activities || []);
      } else {
        console.error(
          'Failed to fetch recent activities:',
          response.data.error
        );
        // Fallback to demo data if API fails
        const fallbackActivities: RecentActivity[] = [
          {
            id: 'demo-1',
            type: 'API Error',
            title: 'Failed to load recent activities',
            status: 'failed',
            timestamp: new Date().toISOString(),
          },
        ];
        setRecentActivities(fallbackActivities);
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch recent activities:', error);
      // Fallback to demo data if API fails
      const fallbackActivities: RecentActivity[] = [
        {
          id: 'demo-1',
          type: 'Connection Error',
          title: 'Unable to connect to backend',
          status: 'failed',
          timestamp: new Date().toISOString(),
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
        <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
          Your comprehensive MCP evaluation framework dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Designed by
          </Typography>
          <Chip
            label="Salesforce AI Research Team"
            variant="outlined"
            size="small"
            sx={{
              borderColor: '#1976d2',
              color: '#1976d2',
              fontWeight: 600,
              '&:hover': {
                backgroundColor: '#e3f2fd',
              },
            }}
          />
        </Box>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={3}>
          {quickActions.map(action => {
            const gridSize =
              action.size === 'large'
                ? { xs: 12, sm: 12, md: 8, lg: 6 }
                : { xs: 12, sm: 6, md: 4, lg: 3 };

            return (
              <Grid item {...gridSize} key={action.title}>
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
                  <CardContent
                    sx={{
                      textAlign: 'center',
                      p: action.size === 'large' ? 4 : 3,
                      display: 'flex',
                      flexDirection: action.size === 'large' ? 'row' : 'column',
                      alignItems: 'center',
                      gap: action.size === 'large' ? 3 : 0,
                    }}
                  >
                    {action.size === 'large' ? (
                      <>
                        <Avatar
                          sx={{
                            bgcolor: action.color,
                            width: 80,
                            height: 80,
                            flexShrink: 0,
                          }}
                        >
                          {action.icon}
                        </Avatar>
                        <Box sx={{ textAlign: 'left', flex: 1 }}>
                          <Typography
                            variant="h5"
                            gutterBottom
                            sx={{ fontWeight: 600 }}
                          >
                            {action.title}
                          </Typography>
                          <Typography
                            variant="body1"
                            color="text.secondary"
                            sx={{ mb: 3 }}
                          >
                            {action.description}
                          </Typography>
                          <Button
                            variant="contained"
                            size="large"
                            sx={{
                              backgroundColor: action.color,
                              '&:hover': {
                                backgroundColor: action.color,
                                filter: 'brightness(0.9)',
                              },
                              px: 4,
                              py: 1.5,
                            }}
                            startIcon={<PlayArrow />}
                          >
                            {action.action}
                          </Button>
                        </Box>
                      </>
                    ) : (
                      <>
                        <Avatar
                          sx={{
                            bgcolor: action.color,
                            width: 56,
                            height: 56,
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
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
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
                  Total Activities
                </Typography>
                <Typography variant="h4" color="primary">
                  {recentActivities.length}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Running Jobs
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {recentActivities.filter(a => a.status === 'running').length}
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
                <Typography variant="h4" color="success.main">
                  {recentActivities.length > 0
                    ? Math.round(
                        (recentActivities.filter(a => a.status === 'completed')
                          .length /
                          recentActivities.length) *
                          100
                      )
                    : 0}
                  %
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
