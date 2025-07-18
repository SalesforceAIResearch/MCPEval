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
  Analytics as AnalyzeIcon,
  Upload,
  Download,
  Info,
  TrendingUp,
  Refresh,
  Stop,
  Launch,
} from '@mui/icons-material';

interface AnalysisProgress {
  isRunning: boolean;
  status: string;
  logs: string[];
  jobId?: string;
  outputPath?: string;
  reportOutput?: string;
  domain?: string;
}

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
}

const Analyzer: React.FC = () => {
  const navigate = useNavigate();
  const [domainName, setDomainName] = useState('');
  const [evaluationFile, setEvaluationFile] = useState('');
  const [groundTruthFile, setGroundTruthFile] = useState('');
  const [summaryFileName, setSummaryFileName] = useState('');
  const [reportFileName, setReportFileName] = useState('');
  const [generateReport, setGenerateReport] = useState(true);
  const [includeCharts, setIncludeCharts] = useState(false);
  const [chartFormats, setChartFormats] = useState<string[]>(['html', 'png']);
  const [model, setModel] = useState('gpt-4o');

  // File listing states
  const [evaluationFiles, setEvaluationFiles] = useState<FileInfo[]>([]);
  const [groundTruthFiles, setGroundTruthFiles] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Progress tracking
  const [progress, setProgress] = useState<AnalysisProgress>({
    isRunning: false,
    status: '',
    logs: [],
    jobId: undefined,
    outputPath: undefined,
    reportOutput: undefined,
    domain: undefined,
  });

  // Refs for polling
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Helper function to get base name from evaluation file
  const getBaseNameFromEvaluationFile = (fileName: string): string => {
    if (!fileName) return '';
    const lastDotIndex = fileName.lastIndexOf('.');
    return lastDotIndex > 0 ? fileName.substring(0, lastDotIndex) : fileName;
  };

  // Get effective output file names (custom or derived from evaluation file)
  const getEffectiveSummaryFileName = (): string => {
    if (summaryFileName.trim()) {
      // If user provided a custom name, use it as-is (they can include .json or not)
      return summaryFileName.endsWith('.json') ? summaryFileName : `${summaryFileName}.json`;
    }
    // Use evaluation file base name as default
    const baseName = getBaseNameFromEvaluationFile(evaluationFile);
    return baseName ? `${baseName}_summary.json` : '';
  };

  const getEffectiveReportFileName = (): string => {
    if (reportFileName.trim()) {
      // If user provided a custom name, use it as-is (they can include .md or not)
      return reportFileName.endsWith('.md') ? reportFileName : `${reportFileName}.md`;
    }
    // Use evaluation file base name as default
    const baseName = getBaseNameFromEvaluationFile(evaluationFile);
    return baseName ? `${baseName}_report.md` : '';
  };

  // Get expected output file names
  const getExpectedOutputFiles = () => {
    return {
      summary: getEffectiveSummaryFileName(),
      report: getEffectiveReportFileName()
    };
  };

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
      setGroundTruthFiles([]);
      setEvaluationFile('');
      setGroundTruthFile('');
    }
  }, [domainName]);

  const fetchFiles = async (domain: string) => {
    if (!domain.trim()) {
      setEvaluationFiles([]);
      setGroundTruthFiles([]);
      return;
    }

    setLoadingFiles(true);
    try {
      // Use correct relative paths from workspace root
      // Backend root is set to workspace, so we use relative paths from there
      const evaluationPath = `data/${domain}/evaluations`;
      const groundTruthPath = `data/${domain}/verified_tasks`;

      const [evaluationResponse, groundTruthResponse] = await Promise.all([
        fetch(`/api/files?directory=${evaluationPath}`),
        fetch(`/api/files?directory=${groundTruthPath}`),
      ]);

      if (evaluationResponse.ok) {
        const evaluationData = await evaluationResponse.json();
        setEvaluationFiles(evaluationData.files || []);
      } else {
        console.error('Failed to fetch evaluation files');
        setEvaluationFiles([]);
      }

      if (groundTruthResponse.ok) {
        const groundTruthData = await groundTruthResponse.json();
        setGroundTruthFiles(groundTruthData.files || []);
      } else {
        console.error('Failed to fetch ground truth files');
        setGroundTruthFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setEvaluationFiles([]);
      setGroundTruthFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleAnalyze = async () => {
    if (!domainName.trim() || !evaluationFile || !groundTruthFile) {
      return;
    }

    // Find the selected files to get their full paths
    const selectedEvaluationFile = evaluationFiles.find(
      f => f.name === evaluationFile
    );
    const selectedGroundTruthFile = groundTruthFiles.find(
      f => f.name === groundTruthFile
    );

    if (!selectedEvaluationFile || !selectedGroundTruthFile) {
      setProgress({
        isRunning: false,
        status: 'Error: Selected files not found',
        logs: ['Error: Selected files not found'],
      });
      return;
    }

    // Use the relative paths from the file listing API
    // The backend will resolve these relative to the workspace root
    const resultsPath = selectedEvaluationFile.path;
    const groundTruthPath = selectedGroundTruthFile.path;

    setProgress({
      isRunning: true,
      status: 'Starting analysis...',
      logs: ['Initializing analysis...'],
      jobId: undefined,
      outputPath: undefined,
      reportOutput: undefined,
      domain: domainName,
    });

    try {
      const payload = {
        results_dir: resultsPath,
        ground_truth: groundTruthPath,
        generate_report: generateReport,
        model: model,
        include_charts: includeCharts,
        chart_formats: chartFormats,
        summary_filename: getEffectiveSummaryFileName(),
        report_filename: getEffectiveReportFileName(),
      };

      // Call the backend API with the appropriate endpoint
      const endpoint = includeCharts
        ? '/api/analyze-results/comprehensive'
        : '/api/analyze-results/basic';
      const response = await fetch(endpoint, {
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
      const { job_id, domain_name, output_files, timestamp } = data;

      setProgress(prev => ({
        ...prev,
        status: 'Analysis started successfully',
        logs: [...prev.logs, 'Analysis job started, tracking progress...'],
        jobId: job_id,
        outputPath: output_files?.summary || '',
        reportOutput: output_files?.report || '',
        domain: domain_name,
      }));

      // Poll job status for progress updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/jobs/${job_id}`);
          const statusData = await statusResponse.json();

          if (statusResponse.ok && statusData) {
            const { progress: jobProgress, logs: jobLogs } = statusData;

            setProgress(prev => ({
              ...prev,
              status:
                jobProgress.status === 'running'
                  ? 'Analyzing results...'
                  : jobProgress.status === 'completed'
                    ? 'Analysis completed successfully!'
                    : jobProgress.status === 'failed'
                      ? 'Analysis failed'
                      : jobProgress.status === 'cancelled'
                        ? 'Analysis cancelled'
                        : prev.status,
              logs: jobLogs || prev.logs,
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
              }));
            }
          }
        } catch (pollError) {
          console.error('Error polling job status:', pollError);
        }
      }, 2000);

      // Set timeout
      timeoutRef.current = setTimeout(
        () => {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Analysis timed out',
            logs: [...prev.logs, 'Analysis timed out after 30 minutes'],
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
            status: 'Analysis cancelled by user',
            logs: [...prev.logs, 'Analysis cancelled by user'],
          }));
        } else {
          const errorData = await response.json().catch(() => ({}));
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: 'Analysis stopped (cancel failed)',
            logs: [
              ...prev.logs,
              `Cancel failed: ${errorData.error || 'Unknown error'}`,
              'Analysis stopped locally',
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
          status: 'Analysis stopped (cancel failed)',
          logs: [
            ...prev.logs,
            `Cancel failed: ${errorMessage}`,
            'Analysis stopped locally',
          ],
        }));
      }
    } else {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'Analysis stopped by user',
        logs: [...prev.logs, 'Analysis stopped by user'],
      }));
    }
  };

  const isConfigValid = () => {
    return domainName.trim() && evaluationFile && groundTruthFile;
  };

  const handleViewReportFile = () => {
    if (progress.reportOutput) {
      const reportPath = progress.reportOutput;
      const dirPath = reportPath.substring(0, reportPath.lastIndexOf('/'));
      
      navigate(
        `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(reportPath)}`
      );
    }
  };

  const handleViewSummaryFile = () => {
    if (progress.outputPath) {
      const summaryPath = progress.outputPath;
      const dirPath = summaryPath.substring(0, summaryPath.lastIndexOf('/'));
      
      navigate(
        `/data-files?path=${encodeURIComponent(dirPath)}&highlight=${encodeURIComponent(summaryPath)}`
      );
    }
  };



  const downloadReport = () => {
    if (progress.reportOutput) {
      // Create download link for the report
      const link = document.createElement('a');
      link.href = `/api/download/${progress.reportOutput}`;
      link.download = getEffectiveReportFileName() || `analysis_report_${domainName}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🔍 Analyze Results
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Analyze evaluation results against ground truth to generate
          comprehensive performance reports with AI-powered insights
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Configuration
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                Compare evaluation results with ground truth to get detailed
                performance metrics and AI-generated insights.
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
                <Grid item xs={12} md={6}>
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
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Ground Truth File</InputLabel>
                    <Select
                      value={groundTruthFile}
                      onChange={e => setGroundTruthFile(e.target.value)}
                      label="Ground Truth File"
                      disabled={
                        !domainName.trim() || groundTruthFiles.length === 0
                      }
                    >
                      {groundTruthFiles.map(file => (
                        <MenuItem key={file.name} value={file.name}>
                          {file.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {domainName
                        ? `→ workspace/data/${domainName}/verified_tasks/${groundTruthFile || 'select_file.jsonl'}`
                        : 'Select domain first to see available files'}
                    </FormHelperText>
                  </FormControl>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Output Configuration */}
              <Typography variant="subtitle1" gutterBottom>
                Output Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Summary File Name (Optional)"
                    value={summaryFileName}
                    onChange={e => setSummaryFileName(e.target.value)}
                    placeholder={getBaseNameFromEvaluationFile(evaluationFile) ? `${getBaseNameFromEvaluationFile(evaluationFile)}_summary` : "analysis_summary"}
                    helperText={
                      domainName && evaluationFile
                        ? `→ workspace/data/${domainName}/reports/${getExpectedOutputFiles().summary}`
                        : domainName
                        ? `→ workspace/data/${domainName}/reports/${summaryFileName || 'analysis_summary.json'}`
                        : 'Auto-generated based on evaluation file name'
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Report File Name (Optional)"
                    value={reportFileName}
                    onChange={e => setReportFileName(e.target.value)}
                    placeholder={getBaseNameFromEvaluationFile(evaluationFile) ? `${getBaseNameFromEvaluationFile(evaluationFile)}_report` : "analysis_report"}
                    helperText={
                      domainName && evaluationFile
                        ? `→ workspace/data/${domainName}/reports/${getExpectedOutputFiles().report}`
                        : domainName
                        ? `→ workspace/data/${domainName}/reports/${reportFileName || 'analysis_report.md'}`
                        : 'Auto-generated based on evaluation file name'
                    }
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Analysis Settings */}
              <Typography variant="subtitle1" gutterBottom>
                Analysis Settings
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Report Model"
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    placeholder="gpt-4o"
                    helperText="AI model for generating analysis reports"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Generate AI Report</InputLabel>
                    <Select
                      value={generateReport ? 'yes' : 'no'}
                      onChange={e =>
                        setGenerateReport(e.target.value === 'yes')
                      }
                      label="Generate AI Report"
                    >
                      <MenuItem value="yes">Yes - Generate AI Report</MenuItem>
                      <MenuItem value="no">No - Summary Only</MenuItem>
                    </Select>
                    <FormHelperText>
                      AI report provides detailed insights and recommendations
                    </FormHelperText>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Include Charts</InputLabel>
                    <Select
                      value={includeCharts ? 'yes' : 'no'}
                      onChange={e => setIncludeCharts(e.target.value === 'yes')}
                      label="Include Charts"
                    >
                      <MenuItem value="yes">Yes - Generate Charts</MenuItem>
                      <MenuItem value="no">No - Text Only</MenuItem>
                    </Select>
                    <FormHelperText>
                      Generate interactive charts and visualizations
                    </FormHelperText>
                  </FormControl>
                </Grid>
                {includeCharts && (
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Chart Formats</InputLabel>
                      <Select
                        multiple
                        value={chartFormats}
                        onChange={e =>
                          setChartFormats(
                            typeof e.target.value === 'string'
                              ? e.target.value.split(',')
                              : e.target.value
                          )
                        }
                        label="Chart Formats"
                        renderValue={selected => (
                          <Box
                            sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
                          >
                            {selected.map(value => (
                              <Chip
                                key={value}
                                label={value.toUpperCase()}
                                size="small"
                              />
                            ))}
                          </Box>
                        )}
                      >
                        <MenuItem value="html">
                          HTML - Interactive charts
                        </MenuItem>
                        <MenuItem value="png">PNG - Static images</MenuItem>
                        <MenuItem value="svg">SVG - Vector graphics</MenuItem>
                      </Select>
                      <FormHelperText>
                        Select one or more chart output formats
                      </FormHelperText>
                    </FormControl>
                  </Grid>
                )}
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
                  onClick={progress.isRunning ? handleStop : handleAnalyze}
                  disabled={!progress.isRunning && !isConfigValid()}
                  startIcon={progress.isRunning ? <Stop /> : <AnalyzeIcon />}
                  size="large"
                  color={progress.isRunning ? 'error' : 'primary'}
                >
                  {progress.isRunning ? 'Stop Analysis' : 'Analyze Results'}
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
                <strong>Status:</strong> {progress.status || 'Ready to analyze'}
              </Typography>

              {/* Show file paths */}
              {domainName && evaluationFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Evaluation:</strong> {domainName}/evaluations/
                  {evaluationFile}
                </Typography>
              )}

              {domainName && groundTruthFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Ground Truth:</strong> {domainName}/verified_tasks/
                  {groundTruthFile}
                </Typography>
              )}

              {progress.outputPath && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  <strong>Summary:</strong> {progress.outputPath}
                </Typography>
              )}

              {progress.reportOutput && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  <strong>AI Report:</strong> {progress.reportOutput}
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

              {!progress.isRunning && (progress.outputPath || progress.reportOutput) && (
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  {progress.outputPath && (
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Launch />}
                      onClick={handleViewSummaryFile}
                    >
                      View Summary
                    </Button>
                  )}
                  {progress.reportOutput && (
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<Launch />}
                      onClick={handleViewReportFile}
                    >
                      View Report
                    </Button>
                  )}
                  {progress.reportOutput && (
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={downloadReport}
                    >
                      Download
                    </Button>
                  )}
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
                Analysis Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Analysis compares model predictions with expected results to
                generate comprehensive performance insights.
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Domain should match your evaluation domain
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Evaluation file contains model predictions
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Ground truth file contains expected results
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • AI report provides detailed insights and recommendations
              </Typography>
              <Typography variant="body2">
                • Results are saved to reports/ directory
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
                📊 Analysis Pipeline
              </Typography>

              <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                File organization:
              </Typography>

              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ⚡ <strong>evaluations/</strong> - Input: Model predictions
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                ✅ <strong>verified_tasks/</strong> - Input: Ground truth data
              </Typography>
              <Typography variant="body2" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                📊 <strong>reports/</strong> - Output: Analysis results & AI
                insights
              </Typography>

              <Typography
                variant="body2"
                sx={{ mt: 1, fontStyle: 'italic', fontSize: '0.75rem' }}
              >
                Analysis provides comprehensive performance evaluation and
                actionable insights.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Analyzer;
