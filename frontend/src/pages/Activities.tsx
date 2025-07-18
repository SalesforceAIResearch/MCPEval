import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Avatar,
  Grid,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Refresh,
  Visibility,
  Stop,
  Delete,
  PlayArrow,
  CheckCircle,
  Error,
  Schedule,
  Cancel,
  ExpandMore,
  Terminal,
  Info,
  FolderOpen,
  Launch,
} from '@mui/icons-material';

interface Activity {
  id: string;
  type: string;
  title: string;
  status: 'completed' | 'running' | 'failed' | 'pending' | 'cancelled';
  progress?: number;
  timestamp: string;
  models?: string[];
  num_models?: number;
}

interface JobDetails {
  job_id: string;
  progress: {
    status: string;
    progress: number;
    success?: boolean;
    output?: string;
    error?: string;
    returncode?: number;
  };
  logs: string[];
}

interface TaskProgress {
  current: number;
  total: number;
  phase: string;
  percentage: number;
  hasRealData: boolean;
}

interface ActivityProgress {
  [key: string]: {
    startTime: number;
    lastUpdate: number;
    estimatedProgress: number;
    logCount: number;
    taskProgress?: TaskProgress;
  };
}

const Activities: React.FC = () => {
  const navigate = useNavigate();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(
    null
  );
  const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
  const [detailsDialog, setDetailsDialog] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activityProgress, setActivityProgress] = useState<ActivityProgress>(
    {}
  );
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const parseTaskProgressFromLogs = (logs: string[]): TaskProgress | null => {
    let totalTasks = 0;
    let currentTasks = 0;
    let currentPhase = 'Processing';
    let hasRealData = false;

    // Parse logs in reverse order to get the most recent information
    for (let i = logs.length - 1; i >= 0; i--) {
      const log = logs[i];

      // Task Generation patterns
      let match = log.match(/Generated task (\d+)\/(\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Generating tasks';
        hasRealData = true;
        break;
      }

      match = log.match(/Starting generation of (\d+) tasks/i);
      if (match) {
        totalTasks = parseInt(match[1]);
        currentTasks = 0;
        currentPhase = 'Starting generation';
        hasRealData = true;
        continue; // Don't break, keep looking for progress
      }

      match = log.match(/Task generation complete\. (\d+) tasks saved/i);
      if (match) {
        totalTasks = parseInt(match[1]);
        currentTasks = totalTasks;
        currentPhase = 'Generation complete';
        hasRealData = true;
        break;
      }

      // Task Verification patterns
      match = log.match(/Processing task (\d+)\/(\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Verifying tasks';
        hasRealData = true;
        break;
      }

      match = log.match(/Verified (\d+)\/(\d+) tasks/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Verifying tasks';
        hasRealData = true;
        break;
      }

      match = log.match(/Verifying task (\d+)\/(\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Verifying tasks';
        hasRealData = true;
        break;
      }

      // Model Evaluation patterns
      match = log.match(/Evaluating task (\d+)\/(\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Evaluating models';
        hasRealData = true;
        break;
      }

      match = log.match(/Processing task (\d+) of (\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Processing tasks';
        hasRealData = true;
        break;
      }

      match = log.match(/Tasks evaluated: (\d+)/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        // Look for total in earlier logs if not found
        if (!totalTasks) {
          for (let j = 0; j < i; j++) {
            const totalMatch = logs[j].match(
              /Starting generation of (\d+) tasks/i
            );
            if (totalMatch) {
              totalTasks = parseInt(totalMatch[1]);
              break;
            }
          }
        }
        currentPhase = 'Evaluation complete';
        hasRealData = true;
        break;
      }

      // Analysis patterns
      match = log.match(/Analyzing (\d+)\/(\d+) results/i);
      if (match) {
        currentTasks = parseInt(match[1]);
        totalTasks = parseInt(match[2]);
        currentPhase = 'Analyzing results';
        hasRealData = true;
        break;
      }

      // Phase detection without numbers
      if (log.toLowerCase().includes('starting generation')) {
        currentPhase = 'Starting generation';
      } else if (log.toLowerCase().includes('generation complete')) {
        currentPhase = 'Generation complete';
      } else if (log.toLowerCase().includes('starting verification')) {
        currentPhase = 'Starting verification';
      } else if (log.toLowerCase().includes('verification complete')) {
        currentPhase = 'Verification complete';
      } else if (log.toLowerCase().includes('starting evaluation')) {
        currentPhase = 'Starting evaluation';
      } else if (log.toLowerCase().includes('evaluation complete')) {
        currentPhase = 'Evaluation complete';
      } else if (log.toLowerCase().includes('starting analysis')) {
        currentPhase = 'Starting analysis';
      } else if (log.toLowerCase().includes('analysis complete')) {
        currentPhase = 'Analysis complete';
      }
    }

    if (hasRealData && totalTasks > 0) {
      const percentage = Math.round((currentTasks / totalTasks) * 100);
      return {
        current: currentTasks,
        total: totalTasks,
        phase: currentPhase,
        percentage: percentage,
        hasRealData: true,
      };
    }

    // If we found a phase but no task counts, return phase info only
    if (currentPhase !== 'Processing') {
      return {
        current: 0,
        total: 0,
        phase: currentPhase,
        percentage: 0,
        hasRealData: false,
      };
    }

    return null;
  };

  const fetchActivities = async () => {
    try {
      const response = await axios.get('/api/recent-activities');
      if (response.data.success) {
        const newActivities = response.data.activities;
        setActivities(newActivities);
        setError(null);

        // Update activity progress tracking
        updateActivityProgress(newActivities);
      } else {
        setError(response.data.error || 'Failed to fetch activities');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch activities');
    } finally {
      setLoading(false);
    }
  };

  const updateActivityProgress = (activities: Activity[]) => {
    const currentTime = Date.now();

    setActivityProgress(prev => {
      const updated = { ...prev };

      activities.forEach(activity => {
        if (activity.status === 'running') {
          if (!updated[activity.id]) {
            // First time seeing this running job - fetch details to get logs
            updated[activity.id] = {
              startTime: currentTime,
              lastUpdate: currentTime,
              estimatedProgress: 0,
              logCount: 0,
            };
            // Fetch job details to get logs for parsing
            fetchJobDetailsForProgress(activity.id);
          } else {
            // Update existing running job
            const timeSinceStart = currentTime - updated[activity.id].startTime;

            // Use real progress if available, otherwise time-based estimation
            const backendProgress = activity.progress || 0;

            if (
              backendProgress > 0 ||
              updated[activity.id].taskProgress?.hasRealData
            ) {
              // We have real progress from backend or parsed logs
              updated[activity.id] = {
                ...updated[activity.id],
                lastUpdate: currentTime,
                estimatedProgress:
                  backendProgress ||
                  updated[activity.id].taskProgress?.percentage ||
                  0,
              };
            } else {
              // No real progress yet, use time-based estimation
              const estimatedDuration = 3 * 60 * 1000; // 3 minutes
              const timeBasedProgress = Math.min(
                85,
                (timeSinceStart / estimatedDuration) * 100
              );

              updated[activity.id] = {
                ...updated[activity.id],
                lastUpdate: currentTime,
                estimatedProgress: Math.min(90, timeBasedProgress), // Cap at 90% until completion
              };
            }
          }
        } else if (activity.status === 'completed') {
          // Job completed, set progress to 100%
          if (updated[activity.id]) {
            updated[activity.id].estimatedProgress = 100;
          }
        } else if (
          updated[activity.id] &&
          (activity.status === 'failed' || activity.status === 'cancelled')
        ) {
          // Job failed or cancelled, clean up tracking
          delete updated[activity.id];
        }
      });

      // Clean up old entries for jobs that are no longer in the list
      const currentJobIds = new Set(activities.map(a => a.id));
      Object.keys(updated).forEach(jobId => {
        if (!currentJobIds.has(jobId)) {
          delete updated[jobId];
        }
      });

      return updated;
    });
  };

  const fetchJobDetailsForProgress = async (jobId: string) => {
    try {
      const response = await axios.get(`/api/job/${jobId}`);
      if (response.data && response.data.logs) {
        const taskProgress = parseTaskProgressFromLogs(response.data.logs);

        setActivityProgress(prev => ({
          ...prev,
          [jobId]: {
            ...prev[jobId],
            logCount: response.data.logs.length,
            taskProgress: taskProgress || undefined,
          },
        }));
      }
    } catch (err) {
      console.error('Failed to fetch job details for progress:', err);
    }
  };

  const fetchJobDetails = async (jobId: string) => {
    try {
      const response = await axios.get(`/api/job/${jobId}`);
      if (response.data) {
        setJobDetails(response.data);

        // Update progress tracking with task progress
        if (response.data.logs) {
          const taskProgress = parseTaskProgressFromLogs(response.data.logs);

          setActivityProgress(prev => ({
            ...prev,
            [jobId]: {
              ...prev[jobId],
              logCount: response.data.logs.length,
              taskProgress: taskProgress || undefined,
            },
          }));
        }
      }
    } catch (err) {
      console.error('Failed to fetch job details:', err);
    }
  };

  const handleViewDetails = async (activity: Activity) => {
    setSelectedActivity(activity);
    await fetchJobDetails(activity.id);
    setDetailsDialog(true);
  };

  const handleStopJob = async (jobId: string) => {
    try {
      await axios.post(`/api/job/${jobId}/stop`);
      // Refresh activities after stopping
      await fetchActivities();
    } catch (err) {
      console.error('Failed to stop job:', err);
    }
  };

  const getOutputFiles = (jobDetails: JobDetails | null): string[] => {
    if (!jobDetails) return [];

    const outputFiles: string[] = [];

    // Try to get output files from job metadata stored in logs
    const metadataLog = jobDetails.logs.find(
      log => log.includes('output_path') || log.includes('output_files')
    );
    if (metadataLog) {
      try {
        // Extract file paths from metadata
        const pathMatches = metadataLog.match(/data\/[^"\s]+/g);
        if (pathMatches) {
          outputFiles.push(...pathMatches);
        }
      } catch (err) {
        console.error('Error parsing metadata log:', err);
      }
    }

    // Also check for common output patterns in logs
    jobDetails.logs.forEach(log => {
      // Look for file paths in logs
      const filePathMatches = log.match(
        /(?:saved to|output|generated).*?data\/[^"\s]+/gi
      );
      if (filePathMatches) {
        filePathMatches.forEach(match => {
          const pathMatch = match.match(/data\/[^"\s]+/);
          if (pathMatch) {
            outputFiles.push(pathMatch[0]);
          }
        });
      }
    });

    return Array.from(new Set(outputFiles)); // Remove duplicates
  };

  const handleViewOutputFiles = (activity: Activity) => {
    const outputFiles = getOutputFiles(jobDetails);
    if (outputFiles.length > 0) {
      // Navigate to DataFiles with the first output file's directory
      const firstFile = outputFiles[0];
      const dirPath = firstFile.substring(0, firstFile.lastIndexOf('/'));
      navigate(
        `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(firstFile)}`
      );
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'running':
        return <PlayArrow color="primary" />;
      case 'failed':
        return <Error color="error" />;
      case 'pending':
        return <Schedule color="warning" />;
      case 'cancelled':
        return <Cancel color="disabled" />;
      default:
        return <Info color="disabled" />;
    }
  };

  const getProgressValue = (activity: Activity): number => {
    if (activity.status === 'completed') {
      return 100;
    }

    if (activity.status === 'running') {
      // Check if we have task progress data
      const taskProgress = activityProgress[activity.id]?.taskProgress;
      if (taskProgress?.hasRealData) {
        return taskProgress.percentage;
      }

      // Prioritize real backend progress over time-based estimation
      const backendProgress = activity.progress || 0;
      const estimatedProgress =
        activityProgress[activity.id]?.estimatedProgress || 0;

      // If backend has meaningful progress (> 0), use it
      // Otherwise fall back to time-based estimation
      if (backendProgress > 0) {
        return backendProgress;
      }

      return estimatedProgress;
    }

    return activity.progress || 0;
  };

  const getProgressLabel = (activity: Activity): string => {
    if (activity.status === 'completed') {
      return '100% completed';
    }

    if (activity.status === 'running') {
      const progressValue = getProgressValue(activity);
      const taskProgress = activityProgress[activity.id]?.taskProgress;

      if (taskProgress?.hasRealData && taskProgress.total > 0) {
        // Show task count and phase
        return `${taskProgress.current}/${taskProgress.total} tasks (${taskProgress.phase})`;
      } else if (taskProgress?.phase && taskProgress.phase !== 'Processing') {
        // Show phase only
        return `${taskProgress.phase}...`;
      } else if (progressValue < 10) {
        return 'Starting...';
      } else {
        // Show percentage with indicator
        const isRealProgress = (activity.progress || 0) > 0;
        return `${Math.round(progressValue)}% ${isRealProgress ? 'completed' : 'estimated'}`;
      }
    }

    return `${getProgressValue(activity)}% completed`;
  };

  const shouldShowProgress = (activity: Activity): boolean => {
    return (
      activity.status === 'running' ||
      (activity.status === 'completed' && activity.progress !== undefined)
    );
  };

  const formatTimestamp = (timestamp: string) => {
    if (timestamp === 'Just now') return timestamp;
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getProgressColor = (
    activity: Activity
  ): 'primary' | 'secondary' | 'success' => {
    if (activity.status === 'completed') {
      return 'success';
    }
    if (activity.status === 'running') {
      return 'primary';
    }
    return 'secondary';
  };

  const hasRealProgress = (activity: Activity): boolean => {
    const taskProgress = activityProgress[activity.id]?.taskProgress;
    return (activity.progress || 0) > 0 || taskProgress?.hasRealData === true;
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchActivities();
        // Also refresh job details for running activities to get updated logs
        activities.forEach(activity => {
          if (activity.status === 'running') {
            fetchJobDetailsForProgress(activity.id);
          }
        });
      }, 2000); // Faster refresh for better progress tracking
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, activities]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          Recent Activities
        </Typography>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="h4" component="h1">
          Recent Activities
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
          >
            <IconButton
              onClick={() => setAutoRefresh(!autoRefresh)}
              color={autoRefresh ? 'primary' : 'default'}
            >
              <Schedule />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchActivities} color="primary">
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {activities.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Recent Activities
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Activities will appear here when you run tasks, generate reports, or
            perform other operations.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {activities.map(activity => {
            const progressValue = getProgressValue(activity);
            const showProgress = shouldShowProgress(activity);
            const progressLabel = getProgressLabel(activity);

            return (
              <Grid item xs={12} key={activity.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'transparent' }}>
                        {activity.status === 'running' ? (
                          <CircularProgress size={24} />
                        ) : (
                          getStatusIcon(activity.status)
                        )}
                      </Avatar>

                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom>
                          {activity.title}
                        </Typography>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          gutterBottom
                        >
                          {activity.type} •{' '}
                          {formatTimestamp(activity.timestamp)}
                          {activity.models && activity.models.length > 0 && (
                            <span>
                              {' • '}
                              <strong>
                                {activity.models.length === 1
                                  ? activity.models[0]
                                  : `${activity.models.length} models`}
                              </strong>
                            </span>
                          )}
                        </Typography>

                        {showProgress && (
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress
                              variant={
                                activity.status === 'running' &&
                                progressValue < 10
                                  ? 'indeterminate'
                                  : 'determinate'
                              }
                              value={progressValue}
                              color={getProgressColor(activity)}
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ mt: 0.5, display: 'block' }}
                            >
                              {progressLabel}
                              {activity.status === 'running' &&
                                hasRealProgress(activity) && (
                                  <span
                                    style={{
                                      color: '#4caf50',
                                      marginLeft: '4px',
                                    }}
                                  >
                                    ●
                                  </span>
                                )}
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      <Box
                        sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                      >
                        <Chip
                          label={
                            activity.status.charAt(0).toUpperCase() +
                            activity.status.slice(1)
                          }
                          color={getStatusColor(activity.status) as any}
                          size="small"
                        />

                        <Tooltip title="View Details">
                          <IconButton
                            onClick={() => handleViewDetails(activity)}
                            size="small"
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>

                        {activity.status === 'completed' && (
                          <Tooltip title="View Output Files">
                            <IconButton
                              onClick={() => {
                                // We need to fetch job details first, then navigate
                                fetchJobDetails(activity.id).then(() => {
                                  handleViewOutputFiles(activity);
                                });
                              }}
                              size="small"
                              color="primary"
                            >
                              <FolderOpen />
                            </IconButton>
                          </Tooltip>
                        )}

                        {activity.status === 'running' && (
                          <Tooltip title="Stop Job">
                            <IconButton
                              onClick={() => handleStopJob(activity.id)}
                              size="small"
                              color="error"
                            >
                              <Stop />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Job Details Dialog */}
      <Dialog
        open={detailsDialog}
        onClose={() => setDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Terminal />
          Job Details: {selectedActivity?.title}
        </DialogTitle>
        <DialogContent>
          {jobDetails && (
            <Box sx={{ mt: 2 }}>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">Job Status</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>
                            <strong>Job ID</strong>
                          </TableCell>
                          <TableCell>{jobDetails.job_id}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>
                            <strong>Status</strong>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={jobDetails.progress.status}
                              color={
                                getStatusColor(
                                  jobDetails.progress.status
                                ) as any
                              }
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>
                            <strong>Progress</strong>
                          </TableCell>
                          <TableCell>
                            {selectedActivity &&
                              getProgressLabel(selectedActivity)}
                          </TableCell>
                        </TableRow>
                        {selectedActivity?.models &&
                          selectedActivity.models.length > 0 && (
                            <TableRow>
                              <TableCell>
                                <strong>Models</strong>
                              </TableCell>
                              <TableCell>
                                {selectedActivity.models.length === 1
                                  ? selectedActivity.models[0]
                                  : `${selectedActivity.models.length} models: ${selectedActivity.models.join(', ')}`}
                              </TableCell>
                            </TableRow>
                          )}
                        {jobDetails.progress.returncode !== undefined && (
                          <TableRow>
                            <TableCell>
                              <strong>Return Code</strong>
                            </TableCell>
                            <TableCell>
                              {jobDetails.progress.returncode}
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Job Logs ({jobDetails.logs.length} entries)
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Paper
                    sx={{
                      p: 2,
                      maxHeight: 400,
                      overflow: 'auto',
                      backgroundColor: '#f5f5f5',
                      fontFamily: 'monospace',
                    }}
                  >
                    {jobDetails.logs.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        No logs available
                      </Typography>
                    ) : (
                      jobDetails.logs.map((log, index) => (
                        <Box key={index} sx={{ mb: 0.5 }}>
                          <Typography
                            variant="caption"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.8rem',
                              color: log.includes('Error:')
                                ? 'error.main'
                                : 'text.primary',
                            }}
                          >
                            {log}
                          </Typography>
                        </Box>
                      ))
                    )}
                  </Paper>
                </AccordionDetails>
              </Accordion>

              {jobDetails.progress.output && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6">Info</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Paper
                      sx={{
                        p: 2,
                        maxHeight: 300,
                        overflow: 'auto',
                        backgroundColor: '#f5f5f5',
                        fontFamily: 'monospace',
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.8rem',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {jobDetails.progress.output}
                      </Typography>
                    </Paper>
                  </AccordionDetails>
                </Accordion>
              )}

              {jobDetails.progress.error && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6" color="error">
                      Messages
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Paper
                      sx={{
                        p: 2,
                        maxHeight: 300,
                        overflow: 'auto',
                        backgroundColor: '#ffebee',
                        fontFamily: 'monospace',
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.8rem',
                          color: 'error.main',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {jobDetails.progress.error}
                      </Typography>
                    </Paper>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {jobDetails && getOutputFiles(jobDetails).length > 0 && (
            <Button
              onClick={() => {
                handleViewOutputFiles(selectedActivity!);
                setDetailsDialog(false);
              }}
              startIcon={<Launch />}
              color="primary"
            >
              View Output Files
            </Button>
          )}
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Activities;
