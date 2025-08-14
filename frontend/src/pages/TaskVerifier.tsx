import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Box,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Chip,
} from '@mui/material';
import {
  CheckCircle as VerifyIcon,
  PlayArrow,
  Stop,
  Upload,
  Download,
  Info,
  Warning,
  FolderOpen,
  Launch,
  Refresh,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { ServerConfig } from '../components/types';
import UnifiedMCPServerConfiguration from '../components/UnifiedMCPServerConfiguration';

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
}

interface VerificationProgress {
  isRunning: boolean;
  currentTask: number;
  totalTasks: number;
  passedTasks: number;
  failedTasks: number;
  status: string;
  logs: string[];
  jobId?: string;
  currentTaskName?: string;
  inputFile?: string;
  outputFile?: string;
}

const TaskVerifier: React.FC = () => {
  const navigate = useNavigate();
  const [servers, setServers] = useState<ServerConfig[]>([{ path: '', args: [], env: {} }]);
  const [domainName, setDomainName] = useState('');
  const [tasksFileName, setTasksFileName] = useState('');
  const [outputFileName, setOutputFileName] = useState('');
  const [model, setModel] = useState('gpt-4.1-2025-04-14');
  const [numTasks, setNumTasks] = useState(-1);
  const [apiKey, setApiKey] = useState('');

  // File listing states
  const [tasksFiles, setTasksFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const [progress, setProgress] = useState<VerificationProgress>({
    isRunning: false,
    currentTask: 0,
    totalTasks: 0,
    passedTasks: 0,
    failedTasks: 0,
    status: '',
    logs: [],
    jobId: undefined,
    currentTaskName: undefined,
    inputFile: undefined,
    outputFile: undefined,
  });

  // Ref to track the active polling interval
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollErrorCountRef = useRef<number>(0);

  // Cleanup effect to prevent memory leaks
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Load files when domain changes
  useEffect(() => {
    if (domainName.trim()) {
      fetchFiles(domainName);
    } else {
      setTasksFiles([]);
      setTasksFileName('');
    }
  }, [domainName]);

  // Server configuration is handled via UnifiedMCPServerConfiguration

  const fetchFiles = async (domain: string) => {
    if (!domain.trim()) {
      setTasksFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Use correct relative path from workspace root
      const tasksPath = `data/${domain}/tasks`;

      const response = await fetch(`/api/files?directory=${tasksPath}`);

      if (response.ok) {
        const data = await response.json();
        setTasksFiles(data.files || []);
      } else {
        console.error('Failed to fetch tasks files');
        setTasksFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setTasksFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const getOutputFiles = (): string[] => {
    const outputFiles: string[] = [];
    const logs = progress.logs || [];

    // Try to get output files from job metadata stored in logs
    const metadataLog = logs.find(
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
    logs.forEach(log => {
      // Look for file paths in logs
      const filePathMatches = log.match(
        /(?:saved to|output|generated|verified).*?data\/[^"\s]+/gi
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

  const handleViewOutputFiles = () => {
    const outputFiles = getOutputFiles();
    if (outputFiles.length > 0) {
      // Navigate to DataFiles with the first output file's directory
      const firstFile = outputFiles[0];
      const dirPath = firstFile.substring(0, firstFile.lastIndexOf('/'));
      navigate(
        `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(firstFile)}`
      );
    } else if (progress.outputFile) {
      // Fallback: If no files found in logs, try to use outputFile
      // Check if outputFile is a file or directory
      const outputPath = progress.outputFile;
      if (outputPath.includes('.')) {
        // It's likely a file path, extract the directory
        const dirPath = outputPath.substring(0, outputPath.lastIndexOf('/'));
        navigate(
          `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(outputPath)}`
        );
      } else {
        // It's likely a directory path
        navigate(`/data-files?path=${encodeURIComponent(outputPath)}`);
      }
    }
  };

  const handleVerify = async () => {
    if (!domainName.trim() || !tasksFileName) {
      return;
    }

    // Find the selected file to get its full path
    const selectedTasksFile = tasksFiles.find(f => f.name === tasksFileName);

    if (!selectedTasksFile) {
      setProgress({
        isRunning: false,
        status: 'Error: Selected tasks file not found',
        logs: ['Error: Selected tasks file not found'],
        currentTask: 0,
        totalTasks: 0,
        passedTasks: 0,
        failedTasks: 0,
      });
      return;
    }

    const tasksFilePath = selectedTasksFile.path;
    const outputFilePath = outputFileName
      ? `data/${domainName}/verified_tasks/${outputFileName}`
      : `data/${domainName}/verified_tasks/verified_${tasksFileName}`;

    // Reset error count for new verification
    pollErrorCountRef.current = 0;

    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks: numTasks > 0 ? numTasks : 0, // Set totalTasks from numTasks
      passedTasks: 0,
      failedTasks: 0,
      status: 'Starting task verification...',
      logs: ['Initializing task verification...'],
      jobId: undefined,
      inputFile: tasksFilePath,
      outputFile: outputFilePath,
    });

    try {
      const payload = {
        servers: servers
          .filter(s => s.path.trim())
          .map(server => ({
            path: server.path,
            args: server.args,
            env: server.env,
          })),
        domain_name: domainName,
        tasks_filename: tasksFileName,
        output_filename: outputFileName,
        model,
        num_tasks: numTasks,
        api_key: apiKey || null,
      };

      // Debug: Log payload to verify environment variables are included
      console.log('TaskVerifier payload:', JSON.stringify(payload, null, 2));

      // Call the backend API
      const response: Response = await fetch('/api/verify-tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            `Server error: ${response.status} ${response.statusText}`
        );
      }

      const data: any = await response.json();

      const jobId = data.job_id;
      const inputFile = data.input_file;
      const outputFile = data.output_file;
      const responseDomainName = data.domain_name;

      setProgress(prev => ({
        ...prev,
        status: 'Task verification started successfully',
        logs: [
          ...prev.logs,
          'Task verification job started, tracking progress...',
          inputFile ? `Loading tasks from: ${inputFile}` : '',
          outputFile ? `Results will be saved to: ${outputFile}` : '',
        ],
        jobId: jobId,
        inputFile: inputFile,
        outputFile: outputFile,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/job/${jobId}`);
          const statusData = await statusResponse.json();

          if (statusResponse.ok && statusData) {
            // Reset error count on successful poll
            pollErrorCountRef.current = 0;

            const { progress: jobProgress, logs: jobLogs } = statusData;

            // Parse logs to extract verification progress - use backend progress + log parsing
            const parseProgressFromLogs = (logs: string[]) => {
              if (!logs || logs.length === 0) {
                return {
                  currentTask: 0,
                  totalTasks: numTasks > 0 ? numTasks : 0,
                  passedTasks: 0,
                  failedTasks: 0,
                  currentTaskName: undefined,
                };
              }

              const allLogs = logs.join('\n');

              // Look for total tasks information
              const totalTasksMatch =
                allLogs.match(/Verifying (\d+) tasks?/i) ||
                allLogs.match(/Starting verification of (\d+) tasks/i) ||
                allLogs.match(/Loaded (\d+) tasks from/i);
              const totalTasks = totalTasksMatch
                ? parseInt(totalTasksMatch[1])
                : numTasks > 0
                  ? numTasks
                  : 0;

              // Look for current task progress patterns - use actual CLI output patterns
              const taskProgressPatterns = [
                /Starting verification for task (\d+)\/(\d+)/g,
                /Successfully verified task (\d+)\/(\d+)/g,
                /Task (\d+)\/(\d+) failed verification/g,
                /Error processing task (\d+)\/(\d+)/g,
              ];

              let currentTask = 0;
              for (const pattern of taskProgressPatterns) {
                const progressMatches = allLogs.match(pattern);
                if (progressMatches && progressMatches.length > 0) {
                  const lastMatch = progressMatches[progressMatches.length - 1];
                  const match = lastMatch.match(/(\d+)\/(\d+)/);
                  if (match) {
                    currentTask = parseInt(match[1]);
                    break;
                  }
                }
              }

              // Count passed and failed tasks using actual CLI output patterns
              const passedMatches = allLogs.match(
                /Successfully verified task \d+\/\d+/g
              );
              const passedTasks = passedMatches ? passedMatches.length : 0;

              const failedMatches = allLogs.match(
                /Task \d+\/\d+ failed verification/g
              );
              const failedTasks = failedMatches ? failedMatches.length : 0;

              // Look for current task name from logs
              const taskNameMatches = allLogs.match(
                /Starting verification for task \d+\/\d+.*?:\s*(.+)/g
              );
              let currentTaskName = undefined;
              if (taskNameMatches && taskNameMatches.length > 0) {
                const lastMatch = taskNameMatches[taskNameMatches.length - 1];
                const nameMatch = lastMatch.match(/:\s*(.+)$/);
                if (nameMatch) {
                  currentTaskName = nameMatch[1].trim();
                }
              }

              // If verification is complete, set current task to total
              if (
                allLogs.includes('Task verification complete') ||
                allLogs.includes('completed successfully')
              ) {
                currentTask = totalTasks;
              }

              return {
                currentTask,
                totalTasks,
                passedTasks,
                failedTasks,
                currentTaskName,
              };
            };

            const {
              currentTask,
              totalTasks,
              passedTasks,
              failedTasks,
              currentTaskName,
            } = parseProgressFromLogs(jobLogs);

            // Debug logging to help troubleshoot (only in development)
            if (process.env.NODE_ENV === 'development') {
              console.log(
                'TaskVerifier status:',
                jobProgress.status,
                'backend progress:',
                jobProgress.progress,
                'currentTask:',
                currentTask,
                'totalTasks:',
                totalTasks
              );
            }

            // Use backend progress if available, otherwise fall back to log parsing
            const backendProgress = jobProgress.progress || 0;
            const passedPercentage = totalTasks > 0 ? Math.round((passedTasks / totalTasks) * 100) : 0;
            const progressPercentage = backendProgress > 0 ? backendProgress : passedPercentage;

            setProgress(prev => ({
              ...prev,
              status:
                jobProgress.status === 'running'
                  ? currentTask > 0
                    ? `Processing task ${currentTask}/${totalTasks} | ${passedTasks} passed (${passedPercentage}%)`
                    : 'Initializing verification...'
                  : jobProgress.status === 'completed'
                    ? `Verification completed! ${passedTasks}/${totalTasks} tasks passed (${passedPercentage}%)`
                    : jobProgress.status === 'failed'
                      ? 'Verification failed'
                      : jobProgress.status === 'cancelled'
                        ? 'Verification cancelled'
                        : prev.status,
              logs: jobLogs || prev.logs,
              currentTask:
                jobProgress.status === 'completed' ? totalTasks : currentTask,
              totalTasks: totalTasks,
              passedTasks: passedTasks,
              failedTasks: failedTasks,
              currentTaskName: currentTaskName,
            }));

            // Stop polling when job is complete
            if (
              jobProgress.status === 'completed' ||
              jobProgress.status === 'failed' ||
              jobProgress.status === 'cancelled'
            ) {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
              }
              setProgress(prev => ({
                ...prev,
                isRunning: false,
                currentTask:
                  jobProgress.status === 'completed'
                    ? prev.totalTasks
                    : prev.currentTask,
                currentTaskName:
                  jobProgress.status === 'completed'
                    ? undefined
                    : prev.currentTaskName,
              }));
            }
          }
        } catch (pollError) {
          console.error('Error polling job status:', pollError);
          pollErrorCountRef.current++;

          // Stop polling if there are too many consecutive errors (more than 5)
          if (pollErrorCountRef.current > 5) {
            console.error('Too many polling errors, stopping verification');
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            setProgress(prev => ({
              ...prev,
              isRunning: false,
              status: 'Verification failed due to connection issues',
              logs: [
                ...prev.logs,
                'Verification stopped due to repeated connection errors',
              ],
            }));
          }
        }
      }, 2000); // Poll every 2 seconds

      // Set a timeout to stop polling after 30 minutes
      timeoutRef.current = setTimeout(
        () => {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Verification timed out',
            logs: [...prev.logs, 'Verification timed out after 30 minutes'],
          }));
        },
        30 * 60 * 1000
      );
    } catch (error) {
      let errorMessage = 'An unknown error occurred';
      if (error instanceof Error) {
        if (error.message.includes('Failed to fetch')) {
          errorMessage =
            'Cannot connect to backend server. Please make sure the backend is running on port 22358.';
        } else {
          errorMessage = error.message;
        }
      }

      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: `Error: ${errorMessage}`,
        logs: [...prev.logs, `Error: ${errorMessage}`],
      }));
    }
  };

  const handleStop = async () => {
    // Clear polling interval and timeout
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // Try to kill the job on the backend if we have a job ID
    if (progress.jobId) {
      try {
        const response = await fetch(`/api/job/${progress.jobId}/kill`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Verification cancelled by user',
            logs: [...prev.logs, 'Verification cancelled by user'],
          }));
        } else {
          const errorData = await response.json().catch(() => ({}));
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Verification stopped (cancel failed)',
            logs: [
              ...prev.logs,
              `Cancel failed: ${errorData.error || 'Unknown error'}`,
              'Verification stopped locally',
            ],
          }));
        }
      } catch (error) {
        console.error('Error cancelling job:', error);
        const errorMessage =
          error instanceof Error ? error.message : 'Unknown error';
        setProgress(prev => ({
          ...prev,
          isRunning: false,
          status: 'Verification stopped (cancel failed)',
          logs: [
            ...prev.logs,
            `Cancel failed: ${errorMessage}`,
            'Verification stopped locally',
          ],
        }));
      }
    } else {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'Verification stopped by user',
        logs: [...prev.logs, 'Verification stopped by user'],
      }));
    }
  };

  const isConfigValid = () => {
    return (
      servers.some(s => s.path.trim()) &&
      domainName.trim() &&
      tasksFileName.trim() &&
      tasksFiles.some(f => f.name === tasksFileName)
    );
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          ✅ Verify Tasks
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Validate generated tasks against MCP servers to ensure they can be
          successfully executed
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Verification Configuration
              </Typography>

              {/* Main Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Main Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Domain Name"
                    value={domainName}
                    onChange={e => setDomainName(e.target.value)}
                    placeholder="healthcare"
                    helperText="The domain/server name (e.g., healthcare, sports, yfinance)"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="Refresh file list">
                      <IconButton
                        onClick={() => fetchFiles(domainName)}
                        disabled={!domainName.trim() || loadingFiles}
                        size="small"
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                    <Typography variant="body2" color="text.secondary">
                      {loadingFiles
                        ? 'Loading files...'
                        : 'Click to refresh file list'}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Tasks File</InputLabel>
                    <Select
                      value={tasksFileName}
                      onChange={e => setTasksFileName(e.target.value)}
                      label="Tasks File"
                      disabled={
                        !domainName.trim() ||
                        tasksFiles.length === 0 ||
                        loadingFiles
                      }
                    >
                      {tasksFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/tasks/${tasksFileName || 'select_file.jsonl'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Number of Tasks to Verify"
                    value={numTasks}
                    onChange={e => setNumTasks(parseInt(e.target.value) || -1)}
                    helperText="Use -1 to verify all tasks"
                    inputProps={{ min: -1, max: 1000 }}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Server Configuration */}
              <UnifiedMCPServerConfiguration
                servers={servers}
                onServersChange={(updated: any[]) =>
                  setServers(
                    updated.map((s: any) => ({
                      path: s.path || '',
                      args: Array.isArray(s.args) ? s.args : [],
                      env: s.env || {},
                    }))
                  )
                }
                title="MCP Servers"
                subtitle="Configure or import servers for task verification"
                required
              />

              <Divider sx={{ my: 3 }} />

              {/* Output Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Output Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Output File Name (Optional)"
                    value={outputFileName}
                    onChange={e => setOutputFileName(e.target.value)}
                    placeholder="verified_tasks.jsonl"
                    helperText={
                      domainName
                        ? `→ workspace/data/${domainName}/verified_tasks/${outputFileName || `verified_${tasksFileName || 'tasks.jsonl'}`}`
                        : 'Auto-generated if empty'
                    }
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Verification Settings */}
              <Typography variant="subtitle1" gutterBottom>
                Verification Settings
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Model"
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    placeholder="Enter model name (e.g., gpt-4.1-2025-04-14)"
                    helperText="Specify the AI model to use for verification"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="OpenAI API Key (Optional)"
                    type="password"
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    helperText="Uses OPENAI_API_KEY env var if not provided"
                  />
                </Grid>
              </Grid>

              {/* Action Buttons */}
              <Box
                sx={{
                  display: 'flex',
                  gap: 2,
                  justifyContent: 'flex-end',
                  mt: 3,
                }}
              >
                <Button
                  variant="outlined"
                  startIcon={<Upload />}
                  onClick={() => {
                    // TODO: Implement file upload
                    console.log('Upload tasks file');
                  }}
                >
                  Upload Tasks File
                </Button>
                <Button
                  variant="contained"
                  onClick={progress.isRunning ? handleStop : handleVerify}
                  disabled={!progress.isRunning && !isConfigValid()}
                  startIcon={progress.isRunning ? <Stop /> : <VerifyIcon />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Verification' : 'Verify Tasks'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Progress Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Verification Progress
              </Typography>

              {progress.isRunning && (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant={
                      progress.totalTasks === 0
                        ? 'indeterminate'
                        : 'determinate'
                    }
                    value={
                      progress.totalTasks === 0
                        ? 0
                        : (progress.passedTasks / progress.totalTasks) * 100
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.passedTasks} / {progress.totalTasks} tasks passed ({progress.totalTasks > 0 ? Math.round((progress.passedTasks / progress.totalTasks) * 100) : 0}%)
                  </Typography>

                  {progress.currentTask > 0 && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mt: 0.5, fontSize: '0.75rem' }}
                    >
                      Currently processing: {progress.currentTask} / {progress.totalTasks}
                    </Typography>
                  )}

                  {progress.currentTaskName && (
                    <Typography
                      variant="body2"
                      color="primary"
                      sx={{
                        mt: 1,
                        fontStyle: 'italic',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Current: {progress.currentTaskName}
                    </Typography>
                  )}
                </Box>
              )}

              {!progress.isRunning && progress.totalTasks > 0 && (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={progress.totalTasks > 0 ? (progress.passedTasks / progress.totalTasks) * 100 : 0}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.passedTasks} / {progress.totalTasks} tasks passed ({progress.totalTasks > 0 ? Math.round((progress.passedTasks / progress.totalTasks) * 100) : 0}%)
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 0.5, fontSize: '0.75rem' }}
                  >
                    Verification completed: {progress.currentTask} / {progress.totalTasks} tasks processed
                  </Typography>
                </Box>
              )}

              {(progress.passedTasks > 0 || progress.failedTasks > 0) && (
                <Box sx={{ mb: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main">
                          {progress.passedTasks}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Passed
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="error.main">
                          {progress.failedTasks}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Failed
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Status:</strong> {progress.status || 'Ready to verify'}
              </Typography>

              {/* Show View Files button prominently when verification is complete */}
              {!progress.isRunning &&
                progress.totalTasks > 0 &&
                (getOutputFiles().length > 0 || progress.outputFile) && (
                  <Box sx={{ mt: 2, mb: 2 }}>
                    <Tooltip title="Click to open the verified task files in the Data Files page">
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<Launch />}
                        onClick={handleViewOutputFiles}
                        color="success"
                        size="small"
                      >
                        📁 Open Verified Files
                      </Button>
                    </Tooltip>
                  </Box>
                )}

              {progress.isRunning && progress.totalTasks > 0 && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Progress:</strong>{' '}
                  {progress.currentTask > 0
                    ? `${progress.passedTasks} passed, ${progress.failedTasks} failed, ${Math.max(0, progress.totalTasks - progress.passedTasks - progress.failedTasks)} pending`
                    : 'Initializing...'}
                </Typography>
              )}

              {/* Show predicted or actual save path */}
              {(progress.inputFile || (domainName && tasksFileName)) && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Input:</strong>{' '}
                  {progress.inputFile ||
                    `workspace/data/${domainName}/tasks/${tasksFileName}`}
                </Typography>
              )}

              {(progress.outputFile || domainName) && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  <strong>Output:</strong>{' '}
                  {(() => {
                    const outputFiles = getOutputFiles();
                    if (outputFiles.length > 0) {
                      const firstFile = outputFiles[0];
                      const dirPath = firstFile.substring(
                        0,
                        firstFile.lastIndexOf('/')
                      );
                      return `${dirPath}/ (${outputFiles.length} file${outputFiles.length > 1 ? 's' : ''})`;
                    }
                    return (
                      progress.outputFile ||
                      `workspace/data/${domainName}/verified_tasks/${outputFileName || `verified_${tasksFileName || 'tasks.jsonl'}`}`
                    );
                  })()}
                </Typography>
              )}

              {progress.logs.length > 0 && (
                <Box
                  sx={{
                    maxHeight: 300,
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5',
                    p: 1,
                    borderRadius: 1,
                    fontSize: '0.8rem',
                    fontFamily: 'monospace',
                  }}
                >
                  {progress.logs.map((log, index) => (
                    <div
                      key={index}
                      style={{
                        color: log.includes('PASSED')
                          ? 'green'
                          : log.includes('FAILED')
                            ? 'red'
                            : 'inherit',
                      }}
                    >
                      {log}
                    </div>
                  ))}
                </Box>
              )}

              {!progress.isRunning && progress.totalTasks > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Tooltip title="Navigate to the Data Files page to view and manage the verified task files">
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<FolderOpen />}
                      onClick={handleViewOutputFiles}
                      disabled={
                        getOutputFiles().length === 0 && !progress.outputFile
                      }
                    >
                      View Output Files
                    </Button>
                  </Tooltip>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Help Card */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <Info sx={{ mr: 1 }} />
                Verification Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Verification checks if tasks can be executed successfully on the
                MCP servers
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Domain name should match your task generation domain
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Tasks files are automatically loaded from the domain directory
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Use -1 to verify all tasks in the selected file
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Server configuration should match generation settings
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Environment variables use format: KEY1=value1, KEY2=value2
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • API keys and secrets should be passed as environment variables
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Example: NPS_API_KEY=your-key-here for National Parks server
              </Typography>
              <Typography variant="body2">
                • Verified tasks are saved to verified_tasks/ directory
              </Typography>
            </CardContent>
          </Card>

          {/* Pipeline Organization Card */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                🔄 Verification Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📝 <strong>tasks/</strong> - Input: Generated tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ✅ <strong>verified_tasks/</strong> - Output: Successfully
                verified tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ⚡ <strong>evaluations/</strong> - Next: Model evaluation
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                Verification ensures tasks work before model evaluation.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TaskVerifier;
