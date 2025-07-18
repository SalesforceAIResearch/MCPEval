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
  Chip,
  LinearProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Assessment as RubricIcon,
  Upload,
  Download,
  Info,
  Refresh,
  Stop,
  Psychology,
} from '@mui/icons-material';

interface RubricProgress {
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

const JudgeRubric: React.FC = () => {
  const [domainName, setDomainName] = useState('');
  const [trajectoryFile, setTrajectoryFile] = useState('');
  const [completionFile, setCompletionFile] = useState('');

  // File listing states
  const [trajectoryFiles, setTrajectoryFiles] = useState<FileInfo[]>([]);
  const [completionFiles, setCompletionFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Progress tracking
  const [progress, setProgress] = useState<RubricProgress>({
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
      setTrajectoryFiles([]);
      setCompletionFiles([]);
      setTrajectoryFile('');
      setCompletionFile('');
    }
  }, [domainName]);

  const fetchFiles = async (domain: string) => {
    if (!domain.trim()) {
      setTrajectoryFiles([]);
      setCompletionFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Look for trajectory and completion files in the judging directory
      const judgingPath = `data/${domain}/judging`;

      const response = await fetch(`/api/files?directory=${judgingPath}`);

      if (response.ok) {
        const data = await response.json();
        const jsonFiles = (data.files || []).filter(
          (file: FileInfo) => file.name.endsWith('.json') || file.name.endsWith('.jsonl')
        );
        
        // Filter for trajectory and completion files
        const trajectoryFiles = jsonFiles.filter((file: FileInfo) =>
          file.name.includes('_trajectory')
        );
        const completionFiles = jsonFiles.filter((file: FileInfo) =>
          file.name.includes('_completion')
        );

        setTrajectoryFiles(trajectoryFiles);
        setCompletionFiles(completionFiles);
      } else {
        console.error('Failed to fetch judging files');
        setTrajectoryFiles([]);
        setCompletionFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setTrajectoryFiles([]);
      setCompletionFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleRubricAnalysis = async () => {
    if (!domainName.trim() || !trajectoryFile || !completionFile) {
      return;
    }

    // Find the selected files to get their full paths
    const selectedTrajectoryFile = trajectoryFiles.find(f => f.name === trajectoryFile);
    const selectedCompletionFile = completionFiles.find(f => f.name === completionFile);

    if (!selectedTrajectoryFile || !selectedCompletionFile) {
      setProgress({
        isRunning: false,
        status: 'Error: Selected files not found',
        logs: ['Error: Selected files not found'],
      });
      return;
    }

    const analysisDir = `data/${domainName}/analysis`;

    setProgress({
      isRunning: true,
      status: 'Starting rubric analysis...',
      logs: ['Initializing rubric analysis...'],
      jobId: undefined,
      outputPath: analysisDir,
      domain: domainName,
    });

    try {
      const rubricPayload = {
        trajectory_file: selectedTrajectoryFile.path,
        completion_file: selectedCompletionFile.path,
        output_dir: analysisDir,
      };

      const rubricResponse = await fetch('/api/llm-judge-rubric', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rubricPayload),
      });

      if (!rubricResponse.ok) {
        const errorData = await rubricResponse.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            `Rubric analysis failed: ${rubricResponse.status} ${rubricResponse.statusText}`
        );
      }

      const rubricData = await rubricResponse.json();
      const { job_id } = rubricData;

      setProgress(prev => ({
        ...prev,
        status: 'Rubric analysis started successfully',
        logs: [
          ...prev.logs,
          'Rubric analysis job started, tracking progress...',
          `Results will be saved to: ${analysisDir}`,
        ],
        jobId: job_id,
      }));

      // Poll rubric job status
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/job/${job_id}`);
          
          if (!statusResponse.ok) {
            console.error('Failed to fetch rubric job status:', statusResponse.status);
            return;
          }
          
          const statusData = await statusResponse.json();
          
          // Validate response structure
          if (!statusData || !statusData.progress) {
            console.error('Invalid rubric status response structure:', statusData);
            return;
          }

          const { progress: jobProgress, logs: jobLogs } = statusData;
          
          // Validate progress object
          if (!jobProgress || typeof jobProgress.status !== 'string') {
            console.error('Invalid rubric progress object:', jobProgress);
            return;
          }

          setProgress(prev => ({
            ...prev,
            status:
              jobProgress.status === 'running'
                ? 'Running rubric analysis...'
                : jobProgress.status === 'completed'
                  ? 'Rubric analysis completed successfully!'
                  : jobProgress.status === 'failed'
                    ? 'Rubric analysis failed'
                    : jobProgress.status === 'cancelled'
                      ? 'Rubric analysis cancelled'
                      : `Unknown rubric status: ${jobProgress.status}`,
            logs: Array.isArray(jobLogs) ? jobLogs : prev.logs,
          }));

          // Stop polling when rubric job is complete
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
            }));
          }
        } catch (pollError) {
          console.error('Error polling rubric job status:', pollError);
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
            status: 'Rubric analysis timed out',
            logs: [...prev.logs, 'Rubric analysis timed out after 30 minutes'],
          }));
        },
        30 * 60 * 1000
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      
      // Clear any ongoing polling
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
        status: `Rubric analysis error: ${errorMessage}`,
        logs: [...prev.logs, `Rubric analysis error: ${errorMessage}`],
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
            status: 'Rubric analysis cancelled by user',
            logs: [...prev.logs, 'Rubric analysis cancelled by user'],
          }));
        } else {
          const errorData = await response.json().catch(() => ({}));
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Rubric analysis stopped (cancel failed)',
            logs: [
              ...prev.logs,
              `Cancel failed: ${errorData.error || 'Unknown error'}`,
              'Rubric analysis stopped locally',
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
          status: 'Rubric analysis stopped (cancel failed)',
          logs: [
            ...prev.logs,
            `Cancel failed: ${errorMessage}`,
            'Rubric analysis stopped locally',
          ],
        }));
      }
    } else {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'Rubric analysis stopped by user',
        logs: [...prev.logs, 'Rubric analysis stopped by user'],
      }));
    }
  };

  const isConfigValid = () => {
    return domainName.trim() && trajectoryFile && completionFile;
  };

  const downloadResults = () => {
    if (progress.outputPath) {
      // Create download link for the results
      const link = document.createElement('a');
      link.href = `/api/download/${progress.outputPath}`;
      link.download = `rubric_analysis_results_${domainName}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Judge Rubric Analysis
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Generate detailed rubric-based analysis from LLM judge results
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Rubric Analysis Configuration
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                Analyze trajectory and completion files to generate detailed rubric-based insights
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
                Input Files Selection
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Trajectory File</InputLabel>
                    <Select
                      value={trajectoryFile}
                      onChange={e => setTrajectoryFile(e.target.value)}
                      label="Trajectory File"
                      disabled={
                        !domainName.trim() || trajectoryFiles.length === 0
                      }
                    >
                      {trajectoryFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/judging/${trajectoryFile || 'select_trajectory_file.json'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Completion File</InputLabel>
                    <Select
                      value={completionFile}
                      onChange={e => setCompletionFile(e.target.value)}
                      label="Completion File"
                      disabled={
                        !domainName.trim() || completionFiles.length === 0
                      }
                    >
                      {completionFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/judging/${completionFile || 'select_completion_file.json'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
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
                  onClick={progress.isRunning ? handleStop : handleRubricAnalysis}
                  disabled={!progress.isRunning && !isConfigValid()}
                  startIcon={progress.isRunning ? <Stop /> : <RubricIcon />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Analysis' : 'Start Rubric Analysis'}
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
                Analysis Progress
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Status:</strong> {progress.status || 'Ready for analysis'}
              </Typography>

              {/* Show file paths */}
              {domainName && trajectoryFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Trajectory:</strong> {domainName}/judging/{trajectoryFile}
                </Typography>
              )}

              {domainName && completionFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Completion:</strong> {domainName}/judging/{completionFile}
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
                Rubric Analysis Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Rubric analysis generates detailed insights from LLM judge results
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Requires trajectory and completion files from LLM judge
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Analyzes quality patterns and scoring rationales
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Generates detailed rubric-based breakdowns
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Results saved to analysis/ directory
              </Typography>
              <Typography variant="body2">
                • Provides human-readable analysis reports
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
                Rubric Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                🧠 <strong>judging/</strong> - Input: Judge results (trajectory, completion)
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📊 <strong>analysis/</strong> - Output: Rubric analysis results
              </Typography>

              <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                Analysis output files:
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _analysis.json - Detailed rubric analysis
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _report.md - Human-readable analysis report
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                • _summary.json - Key metrics and insights
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                Rubric analysis provides deeper insights into judge decision patterns.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default JudgeRubric; 