import React, { useState } from 'react';
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
} from '@mui/material';
import {
  CheckCircle as VerifyIcon,
  PlayArrow,
  Stop,
  Upload,
  Download,
  Info,
  Warning,
} from '@mui/icons-material';

interface VerificationProgress {
  isRunning: boolean;
  currentTask: number;
  totalTasks: number;
  passedTasks: number;
  failedTasks: number;
  status: string;
  logs: string[];
}

const TaskVerifier: React.FC = () => {
  const [serverPath, setServerPath] = useState('');
  const [serverArgs, setServerArgs] = useState('');
  const [tasksFile, setTasksFile] = useState('');
  const [outputFile, setOutputFile] = useState('');
  const [model, setModel] = useState('gpt-4.1-2025-04-14');
  const [numTasks, setNumTasks] = useState(-1);
  const [apiKey, setApiKey] = useState('');

  const [progress, setProgress] = useState<VerificationProgress>({
    isRunning: false,
    currentTask: 0,
    totalTasks: 0,
    passedTasks: 0,
    failedTasks: 0,
    status: '',
    logs: [],
  });

  const handleVerify = async () => {
    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks: numTasks === -1 ? 50 : numTasks, // Simulate 50 total tasks if -1
      passedTasks: 0,
      failedTasks: 0,
      status: 'Starting task verification...',
      logs: ['Connecting to MCP server...', 'Loading tasks from file...'],
    });

    try {
      const payload = {
        server: serverPath,
        server_args: serverArgs.split(' ').filter(arg => arg.trim()),
        tasks_file: tasksFile,
        output: outputFile || `verified_${tasksFile.split('/').pop()}`,
        model,
        num_tasks: numTasks,
        api_key: apiKey || null,
      };

      // TODO: Replace with actual API call
      console.log('Verification payload:', payload);

      // Simulate verification progress
      const totalTasks = numTasks === -1 ? 50 : numTasks;
      for (let i = 1; i <= totalTasks; i++) {
        await new Promise(resolve => setTimeout(resolve, 1500));

        const passed = Math.random() > 0.2; // 80% pass rate simulation
        setProgress(prev => ({
          ...prev,
          currentTask: i,
          passedTasks: prev.passedTasks + (passed ? 1 : 0),
          failedTasks: prev.failedTasks + (passed ? 0 : 1),
          status: `Verifying task ${i}/${totalTasks}`,
          logs: [
            ...prev.logs,
            `Task ${i}: ${passed ? 'PASSED' : 'FAILED'} - ${passed ? 'Successfully executed' : 'Execution error'}`,
          ],
        }));
      }

      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: `Verification completed! ${prev.passedTasks}/${prev.totalTasks} tasks passed`,
        logs: [
          ...prev.logs,
          `Verification summary: ${prev.passedTasks} passed, ${prev.failedTasks} failed`,
        ],
      }));
    } catch (error) {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: `Error: ${error}`,
        logs: [...prev.logs, `Error: ${error}`],
      }));
    }
  };

  const handleStop = () => {
    setProgress(prev => ({
      ...prev,
      isRunning: false,
      status: 'Verification stopped by user',
      logs: [...prev.logs, 'Verification stopped by user'],
    }));
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

              {/* Server Configuration */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <TextField
                    fullWidth
                    label="MCP Server Path"
                    value={serverPath}
                    onChange={e => setServerPath(e.target.value)}
                    placeholder="@openbnb/mcp-server-airbnb"
                    helperText="Path to the MCP server script"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Server Arguments"
                    value={serverArgs}
                    onChange={e => setServerArgs(e.target.value)}
                    placeholder="--debug --timeout 30"
                    helperText="Additional server arguments"
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* File Configuration */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Tasks File"
                    value={tasksFile}
                    onChange={e => setTasksFile(e.target.value)}
                    placeholder="data/tasks.jsonl"
                    helperText="Path to JSONL file containing tasks to verify"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Output File (Optional)"
                    value={outputFile}
                    onChange={e => setOutputFile(e.target.value)}
                    placeholder="verified_tasks.jsonl"
                    helperText="Output file for verified tasks (auto-generated if empty)"
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Verification Settings */}
              <Typography variant="subtitle1" gutterBottom>
                Verification Settings
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Model"
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    placeholder="Enter model name (e.g., gpt-4.1-2025-04-14)"
                    helperText="Specify the AI model to use for verification"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Number of Tasks"
                    value={numTasks}
                    onChange={e => setNumTasks(parseInt(e.target.value) || -1)}
                    helperText="Use -1 to verify all tasks"
                    inputProps={{ min: -1, max: 1000 }}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
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
                  onClick={handleVerify}
                  disabled={progress.isRunning || !serverPath || !tasksFile}
                  startIcon={progress.isRunning ? <Stop /> : <VerifyIcon />}
                  size="large"
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
                    variant="determinate"
                    value={(progress.currentTask / progress.totalTasks) * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.currentTask} / {progress.totalTasks} tasks
                    verified
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

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Status: {progress.status || 'Ready to verify'}
              </Typography>

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

              {!progress.isRunning && progress.currentTask > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => {
                      // TODO: Implement file download
                      console.log('Download verified tasks');
                    }}
                  >
                    Download Verified Tasks
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
                Verification Tips
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Verification checks if tasks can be executed successfully on the
                MCP server
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Failed tasks indicate server compatibility issues
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Use -1 to verify all tasks in the file
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Server arguments should match generation settings
              </Typography>
              <Typography variant="body2">
                • Verified tasks are ready for model evaluation
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TaskVerifier;
