import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Box,
  Alert,
  Divider,
  LinearProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Gavel as JudgeIcon,
  Upload,
  Download,
  Info,
  Refresh,
  Stop,
  Psychology,
} from '@mui/icons-material';

interface JudgeProgress {
  isRunning: boolean;
  status: string;
  logs: string[];
  jobId?: string;
  outputPath?: string;
  domain?: string;
}

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
}

const LLMJudger: React.FC = () => {
  const [domainName, setDomainName] = useState('');
  const [evaluationFile, setEvaluationFile] = useState('');
  const [model, setModel] = useState('gpt-4o');
  const [resume, setResume] = useState(false);

  // File listing states
  const [evaluationFiles, setEvaluationFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Progress tracking
  const [progress, setProgress] = useState<JudgeProgress>({
    isRunning: false,
    status: '',
    logs: [],
    jobId: undefined,
    outputPath: undefined,
    domain: undefined,
  });

  // Refs for polling
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup effect
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
      setEvaluationFiles([]);
      setEvaluationFile('');
    }
  }, [domainName]);

  const fetchFiles = async (domain: string) => {
    if (!domain.trim()) {
      setEvaluationFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Look for evaluation files that can be judged
      const evaluationPath = `data/${domain}/evaluations`;

      const response = await fetch(`/api/files?directory=${evaluationPath}`);

      if (response.ok) {
        const data = await response.json();
        // Filter for JSON and JSONL files that might contain evaluation results
        const jsonFiles = (data.files || []).filter(
          (file: FileInfo) =>
            (file.name.endsWith('.json') || file.name.endsWith('.jsonl')) &&
            !file.name.includes('_trajectory') &&
            !file.name.includes('_completion')
        );
        setEvaluationFiles(jsonFiles);
      } else {
        console.error('Failed to fetch evaluation files');
        setEvaluationFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setEvaluationFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleJudge = async () => {
    if (!domainName.trim() || !evaluationFile) {
      return;
    }

    // Find the selected file to get its full path
    const selectedFile = evaluationFiles.find(f => f.name === evaluationFile);

    if (!selectedFile) {
      setProgress({
        isRunning: false,
        status: 'Error: Selected file not found',
        logs: ['Error: Selected file not found'],
      });
      return;
    }

    // Use the relative path from the file listing API
    const inputFilePath = selectedFile.path;
    const outputDir = `data/${domainName}/judging`;

    setProgress({
      isRunning: true,
      status: 'Starting LLM judging...',
      logs: ['Initializing LLM judge...'],
      jobId: undefined,
      outputPath: undefined,
      domain: domainName,
    });

    try {
      // First, run the judge command
      const judgePayload = {
        input_file: inputFilePath,
        output_dir: outputDir,
        model: model,
        resume: resume,
      };

      const judgeResponse = await fetch('/api/llm-judge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(judgePayload),
      });

      if (!judgeResponse.ok) {
        const errorData = await judgeResponse.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            `Server error: ${judgeResponse.status} ${judgeResponse.statusText}`
        );
      }

      const judgeData = await judgeResponse.json();
      const { job_id } = judgeData;

      setProgress(prev => ({
        ...prev,
        status: 'LLM judge started successfully',
        logs: [...prev.logs, 'LLM judge job started, tracking progress...'],
        jobId: job_id,
        outputPath: outputDir,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/job/${job_id}`);
          
          if (!statusResponse.ok) {
            console.error('Failed to fetch job status:', statusResponse.status);
            return;
          }
          
          const statusData = await statusResponse.json();
          
          // Validate response structure
          if (!statusData || !statusData.progress) {
            console.error('Invalid status response structure:', statusData);
            return;
          }

          const { progress: jobProgress, logs: jobLogs } = statusData;
          
          // Validate progress object
          if (!jobProgress || typeof jobProgress.status !== 'string') {
            console.error('Invalid progress object:', jobProgress);
            return;
          }

          setProgress(prev => ({
            ...prev,
                          status:
                jobProgress.status === 'running'
                  ? 'Running LLM judge...'
                  : jobProgress.status === 'completed'
                    ? 'LLM judging completed successfully!'
                    : jobProgress.status === 'failed'
                      ? 'Judge failed'
                      : jobProgress.status === 'cancelled'
                        ? 'Judge cancelled'
                        : `Unknown status: ${jobProgress.status}`,
            logs: Array.isArray(jobLogs) ? jobLogs : prev.logs,
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
                status:
                  jobProgress.status === 'completed'
                    ? 'LLM judging completed successfully!'
                    : prev.status,
              }));
            }
        } catch (pollError) {
          console.error('Error polling job status:', pollError);
          // Continue polling despite errors, but log them
        }
      }, 2000);

      // Set timeout
      timeoutRef.current = setTimeout(
        () => {
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
            status: 'LLM judging timed out',
            logs: [...prev.logs, 'LLM judging timed out after 30 minutes'],
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
        const response = await fetch(`/api/jobs/${progress.jobId}/kill`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'LLM judging cancelled by user',
            logs: [...prev.logs, 'LLM judging cancelled by user'],
          }));
        } else {
          const errorData = await response.json().catch(() => ({}));
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'LLM judging stopped (cancel failed)',
            logs: [
              ...prev.logs,
              `Cancel failed: ${errorData.error || 'Unknown error'}`,
              'LLM judging stopped locally',
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
          status: 'LLM judging stopped (cancel failed)',
          logs: [
            ...prev.logs,
            `Cancel failed: ${errorMessage}`,
            'LLM judging stopped locally',
          ],
        }));
      }
    } else {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'LLM judging stopped by user',
        logs: [...prev.logs, 'LLM judging stopped by user'],
      }));
    }
  };

  const isConfigValid = () => {
    return domainName.trim() && evaluationFile;
  };

  const downloadResults = () => {
    if (progress.outputPath) {
      // Create download link for the results
      const link = document.createElement('a');
      link.href = `/api/download/${progress.outputPath}`;
      link.download = `llm_judge_results_${domainName}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🧠 LLM Judge
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Score task execution results using LLM judges for automated quality assessment
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                LLM Judge Configuration
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                AI-powered scoring of task execution quality and correctness
              </Alert>

              {/* Domain Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Domain Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Domain Name"
                    value={domainName}
                    onChange={e => setDomainName(e.target.value)}
                    placeholder="healthcare"
                    helperText="The domain name (e.g., healthcare, sports, yfinance)"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="Refresh file lists">
                      <IconButton
                        onClick={() => fetchFiles(domainName)}
                        disabled={!domainName.trim() || loadingFiles}
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                    <Typography variant="body2" color="text.secondary">
                      {loadingFiles
                        ? 'Loading files...'
                        : 'Click to refresh file lists'}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* File Selection */}
              <Typography variant="subtitle1" gutterBottom>
                File Selection
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12}>
                  <FormControl fullWidth required>
                    <InputLabel>Evaluation Results File</InputLabel>
                    <Select
                      value={evaluationFile}
                      onChange={e => setEvaluationFile(e.target.value)}
                      label="Evaluation Results File"
                      disabled={
                        !domainName.trim() || evaluationFiles.length === 0
                      }
                    >
                      {evaluationFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/evaluations/${evaluationFile || 'select_file.json'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Judge Settings */}
              <Typography variant="subtitle1" gutterBottom>
                Judge Configuration
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Judge Model"
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    placeholder="gpt-4o"
                    helperText="AI model for judging evaluations"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box
                    sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
                  >
                    <FormControlLabel
                      control={
                        <Switch
                          checked={resume}
                          onChange={e => setResume(e.target.checked)}
                        />
                      }
                      label="Resume from Previous Run"
                    />
                    <FormHelperText>
                      Continue from where previous judging left off
                    </FormHelperText>
                  </Box>
                </Grid>
              </Grid>

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<Upload />}
                  onClick={() => {
                    // TODO: Implement file upload
                    console.log('Upload files');
                  }}
                >
                  Upload Files
                </Button>
                <Button
                  variant="contained"
                  onClick={progress.isRunning ? handleStop : handleJudge}
                  disabled={!progress.isRunning && !isConfigValid()}
                  startIcon={progress.isRunning ? <Stop /> : <JudgeIcon />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Judging' : 'Start LLM Judge'}
                </Button>
              </Box>

              {progress.isRunning && (
                <Box sx={{ mt: 3 }}>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    {progress.status}
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Progress Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Judge Progress
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Status:</strong> {progress.status || 'Ready to judge'}
              </Typography>

              {/* Show file paths */}
              {domainName && evaluationFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Input:</strong> {domainName}/evaluations/
                  {evaluationFile}
                </Typography>
              )}

              {progress.outputPath && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Output:</strong> {progress.outputPath}
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
                    mb: 2,
                  }}
                >
                  {progress.logs.map((log, index) => (
                    <div key={index}>{log}</div>
                  ))}
                </Box>
              )}

              {!progress.isRunning && progress.outputPath && (
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={downloadResults}
                  sx={{ mb: 2 }}
                >
                  Download Results
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Help Section */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <Info sx={{ mr: 1 }} />
                LLM Judge Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                LLM Judge scores task execution quality using AI models
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Domain should match your evaluation domain
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Evaluation file contains task execution results
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Judge scores trajectory and completion quality
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Results are saved to judging/ directory
              </Typography>
              <Typography variant="body2">
                • Use Judge Rubric page for detailed analysis
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
                <Psychology sx={{ mr: 1 }} />
                Judge Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📋 <strong>evaluations/</strong> - Input: Task execution results
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                🧠 <strong>judging/</strong> - Output: AI judge scores
              </Typography>

              <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                Output files:
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _combined.json - Complete results
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _trajectory.json - Trajectory scores
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _completion.json - Completion scores
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                AI judge provides objective quality assessment of task
                execution. Use Judge Rubric page for detailed analysis.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default LLMJudger;
