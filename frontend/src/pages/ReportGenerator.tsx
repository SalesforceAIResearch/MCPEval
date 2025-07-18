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
  Alert,
  LinearProgress,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  FormControlLabel,
  Checkbox,
  Paper,
} from '@mui/material';
import {
  Assessment as ReportIcon,
  InsertDriveFile as FileIcon,
  PlayArrow,
  Stop,
  Download,
  Refresh,
  Info,
  BarChart,
  Timeline,
  FolderOpen,
  Launch,
} from '@mui/icons-material';

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
}

interface ReportProgress {
  isRunning: boolean;
  status: string;
  logs: string[];
  jobId?: string;
  outputPath?: string;
  reportType?: string;
}

const ReportGenerator: React.FC = () => {
  const navigate = useNavigate();
  const [domainName, setDomainName] = useState('');
  const [availableFiles, setAvailableFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // File selection states
  const [toolAnalysisFile, setToolAnalysisFile] = useState('');
  const [llmJudgeFile, setLlmJudgeFile] = useState('');
  const [outputFileName, setOutputFileName] = useState('');

  // Options
  const [includeCharts, setIncludeCharts] = useState(true);
  const [customOutputPath, setCustomOutputPath] = useState('');
  const [model, setModel] = useState('gpt-4o');

  // Progress tracking
  const [progress, setProgress] = useState<ReportProgress>({
    isRunning: false,
    status: '',
    logs: [],
    jobId: undefined,
    outputPath: undefined,
    reportType: undefined,
  });

  // Available models for report generation
  const availableModels = [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-4',
    'gpt-3.5-turbo',
    'claude-3-5-sonnet-20241022',
    'claude-3-opus-20240229',
    'claude-3-haiku-20240307',
  ];

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
      fetchFilesFromDomain(domainName);
    } else {
      setAvailableFiles([]);
      setToolAnalysisFile('');
      setLlmJudgeFile('');
    }
  }, [domainName]);

  const fetchFilesFromDomain = async (domain: string) => {
    if (!domain.trim()) {
      setAvailableFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Fetch files from report, reports, and analysis directories
      const reportPaths = [`data/${domain}/report`, `data/${domain}/reports`, `data/${domain}/analysis`];

      const allFiles: FileInfo[] = [];

      for (const path of reportPaths) {
        try {
          const response = await fetch(`/api/files?directory=${path}`);
          if (response.ok) {
            const data = await response.json();
            // Filter to only show .json and .jsonl files
            const jsonFiles = (data.files || []).filter((file: FileInfo) =>
              file.name.endsWith('.json') || file.name.endsWith('.jsonl')
            );
            allFiles.push(...jsonFiles);
          }
        } catch (error) {
          console.error(`Error fetching files from ${path}:`, error);
        }
      }

      // Remove duplicates and sort by name
      const uniqueFiles = allFiles.filter(
        (file, index, self) =>
          index === self.findIndex(f => f.name === file.name)
      );
      uniqueFiles.sort((a, b) => a.name.localeCompare(b.name));

      setAvailableFiles(uniqueFiles);
    } catch (error) {
      console.error('Error fetching files:', error);
      setAvailableFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleViewOutputFiles = () => {
    if (progress.outputPath) {
      // Check if outputPath is a file or directory
      const outputPath = progress.outputPath;
      if (outputPath.includes('.')) {
        // It's likely a file path, extract the directory and filename
        const dirPath = outputPath.substring(0, outputPath.lastIndexOf('/'));
        const fileName = outputPath.substring(outputPath.lastIndexOf('/') + 1);
        navigate(
          `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(fileName)}`
        );
      } else {
        // It's likely a directory path
        navigate(`/data-files?path=${encodeURIComponent(outputPath)}`);
      }
    }
  };

  const handleGenerateReport = async () => {
    if (!toolAnalysisFile && !llmJudgeFile) {
      return;
    }

    const reportType = determineReportType();

    setProgress({
      isRunning: true,
      status: 'Starting report generation...',
      logs: ['Initializing report generator...'],
      jobId: undefined,
      outputPath: undefined,
      reportType: reportType,
    });

    try {
      const payload: any = {
        include_charts: includeCharts,
        model: model,
      };

      if (toolAnalysisFile) {
        payload.tool_analysis_file = toolAnalysisFile;
      }
      if (llmJudgeFile) {
        payload.llm_judge_file = llmJudgeFile;
      }
      if (outputFileName.trim()) {
        payload.output_file = outputFileName.trim();
      }
      if (customOutputPath.trim()) {
        payload.output_path = customOutputPath.trim();
      }

      const response = await fetch('/api/generate-report', {
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
      const outputPath = data.output_path;
      const detectedReportType = data.report_type;

      setProgress(prev => ({
        ...prev,
        status: 'Report generation started successfully',
        logs: [
          ...prev.logs,
          'Report generation job started, tracking progress...',
          outputPath ? `Report will be saved to: ${outputPath}` : '',
        ],
        jobId: jobId,
        outputPath: outputPath,
        reportType: detectedReportType,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/jobs/${jobId}`);

          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            const { progress: jobProgress, logs } = statusData;

            // Extract status from the nested progress object
            const status = jobProgress?.status || 'running';

            setProgress(prev => ({
              ...prev,
              status:
                status === 'running'
                  ? 'Running...'
                  : status === 'completed'
                    ? 'Report generation completed!'
                    : status === 'failed'
                      ? 'Report generation failed'
                      : status === 'cancelled'
                        ? 'Report generation cancelled'
                        : prev.status,
              logs: logs || prev.logs,
            }));

            // Check if job is complete
            if (
              status === 'completed' ||
              status === 'failed' ||
              status === 'cancelled'
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
          }
        } catch (error) {
          console.error('Error polling job status:', error);
        }
      }, 1000);

      // Set timeout to stop polling after 10 minutes
      timeoutRef.current = setTimeout(
        () => {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }

          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Report generation timed out',
            logs: [
              ...prev.logs,
              'Report generation timed out after 10 minutes',
            ],
          }));
        },
        10 * 60 * 1000
      );
    } catch (error) {
      setProgress({
        isRunning: false,
        status: 'Error starting report generation',
        logs: [
          error instanceof Error ? error.message : 'Unknown error occurred',
        ],
      });
    }
  };

  const handleStop = async () => {
    if (progress.jobId) {
      try {
        await fetch(`/api/jobs/${progress.jobId}/kill`, {
          method: 'POST',
        });
      } catch (error) {
        console.error('Error stopping job:', error);
      }
    }

    // Clear polling
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
      status: 'Report generation stopped',
      logs: [...prev.logs, 'Report generation stopped by user'],
    }));
  };

  const determineReportType = () => {
    if (toolAnalysisFile && llmJudgeFile) {
      return 'Comprehensive Report';
    } else if (toolAnalysisFile) {
      return 'Tool Usage Report';
    } else if (llmJudgeFile) {
      return 'LLM Judge Report';
    }
    return 'Report';
  };

  const isConfigValid = () => {
    return (toolAnalysisFile || llmJudgeFile) && domainName.trim();
  };

  const downloadReport = () => {
    if (progress.outputPath) {
      const link = document.createElement('a');
      link.href = `/api/download?path=${encodeURIComponent(progress.outputPath)}`;
      link.download = outputFileName || 'report.md';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const getFileTypeIcon = (fileName: string) => {
    if (isToolAnalysisFile(fileName)) {
      return <BarChart color="primary" />;
    } else if (isLlmJudgeFile(fileName)) {
      return <Timeline color="secondary" />;
    }
    return <FileIcon />;
  };

  const getFileTypeDescription = (fileName: string) => {
    if (fileName.endsWith('.jsonl')) {
      return 'JSONL Analysis File';
    }
    return 'JSON Analysis File';
  };

  const isToolAnalysisFile = (fileName: string) => {
    // Allow any JSON or JSONL file to be used as tool analysis file
    return fileName.endsWith('.json') || fileName.endsWith('.jsonl');
  };

  const isLlmJudgeFile = (fileName: string) => {
    // Allow any JSON or JSONL file to be used as LLM judge file
    return fileName.endsWith('.json') || fileName.endsWith('.jsonl');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Report Generator
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Generate AI-powered evaluation reports from analysis files. Select
          tool analysis files, LLM judge files, or both to create comprehensive
          reports with optional charts.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Configuration
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                Generate comprehensive AI-powered reports from your analysis
                files with optional charts and visualizations.
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
                    placeholder="e.g., healthcare, airbnb, sports"
                    helperText="The domain name (e.g., healthcare, airbnb, sports, yfinance)"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="Refresh file lists">
                      <IconButton
                        onClick={() => fetchFilesFromDomain(domainName)}
                        disabled={!domainName.trim() || loadingFiles}
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                    <Typography variant="body2" color="text.secondary">
                      {loadingFiles
                        ? 'Loading files from report, reports, and analysis directories...'
                        : 'Click to refresh file lists'}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* File Selection */}
              {domainName && !loadingFiles && (
                <>
                  <Typography variant="subtitle1" gutterBottom>
                    📄 Select Analysis Files
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    Choose tool analysis files, LLM judge files, or both from
                    the {domainName} domain (searches in report/, reports/, and analysis/ directories)
                  </Typography>

                  {availableFiles.length === 0 ? (
                    <Alert severity="info">
                      <Typography variant="body2">
                        No JSON or JSONL files found in {domainName}/report, {domainName}/reports, or{' '}
                        {domainName}/analysis directories.
                        <br />
                        Make sure you've entered the correct domain name and
                        that analysis files exist.
                      </Typography>
                    </Alert>
                  ) : (
                    <>
                      <Paper
                        variant="outlined"
                        sx={{ maxHeight: 400, overflow: 'auto' }}
                      >
                        <List>
                          {availableFiles.map((file, index) => (
                            <ListItem key={index} divider>
                              <ListItemIcon>
                                {getFileTypeIcon(file.name)}
                              </ListItemIcon>
                              <ListItemText
                                primary={file.name}
                                secondary={
                                  <Box>
                                    <Typography
                                      variant="body2"
                                      color="text.secondary"
                                    >
                                      {getFileTypeDescription(file.name)} •{' '}
                                      {formatFileSize(file.size)}
                                    </Typography>
                                    <Typography
                                      variant="caption"
                                      color="text.secondary"
                                    >
                                      {file.path}
                                    </Typography>
                                  </Box>
                                }
                              />
                              <Box>
                                <Button
                                  size="small"
                                  variant={
                                    toolAnalysisFile === file.path
                                      ? 'contained'
                                      : 'outlined'
                                  }
                                  onClick={() =>
                                    setToolAnalysisFile(
                                      toolAnalysisFile === file.path
                                        ? ''
                                        : file.path
                                    )
                                  }
                                  sx={{ mr: 1 }}
                                >
                                  Tool Analysis
                                </Button>
                                <Button
                                  size="small"
                                  variant={
                                    llmJudgeFile === file.path
                                      ? 'contained'
                                      : 'outlined'
                                  }
                                  onClick={() =>
                                    setLlmJudgeFile(
                                      llmJudgeFile === file.path
                                        ? ''
                                        : file.path
                                    )
                                  }
                                >
                                  LLM Judge
                                </Button>
                              </Box>
                            </ListItem>
                          ))}
                        </List>
                      </Paper>

                      {/* Selected Files Display */}
                      {(toolAnalysisFile || llmJudgeFile) && (
                        <Box mt={2}>
                          <Typography variant="subtitle2" gutterBottom>
                            Selected Files:
                          </Typography>
                          {toolAnalysisFile && (
                            <Chip
                              label={`Tool Analysis: ${toolAnalysisFile.split('/').pop()}`}
                              color="primary"
                              sx={{ mr: 1, mb: 1 }}
                              onDelete={() => setToolAnalysisFile('')}
                            />
                          )}
                          {llmJudgeFile && (
                            <Chip
                              label={`LLM Judge: ${llmJudgeFile.split('/').pop()}`}
                              color="secondary"
                              sx={{ mr: 1, mb: 1 }}
                              onDelete={() => setLlmJudgeFile('')}
                            />
                          )}
                        </Box>
                      )}
                    </>
                  )}

                  <Divider sx={{ my: 3 }} />
                </>
              )}

              {/* Options */}
              <Typography variant="subtitle1" gutterBottom>
                ⚙️ Report Generation Options
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth margin="normal">
                    <InputLabel>AI Model</InputLabel>
                    <Select
                      value={model}
                      onChange={e => setModel(e.target.value)}
                      label="AI Model"
                    >
                      {availableModels.map(m => (
                        <MenuItem key={m} value={m}>
                          {m}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      Select a model for AI-powered report generation
                    </FormHelperText>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Box mt={2}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={includeCharts}
                          onChange={e => setIncludeCharts(e.target.checked)}
                        />
                      }
                      label="Include Charts and Visualizations"
                    />
                  </Box>
                </Grid>
              </Grid>

              <TextField
                fullWidth
                label="Output File Name"
                value={outputFileName}
                onChange={e => setOutputFileName(e.target.value)}
                placeholder="e.g., my_report.md"
                margin="normal"
                helperText="Optional: Leave blank for auto-generated name based on model and report type"
              />

              <TextField
                fullWidth
                label="Custom Output Path"
                value={customOutputPath}
                onChange={e => setCustomOutputPath(e.target.value)}
                placeholder="e.g., data/reports/custom/"
                margin="normal"
                helperText="Optional: Leave blank to use default location in the same directory as analysis files"
              />

              {/* Action Buttons */}
              <Box display="flex" gap={2} mt={3}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGenerateReport}
                  disabled={!isConfigValid() || progress.isRunning}
                  startIcon={<PlayArrow />}
                >
                  {progress.isRunning
                    ? 'Generating...'
                    : `Generate ${determineReportType()} with ${model}`}
                </Button>

                {progress.isRunning && (
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={handleStop}
                    startIcon={<Stop />}
                    color="error"
                  >
                    Stop
                  </Button>
                )}

                {progress.outputPath && !progress.isRunning && (
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={downloadReport}
                    startIcon={<Download />}
                  >
                    Download Report
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Progress Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Progress
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Status:</strong>{' '}
                {progress.status || 'Ready to generate report'}
              </Typography>

              {/* Show file paths */}
              {domainName && toolAnalysisFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Tool Analysis:</strong>{' '}
                  {toolAnalysisFile.split('/').pop()}
                </Typography>
              )}

              {domainName && llmJudgeFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>LLM Judge:</strong> {llmJudgeFile.split('/').pop()}
                </Typography>
              )}

              {progress.outputPath && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  <strong>Output:</strong> {progress.outputPath}
                </Typography>
              )}

              {/* Show View Files button prominently when generation is complete */}
              {!progress.isRunning && progress.outputPath && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Tooltip title="Click to open the generated report file in the Data Files page">
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<Launch />}
                      onClick={handleViewOutputFiles}
                      color="success"
                      size="small"
                    >
                      📁 Open Generated Report
                    </Button>
                  </Tooltip>
                </Box>
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

              {progress.isRunning && (
                <Box sx={{ mt: 2 }}>
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

              {!progress.isRunning && progress.outputPath && (
                <Box sx={{ mt: 2 }}>
                  <Tooltip title="Navigate to the Data Files page to view and manage the generated report">
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<FolderOpen />}
                      onClick={handleViewOutputFiles}
                    >
                      View Output File
                    </Button>
                  </Tooltip>
                </Box>
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
                Report Generation Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Generate comprehensive AI-powered reports from your analysis
                files with optional charts and visualizations.
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                                  • Enter your domain name (e.g., healthcare, airbnb)
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Select analysis files from report, reports, or analysis directories
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Choose AI model for report generation
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Enable charts for visual insights
              </Typography>
              <Typography variant="body2">
                • Reports are saved with timestamp
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
                📊 Report Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📁 <strong>report/</strong> - Analysis files
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📁 <strong>reports/</strong> - Analysis files (alternative)
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📁 <strong>analysis/</strong> - Analysis files (alternative)
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📊 <strong>Output:</strong> AI-generated reports with insights
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                Generate comprehensive reports with AI insights and optional
                visualizations.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Results Display */}
      {!progress.isRunning && progress.outputPath && (
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Alert severity="success">
              <Typography variant="body2">
                Report generated successfully! Output saved to:{' '}
                {progress.outputPath}
              </Typography>
            </Alert>
          </Grid>
        </Grid>
      )}

      {/* Error Display */}
      {!progress.isRunning && progress.status.includes('Error') && (
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Alert severity="error">
              <Typography variant="body2">{progress.status}</Typography>
              {progress.logs.length > 0 && (
                <Box mt={1}>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {progress.logs[progress.logs.length - 1]}
                  </Typography>
                </Box>
              )}
            </Alert>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default ReportGenerator;
