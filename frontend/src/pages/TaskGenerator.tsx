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
  Chip,
  Alert,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  PlayArrow,
  Stop,
  Download,
  Upload,
  Info,
  FolderOpen,
  Launch,
} from '@mui/icons-material';
import MCPServerConfiguration from '../components/MCPServerConfiguration';
import { ServerConfig } from '../components/types';

interface GenerationProgress {
  isRunning: boolean;
  currentTask: number;
  totalTasks: number;
  status: string;
  logs: string[];
  jobId?: string;
  currentTaskName?: string;
  estimatedTimeRemaining?: string;
  serverName?: string;
  outputPath?: string;
}

const TaskGenerator: React.FC = () => {
  const navigate = useNavigate();
  const [servers, setServers] = useState<ServerConfig[]>([
    { path: '', args: [], env: {} },
  ]);
  const [outputFolderName, setOutputFolderName] = useState('');
  const [outputFileName, setOutputFileName] = useState('');
  const [numTasks, setNumTasks] = useState(10);
  const [existingFiles, setExistingFiles] = useState<string[]>([]);
  const [promptFile, setPromptFile] = useState('');
  const [model, setModel] = useState('gpt-4.1-2025-04-14');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2000);
  const [topP, setTopP] = useState(0.95);
  const [apiKey, setApiKey] = useState('');

  const [progress, setProgress] = useState<GenerationProgress>({
    isRunning: false,
    currentTask: 0,
    totalTasks: 0,
    status: '',
    logs: [],
    jobId: undefined,
    currentTaskName: undefined,
    estimatedTimeRemaining: undefined,
    serverName: undefined,
    outputPath: undefined,
  });

  // Ref to track the active polling interval
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

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



  const addExistingFile = () => {
    setExistingFiles([...existingFiles, '']);
  };

  const removeExistingFile = (index: number) => {
    setExistingFiles(existingFiles.filter((_, i) => i !== index));
  };

  const updateExistingFile = (index: number, value: string) => {
    const newFiles = [...existingFiles];
    newFiles[index] = value;
    setExistingFiles(newFiles);
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

  const handleViewOutputFiles = () => {
    const outputFiles = getOutputFiles();
    if (outputFiles.length > 0) {
      // Navigate to DataFiles with the first output file's directory
      const firstFile = outputFiles[0];
      const dirPath = firstFile.substring(0, firstFile.lastIndexOf('/'));
      navigate(
        `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(firstFile)}`
      );
    } else if (progress.outputPath) {
      // Fallback: If no files found in logs, try to use outputPath
      // Check if outputPath is a file or directory
      const outputPath = progress.outputPath;
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

  const handleGenerate = async () => {
    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks: numTasks,
      status: 'Starting task generation...',
      logs: ['Initializing task generator...'],
      jobId: undefined,
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
        num_tasks: numTasks,
        existing_files: existingFiles.filter(f => f.trim()),
        prompt_file: promptFile || null,
        model,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
        api_key: apiKey || null,
        output_folder_name: outputFolderName.trim() || null,
        output_file_name: outputFileName.trim() || null,
      };

      // Call the backend API
      const response = await fetch('/api/generate-tasks', {
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

      const data = await response.json();

      const jobId = data.job_id;
      const serverName = data.server_name;
      const outputPath = data.output_path;

      setProgress(prev => ({
        ...prev,
        status: 'Task generation started successfully',
        logs: [
          ...prev.logs,
          'Task generation job started, tracking progress...',
          outputPath ? `Files will be saved to: ${outputPath}` : '',
        ],
        jobId: jobId,
        serverName: serverName,
        outputPath: outputPath,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/job/${jobId}`);
          const statusData = await statusResponse.json();

          if (statusResponse.ok && statusData) {
            const { progress: jobProgress, logs: jobLogs } = statusData;

            // Parse logs to extract current task progress - use backend progress + actual CLI patterns
            const parseProgressFromLogs = (logs: string[]) => {
              if (!logs || logs.length === 0)
                return { currentTask: 0, currentTaskName: undefined };

              // Join all logs into a single string for easier parsing
              const allLogs = logs.join('\n');

              // Look for patterns - use actual CLI output patterns
              const taskPattern =
                /(?:Starting generation for task|Generated task) (\d+)\/\d+(?:: (.+?)(?:\n|$))?/g;
              const taskStartMatches: RegExpExecArray[] = [];
              let match;

              while ((match = taskPattern.exec(allLogs)) !== null) {
                taskStartMatches.push(match);
              }

              if (taskStartMatches.length > 0) {
                const lastMatch = taskStartMatches[taskStartMatches.length - 1];
                const taskNumber = parseInt(lastMatch[1]);
                const taskName = lastMatch[2]?.trim();

                return {
                  currentTask: taskNumber,
                  currentTaskName: taskName,
                };
              }

              // Also check for completed status in logs
              if (
                allLogs.includes('Task generation complete') ||
                allLogs.includes('completed successfully')
              ) {
                return { currentTask: numTasks, currentTaskName: undefined };
              }

              return { currentTask: 0, currentTaskName: undefined };
            };

            const { currentTask, currentTaskName } =
              parseProgressFromLogs(jobLogs);

            // Use backend progress if available, otherwise fall back to log parsing
            const backendProgress = jobProgress.progress || 0;
            const progressPercentage = backendProgress > 0 ? backendProgress : 
              (numTasks > 0 && currentTask > 0) ? Math.round((currentTask / numTasks) * 100) : 0;

            setProgress(prev => ({
              ...prev,
              status:
                jobProgress.status === 'running'
                  ? currentTask > 0
                    ? `Generating task ${currentTask}/${numTasks}... (${progressPercentage}%)`
                    : 'Initializing...'
                  : jobProgress.status === 'completed'
                    ? 'Generation completed successfully!'
                    : jobProgress.status === 'failed'
                      ? 'Generation failed'
                      : prev.status,
              logs: jobLogs || prev.logs,
              currentTask:
                jobProgress.status === 'completed' ? numTasks : currentTask,
              currentTaskName: currentTaskName,
            }));

            // Stop polling when job is complete
            if (
              jobProgress.status === 'completed' ||
              jobProgress.status === 'failed'
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
                    ? numTasks
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
          // Continue polling - don't stop on temporary errors
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
            status: 'Generation timed out',
            logs: [...prev.logs, 'Generation timed out after 30 minutes'],
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

  const handleStop = () => {
    // Clear polling interval and timeout
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
      status: 'Generation stopped by user',
      logs: [...prev.logs, 'Generation stopped by user'],
    }));
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🎯 Generate Tasks
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Generate evaluation tasks for MCP servers using AI models
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generation Configuration
              </Typography>

              {/* Main Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Main Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Task Domain Name"
                    value={outputFolderName}
                    onChange={e => setOutputFolderName(e.target.value)}
                    placeholder="healthcare"
                    helperText={
                      outputFolderName
                        ? `→ workspace/data/${outputFolderName}/tasks/`
                        : 'Leave empty for auto-generated name. Files will be organized by evaluation stage.'
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Number of Tasks"
                    value={numTasks}
                    onChange={e => setNumTasks(parseInt(e.target.value) || 10)}
                    inputProps={{ min: 1, max: 1000 }}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Server Configuration */}
              <MCPServerConfiguration
                servers={servers}
                onServersChange={setServers}
                title="MCP Servers"
                subtitle="Configure or import servers for task generation"
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
                    placeholder="healthcare_tasks_v1.jsonl"
                    helperText={
                      outputFolderName
                        ? `→ workspace/data/${outputFolderName}/tasks/${outputFileName || 'auto_generated_name.jsonl'}`
                        : 'Auto-generated with timestamp if empty'
                    }
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Advanced Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Advanced Settings
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Prompt File (Optional)"
                    value={promptFile}
                    onChange={e => setPromptFile(e.target.value)}
                    placeholder="custom_prompt.json"
                    helperText="JSON file with custom system and user messages"
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

              <Divider sx={{ my: 3 }} />

              {/* Model Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Model Configuration
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Model"
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    placeholder="Enter model name (e.g., gpt-4.1-2025-04-14)"
                    helperText="Specify the AI model to use for task generation"
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Temperature"
                    value={temperature}
                    onChange={e =>
                      setTemperature(parseFloat(e.target.value) || 0.2)
                    }
                    inputProps={{ min: 0, max: 2, step: 0.1 }}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Tokens"
                    value={maxTokens}
                    onChange={e =>
                      setMaxTokens(parseInt(e.target.value) || 2000)
                    }
                    inputProps={{ min: 100, max: 8000 }}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Top P"
                    value={topP}
                    onChange={e => setTopP(parseFloat(e.target.value) || 0.95)}
                    inputProps={{ min: 0, max: 1, step: 0.05 }}
                  />
                </Grid>
              </Grid>

              {/* Existing Files */}
              {existingFiles.length > 0 && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Existing Task Files
                    </Typography>
                    {existingFiles.map((file, index) => (
                      <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                        <TextField
                          fullWidth
                          size="small"
                          value={file}
                          onChange={e =>
                            updateExistingFile(index, e.target.value)
                          }
                          placeholder="path/to/existing/tasks.jsonl"
                        />
                        <IconButton
                          onClick={() => removeExistingFile(index)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    ))}
                  </Box>
                </>
              )}

              <Button
                variant="outlined"
                onClick={addExistingFile}
                startIcon={<AddIcon />}
                sx={{ mb: 3 }}
              >
                Add Existing Task File
              </Button>

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  onClick={progress.isRunning ? handleStop : handleGenerate}
                  disabled={!progress.isRunning && !servers[0].path}
                  startIcon={progress.isRunning ? <Stop /> : <PlayArrow />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Generation' : 'Generate Tasks'}
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
                Generation Progress
              </Typography>

              {progress.isRunning && (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant={
                      progress.currentTask === 0
                        ? 'indeterminate'
                        : 'determinate'
                    }
                    value={
                      progress.currentTask === 0
                        ? 0
                        : (progress.currentTask / progress.totalTasks) * 100
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.currentTask === 0
                      ? `Generating ${progress.totalTasks} tasks...`
                      : `${progress.currentTask} / ${progress.totalTasks} tasks completed (${Math.round((progress.currentTask / progress.totalTasks) * 100)}%)`}
                  </Typography>

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

              {!progress.isRunning && progress.currentTask > 0 && (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.currentTask} / {progress.totalTasks} tasks
                    completed (100%)
                  </Typography>
                </Box>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Status:</strong>{' '}
                {progress.status || 'Ready to generate'}
              </Typography>

              {/* Show View Files button prominently when generation is complete */}
              {!progress.isRunning &&
                progress.currentTask > 0 &&
                (getOutputFiles().length > 0 || progress.outputPath) && (
                  <Box sx={{ mt: 2, mb: 2 }}>
                    <Tooltip title="Click to open the generated task files in the Data Files page">
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<Launch />}
                        onClick={handleViewOutputFiles}
                        color="success"
                        size="small"
                      >
                        📁 Open Generated Files
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
                    ? `${progress.currentTask}/${progress.totalTasks} tasks`
                    : 'Initializing...'}
                </Typography>
              )}

              {/* Show predicted or actual save path */}
              {(progress.outputPath ||
                outputFolderName ||
                servers.some(s => s.path.trim())) && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  <strong>Save Path:</strong>{' '}
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
                    return progress.outputPath
                      ? progress.outputPath
                      : `workspace/data/${outputFolderName || 'generated_tasks'}/tasks/`;
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
                    <div key={index}>{log}</div>
                  ))}
                </Box>
              )}

              {!progress.isRunning && progress.currentTask > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Tooltip title="Navigate to the Data Files page to view and manage the generated task files">
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<FolderOpen />}
                      onClick={handleViewOutputFiles}
                      disabled={
                        getOutputFiles().length === 0 && !progress.outputPath
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
                Quick Tips
              </Typography>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Specify a task domain name to organize your tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Files are automatically timestamped for uniqueness
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Use multiple servers to generate diverse tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Lower temperature (0.1-0.3) for more focused tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Custom prompt files should contain system and user messages
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
                • Use multiple env vars: API_KEY=secret,DEBUG=true,TIMEOUT=30
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
                🔄 Evaluation Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                Generated files will be organized into stages:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📝 <strong>tasks/</strong> - Generated tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ✅ <strong>verified_tasks/</strong> - Verified and approved
                tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ⚡ <strong>evaluations/</strong> - Model evaluation results
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                🧠 <strong>judging/</strong> - LLM judge scoring
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📊 <strong>reports/</strong> - Analysis reports
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                🔍 <strong>analysis/</strong> - Comparative analysis
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                This organization makes it easy to navigate through the complete
                evaluation workflow.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TaskGenerator;
