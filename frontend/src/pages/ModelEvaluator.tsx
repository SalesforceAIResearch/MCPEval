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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  FormHelperText,
} from '@mui/material';
import {
  Assessment as EvaluateIcon,
  PlayArrow,
  Stop,
  Upload,
  Download,
  Info,
  Add as AddIcon,
  Delete as DeleteIcon,
  FolderOpen,
  Launch,
  Refresh,
} from '@mui/icons-material';
import { ServerConfig } from '../components/types';
import MCPServerConfiguration from '../components/MCPServerConfiguration';

interface ModelConfig {
  name: string;
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  apiKey: string;
  baseUrl: string;
}

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
}

interface EvaluationProgress {
  isRunning: boolean;
  currentTask: number;
  totalTasks: number;
  currentModel: string;
  successfulTasks: number;
  failedTasks: number;
  status: string;
  logs: string[];
  jobId?: string;
  currentTaskName?: string;
  estimatedTimeRemaining?: string;
  inputFile?: string;
  outputPath?: string;
}

const ModelEvaluator: React.FC = () => {
  const navigate = useNavigate();
  const [servers, setServers] = useState<ServerConfig[]>([
    { path: '', args: [], env: {} },
  ]);
  const [domainName, setDomainName] = useState('');
  const [tasksFileName, setTasksFileName] = useState('');
  const [outputFileName, setOutputFileName] = useState('');
  const [maxTurns, setMaxTurns] = useState(30);
  const [promptFile, setPromptFile] = useState('');
  const [numTasks, setNumTasks] = useState(-1);

  // File listing states
  const [verifiedTasksFiles, setVerifiedTasksFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const [models, setModels] = useState<ModelConfig[]>([
    {
      name: 'GPT-4o',
      model: 'gpt-4o',
      temperature: 0.0,
      maxTokens: 4000,
      topP: 0.95,
      apiKey: '',
      baseUrl: '',
    },
  ]);

  const [progress, setProgress] = useState<EvaluationProgress>({
    isRunning: false,
    currentTask: 0,
    totalTasks: 0,
    currentModel: '',
    successfulTasks: 0,
    failedTasks: 0,
    status: '',
    logs: [],
    jobId: undefined,
    currentTaskName: undefined,
    estimatedTimeRemaining: undefined,
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

  // Load files when domain changes
  useEffect(() => {
    if (domainName.trim()) {
      fetchFiles(domainName);
    } else {
      setVerifiedTasksFiles([]);
      setTasksFileName('');
    }
  }, [domainName]);

  const fetchFiles = async (domain: string) => {
    if (!domain.trim()) {
      setVerifiedTasksFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Use correct relative path from workspace root
      const verifiedTasksPath = `data/${domain}/verified_tasks`;

      const response = await fetch(`/api/files?directory=${verifiedTasksPath}`);

      if (response.ok) {
        const data = await response.json();
        setVerifiedTasksFiles(data.files || []);
      } else {
        console.error('Failed to fetch verified tasks files');
        setVerifiedTasksFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setVerifiedTasksFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const addModel = () => {
    setModels([
      ...models,
      {
        name: `Model ${models.length + 1}`,
        model: 'gpt-4o',
        temperature: 0.0,
        maxTokens: 4000,
        topP: 0.95,
        apiKey: '',
        baseUrl: '',
      },
    ]);
  };

  const removeModel = (index: number) => {
    setModels(models.filter((_, i) => i !== index));
  };

  const updateModel = (
    index: number,
    field: keyof ModelConfig,
    value: string | number
  ) => {
    const newModels = [...models];
    newModels[index] = { ...newModels[index], [field]: value };
    setModels(newModels);
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

    // Also check for common output patterns in logs with evaluation-specific patterns
    logs.forEach(log => {
      // Look for file paths in logs - more comprehensive patterns for evaluation
      const filePathMatches = log.match(
        /(?:saved to|output|generated|evaluated|results saved|evaluation complete|written to).*?data\/[^"\s]+/gi
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

    // Debug logging in development
    if (process.env.NODE_ENV === 'development') {
      console.log('ModelEvaluator getOutputFiles:', {
        outputFiles,
        outputPath: progress.outputPath,
        logsCount: logs.length,
        hasMetadataLog: !!metadataLog,
      });
    }

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
    } else if (domainName) {
      // Final fallback: Navigate to the evaluations directory for this domain
      const evaluationsPath = `data/${domainName}/evaluations`;
      navigate(`/data-files?path=${encodeURIComponent(evaluationsPath)}`);
    }
  };

  const handleEvaluate = async () => {
    if (!domainName.trim() || !tasksFileName) {
      return;
    }

    // Find the selected file to get its full path
    const selectedTasksFile = verifiedTasksFiles.find(
      f => f.name === tasksFileName
    );

    if (!selectedTasksFile) {
      setProgress({
        isRunning: false,
        currentTask: 0,
        totalTasks: 0,
        currentModel: '',
        successfulTasks: 0,
        failedTasks: 0,
        status: 'Error: Selected verified tasks file not found',
        logs: ['Error: Selected verified tasks file not found'],
      });
      return;
    }

    const tasksFilePath = selectedTasksFile.path;
    
    // Generate default filename based on model names
    const generateDefaultFilename = () => {
      if (models.length === 1) {
        const modelName = models[0].name.toLowerCase().replace(/[^a-z0-9]/g, '_');
        return `${modelName}_evaluation_results.jsonl`;
      } else {
        return `multi_model_evaluation_results.jsonl`;
      }
    };
    
    const outputFilePath = outputFileName
      ? `data/${domainName}/evaluations/${outputFileName}`
      : `data/${domainName}/evaluations/${generateDefaultFilename()}`;

    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks: 0,
      currentModel: '',
      successfulTasks: 0,
      failedTasks: 0,
      status: 'Starting model evaluation...',
      logs: ['Initializing model evaluation...'],
      jobId: undefined,
      inputFile: tasksFilePath,
      outputPath: outputFilePath,
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
        models: models.map(m => ({
          name: m.name,
          model: m.model,
          temperature: m.temperature,
          max_tokens: m.maxTokens,
          top_p: m.topP,
          api_key: m.apiKey || null,
          base_url: m.baseUrl || null,
        })),
        max_turns: maxTurns,
        prompt_file: promptFile || null,
        num_tasks: numTasks,
      };

      // Call the backend API
      const response = await fetch('/api/evaluate-models', {
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
      const inputFile = data.input_file;
      const outputPath = data.output_path;
      const responseDomainName = data.domain_name;

      setProgress(prev => ({
        ...prev,
        status: 'Model evaluation started successfully',
        logs: [
          ...prev.logs,
          'Model evaluation job started, tracking progress...',
          inputFile ? `Loading tasks from: ${inputFile}` : '',
          outputPath ? `Results will be saved to: ${outputPath}` : '',
        ],
        jobId: jobId,
        inputFile: inputFile,
        outputPath: outputPath,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/job/${jobId}`);
          const statusData = await statusResponse.json();

          if (statusResponse.ok && statusData) {
            const { progress: jobProgress, logs: jobLogs } = statusData;

            // Parse logs to extract evaluation progress - use backend progress + actual CLI patterns
            const parseProgressFromLogs = (logs: string[]) => {
              if (!logs || logs.length === 0)
                return {
                  currentTask: 0,
                  totalTasks: 0,
                  successfulTasks: 0,
                  failedTasks: 0,
                  currentModel: '',
                  currentTaskName: undefined,
                };

              // Join all logs into a single string for easier parsing
              const allLogs = logs.join('\n');

              // Look for total tasks patterns - use actual CLI output patterns
              const totalTasksMatch = allLogs.match(
                /Loaded (\d+) tasks from/i
              ) || allLogs.match(
                /Starting evaluation of (\d+) tasks/i
              );
              const totalTasks = totalTasksMatch
                ? parseInt(totalTasksMatch[1])
                : numTasks > 0 ? numTasks : 0;

              // Look for current task patterns - use actual CLI output patterns
              const taskProgressMatches = allLogs.match(
                /Starting evaluation for task (\d+)\/(\d+)/g
              );
              let currentTask = 0;
              if (taskProgressMatches && taskProgressMatches.length > 0) {
                const lastMatch =
                  taskProgressMatches[taskProgressMatches.length - 1];
                const match = lastMatch.match(/(\d+)\/(\d+)/);
                if (match) {
                  currentTask = parseInt(match[1]);
                }
              }

              // Look for current model patterns - use actual CLI output patterns
              const currentModelMatch = allLogs.match(
                /Using model: (.+?)(?:\s|$)/i
              ) || allLogs.match(
                /Model: (.+?)(?:\s|$)/i
              );
              const currentModel = currentModelMatch
                ? currentModelMatch[1].trim()
                : '';

              // Count successful and failed tasks - use actual CLI output patterns
              const successMatches = allLogs.match(
                /Successfully completed task \d+\/\d+/gi
              );
              const failMatches = allLogs.match(
                /Error executing task \d+\/\d+/gi
              );

              const successfulTasks = successMatches
                ? successMatches.length
                : 0;
              const failedTasks = failMatches ? failMatches.length : 0;

              // Extract current task name if available
              const currentTaskMatch = allLogs.match(
                /Starting evaluation for task \d+\/\d+.*?:\s*(.+)/
              );
              const currentTaskName = currentTaskMatch
                ? currentTaskMatch[1].trim()
                : undefined;

              return {
                currentTask,
                totalTasks:
                  totalTasks ||
                  (currentTask > 0 ? Math.max(numTasks, currentTask) : 0),
                successfulTasks,
                failedTasks,
                currentModel,
                currentTaskName,
              };
            };

            const {
              currentTask,
              totalTasks,
              successfulTasks,
              failedTasks,
              currentModel,
              currentTaskName,
            } = parseProgressFromLogs(jobLogs);

            // Use backend progress if available, otherwise fall back to log parsing
            const backendProgress = jobProgress.progress || 0;
            const progressPercentage = backendProgress > 0 ? backendProgress : 
              (totalTasks > 0 && currentTask > 0) ? Math.round((currentTask / totalTasks) * 100) : 0;

            setProgress(prev => ({
              ...prev,
              status:
                jobProgress.status === 'running'
                  ? currentTask > 0
                    ? `Evaluating task ${currentTask}/${totalTasks}${currentModel ? ` with ${currentModel}` : ''}... (${progressPercentage}%)`
                    : 'Initializing evaluation...'
                  : jobProgress.status === 'completed'
                    ? 'Evaluation completed successfully!'
                    : jobProgress.status === 'failed'
                      ? 'Evaluation failed'
                      : jobProgress.status === 'cancelled'
                        ? 'Evaluation cancelled'
                        : prev.status,
              logs: jobLogs || prev.logs,
              currentTask:
                jobProgress.status === 'completed' ? totalTasks : currentTask,
              totalTasks: totalTasks || prev.totalTasks,
              successfulTasks: successfulTasks,
              failedTasks: failedTasks,
              currentModel: currentModel,
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
                    ? totalTasks || prev.currentTask
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

      // Set a timeout to stop polling after 60 minutes (evaluations can take longer)
      timeoutRef.current = setTimeout(
        () => {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Evaluation timed out',
            logs: [...prev.logs, 'Evaluation timed out after 60 minutes'],
          }));
        },
        60 * 60 * 1000
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
            status: 'Evaluation cancelled by user',
            logs: [...prev.logs, 'Evaluation cancelled by user'],
          }));
        } else {
          const errorData = await response.json().catch(() => ({}));
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Evaluation stopped (cancel failed)',
            logs: [
              ...prev.logs,
              `Cancel failed: ${errorData.error || 'Unknown error'}`,
              'Evaluation stopped locally',
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
          status: 'Evaluation stopped (cancel failed)',
          logs: [
            ...prev.logs,
            `Cancel failed: ${errorMessage}`,
            'Evaluation stopped locally',
          ],
        }));
      }
    } else {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'Evaluation stopped by user',
        logs: [...prev.logs, 'Evaluation stopped by user'],
      }));
    }
  };

  const isConfigValid = () => {
    return (
      servers.some(s => s.path.trim()) &&
      domainName.trim() &&
      tasksFileName.trim() &&
      verifiedTasksFiles.some(f => f.name === tasksFileName) &&
      models.length > 0
    );
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Model Evaluation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Evaluate AI models using verified tasks and MCP servers with
          comprehensive performance analysis
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Evaluation Configuration
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
                    <InputLabel>Verified Tasks File</InputLabel>
                    <Select
                      value={tasksFileName}
                      onChange={e => setTasksFileName(e.target.value)}
                      label="Verified Tasks File"
                      disabled={
                        !domainName.trim() ||
                        verifiedTasksFiles.length === 0 ||
                        loadingFiles
                      }
                    >
                      {verifiedTasksFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/verified_tasks/${tasksFileName || 'select_file.jsonl'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Number of Tasks to Evaluate"
                    value={numTasks}
                    onChange={e => setNumTasks(parseInt(e.target.value) || -1)}
                    helperText="Use -1 to evaluate all tasks"
                    inputProps={{ min: -1, max: 1000 }}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Server Configuration */}
              <MCPServerConfiguration
                servers={servers}
                onServersChange={setServers}
                title="MCP Servers"
                subtitle="Configure or import servers for model evaluation"
                required
              />

              <Divider sx={{ my: 3 }} />

              {/* Evaluation Settings */}
              <Typography variant="subtitle1" gutterBottom>
                Evaluation Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Output File Name (Optional)"
                    value={outputFileName}
                    onChange={e => setOutputFileName(e.target.value)}
                    placeholder={
                      models.length === 1 
                        ? `${models[0].name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_evaluation_results.jsonl`
                        : 'multi_model_evaluation_results.jsonl'
                    }
                                          helperText={
                        domainName
                          ? `→ workspace/data/${domainName}/evaluations/${
                              outputFileName || 
                              (models.length === 1 
                                ? `${models[0].name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_evaluation_results.jsonl`
                                : 'multi_model_evaluation_results.jsonl')
                            }`
                          : 'Auto-generated based on model name(s)'
                      }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Turns"
                    value={maxTurns}
                    onChange={e => setMaxTurns(parseInt(e.target.value) || 30)}
                    helperText="Maximum conversation turns per task"
                    inputProps={{ min: 1, max: 100 }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Prompt File (Optional)"
                    value={promptFile}
                    onChange={e => setPromptFile(e.target.value)}
                    placeholder="custom_prompts.json"
                    helperText="Custom system message file"
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Model Configuration */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                  Model Configurations
                </Typography>
                <Tooltip title="Add another model">
                  <IconButton onClick={addModel} color="primary">
                    <AddIcon />
                  </IconButton>
                </Tooltip>
              </Box>

              {models.map((model, index) => (
                <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                        Model {index + 1}
                      </Typography>
                      {models.length > 1 && (
                        <IconButton
                          onClick={() => removeModel(index)}
                          color="error"
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={12} md={4}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Model Name"
                          value={model.name}
                          onChange={e =>
                            updateModel(index, 'name', e.target.value)
                          }
                          placeholder="GPT-4o"
                        />
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Model"
                          value={model.model}
                          onChange={e =>
                            updateModel(index, 'model', e.target.value)
                          }
                          placeholder="gpt-4o"
                        />
                      </Grid>
                      <Grid item xs={12} md={2}>
                        <TextField
                          fullWidth
                          size="small"
                          type="number"
                          label="Temperature"
                          value={model.temperature}
                          onChange={e =>
                            updateModel(
                              index,
                              'temperature',
                              parseFloat(e.target.value) || 0.0
                            )
                          }
                          inputProps={{ min: 0, max: 2, step: 0.01 }}
                        />
                      </Grid>
                      <Grid item xs={12} md={2}>
                        <TextField
                          fullWidth
                          size="small"
                          type="number"
                          label="Top P"
                          value={model.topP}
                          onChange={e =>
                            updateModel(
                              index,
                              'topP',
                              parseFloat(e.target.value) || 0.95
                            )
                          }
                          inputProps={{ min: 0, max: 1, step: 0.05 }}
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          size="small"
                          type="number"
                          label="Max Tokens"
                          value={model.maxTokens}
                          onChange={e =>
                            updateModel(
                              index,
                              'maxTokens',
                              parseInt(e.target.value) || 4000
                            )
                          }
                          inputProps={{ min: 100, max: 8000 }}
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Base URL (Optional)"
                          value={model.baseUrl}
                          onChange={e =>
                            updateModel(index, 'baseUrl', e.target.value)
                          }
                          placeholder="https://api.openai.com/v1"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          size="small"
                          type="password"
                          label="API Key (Optional)"
                          value={model.apiKey}
                          onChange={e =>
                            updateModel(index, 'apiKey', e.target.value)
                          }
                          helperText="Uses environment variable if not provided"
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              ))}

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
                    console.log('Upload verified tasks file');
                  }}
                >
                  Upload Tasks
                </Button>
                <Button
                  variant="contained"
                  onClick={progress.isRunning ? handleStop : handleEvaluate}
                  disabled={!progress.isRunning && !isConfigValid()}
                  startIcon={progress.isRunning ? <Stop /> : <EvaluateIcon />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Evaluation' : 'Start Evaluation'}
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
                Evaluation Progress
              </Typography>

              {progress.currentModel && (
                <Box sx={{ mb: 2 }}>
                  <Chip
                    label={`Current: ${progress.currentModel}`}
                    color="primary"
                    sx={{ mb: 1 }}
                  />
                </Box>
              )}

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
                        : (progress.currentTask / progress.totalTasks) * 100
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.totalTasks === 0
                      ? 'Initializing evaluation...'
                      : `${progress.currentTask} / ${progress.totalTasks} tasks evaluated (${Math.round((progress.currentTask / progress.totalTasks) * 100)}%)`}
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

              {!progress.isRunning &&
                progress.currentTask > 0 &&
                progress.totalTasks > 0 && (
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
                      evaluated (100%)
                    </Typography>
                  </Box>
                )}

              {(progress.successfulTasks > 0 || progress.failedTasks > 0) && (
                <Box sx={{ mb: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main">
                          {progress.successfulTasks}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Successful
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
                <strong>Status:</strong>{' '}
                {progress.status || 'Ready to evaluate'}
              </Typography>

              {/* Show View Files button prominently when evaluation is complete */}
              {!progress.isRunning && domainName && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Tooltip title="Click to open the evaluation result files in the Data Files page">
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<Launch />}
                      onClick={handleViewOutputFiles}
                      color="success"
                      size="small"
                    >
                      📁 Open Evaluation Files
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
              {(progress.inputFile || (domainName && tasksFileName)) && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Input:</strong>{' '}
                  {progress.inputFile ||
                    `workspace/data/${domainName}/verified_tasks/${tasksFileName}`}
                </Typography>
              )}

              {(progress.outputPath || domainName) && (
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
                    
                    // Generate default filename for display
                    const defaultFilename = outputFileName || 
                      (models.length === 1 
                        ? `${models[0].name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_evaluation_results.jsonl`
                        : 'multi_model_evaluation_results.jsonl');
                    
                    return (
                      progress.outputPath ||
                      `workspace/data/${domainName}/evaluations/${defaultFilename}`
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
                        color:
                          log.includes('SUCCESS') || log.includes('COMPLETED')
                            ? 'green'
                            : log.includes('FAILED') || log.includes('ERROR')
                              ? 'red'
                              : 'inherit',
                      }}
                    >
                      {log}
                    </div>
                  ))}
                </Box>
              )}

              {!progress.isRunning && progress.currentTask > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Tooltip title="Navigate to the Data Files page to view and manage the evaluation result files">
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<FolderOpen />}
                      onClick={handleViewOutputFiles}
                      disabled={
                        getOutputFiles().length === 0 && !progress.outputPath
                      }
                      sx={{ mb: 1 }}
                    >
                      View Output Files
                    </Button>
                  </Tooltip>
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => {
                      // TODO: Navigate to results page
                      console.log('View detailed results');
                    }}
                  >
                    View Detailed Results
                  </Button>
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
                Evaluation Guide
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Evaluates AI models on verified tasks using MCP servers
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Domain name should match your verification domain
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Verified tasks files are automatically loaded from the domain
                directory
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Configure multiple models for comparison
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Adjust max turns based on task complexity
              </Typography>
              <Typography variant="body2">
                • Results include conversation logs and performance metrics
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
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ✅ <strong>verified_tasks/</strong> - Input: Verified tasks
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ⚡ <strong>evaluations/</strong> - Output: Model evaluation
                results
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                🧠 <strong>judging/</strong> - Next: LLM judge scoring
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📊 <strong>reports/</strong> - Finally: Analysis reports
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                Evaluation tests how well models perform on verified tasks.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ModelEvaluator;
