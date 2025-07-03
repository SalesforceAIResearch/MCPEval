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
} from '@mui/icons-material';

interface ServerConfig {
  path: string;
  args: string[];
}

interface GenerationProgress {
  isRunning: boolean;
  currentTask: number;
  totalTasks: number;
  status: string;
  logs: string[];
}

const TaskGenerator: React.FC = () => {
  const [servers, setServers] = useState<ServerConfig[]>([
    { path: '', args: [] },
  ]);
  const [outputFile, setOutputFile] = useState('generated_tasks.jsonl');
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
  });

  const addServer = () => {
    setServers([...servers, { path: '', args: [] }]);
  };

  const removeServer = (index: number) => {
    setServers(servers.filter((_, i) => i !== index));
  };

  const updateServerPath = (index: number, path: string) => {
    const newServers = [...servers];
    newServers[index].path = path;
    setServers(newServers);
  };

  const updateServerArgs = (index: number, argsString: string) => {
    const newServers = [...servers];
    newServers[index].args = argsString.split(' ').filter(arg => arg.trim());
    setServers(newServers);
  };

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

  const handleGenerate = async () => {
    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks: numTasks,
      status: 'Starting task generation...',
      logs: ['Initializing task generator...'],
    });

    try {
      const payload = {
        servers: servers.filter(s => s.path.trim()),
        output: outputFile,
        num_tasks: numTasks,
        existing_files: existingFiles.filter(f => f.trim()),
        prompt_file: promptFile || null,
        model,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
        api_key: apiKey || null,
      };

      // TODO: Replace with actual API call
      console.log('Generation payload:', payload);

      // Simulate progress
      for (let i = 1; i <= numTasks; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        setProgress(prev => ({
          ...prev,
          currentTask: i,
          status: `Generating task ${i}/${numTasks}`,
          logs: [...prev.logs, `Generated task ${i}: Sample task name`],
        }));
      }

      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: 'Generation completed successfully!',
        logs: [...prev.logs, `All ${numTasks} tasks generated successfully`],
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

              {/* Server Configuration */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                    MCP Servers
                  </Typography>
                  <Tooltip title="Add another server for multi-server task generation">
                    <IconButton onClick={addServer} color="primary">
                      <AddIcon />
                    </IconButton>
                  </Tooltip>
                </Box>

                {servers.map((server, index) => (
                  <Box
                    key={index}
                    sx={{
                      mb: 2,
                      p: 2,
                      border: '1px solid #e0e0e0',
                      borderRadius: 1,
                    }}
                  >
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label={`Server ${index + 1} Path`}
                          value={server.path}
                          onChange={e =>
                            updateServerPath(index, e.target.value)
                          }
                          placeholder="@openbnb/mcp-server-airbnb"
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} md={5}>
                        <TextField
                          fullWidth
                          label="Server Arguments"
                          value={server.args.join(' ')}
                          onChange={e =>
                            updateServerArgs(index, e.target.value)
                          }
                          placeholder="--debug --timeout 30"
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} md={1}>
                        {servers.length > 1 && (
                          <IconButton
                            onClick={() => removeServer(index)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </Grid>
                    </Grid>
                  </Box>
                ))}
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Basic Settings */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Output File"
                    value={outputFile}
                    onChange={e => setOutputFile(e.target.value)}
                    helperText="Path where generated tasks will be saved"
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
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Prompt File (Optional)"
                    value={promptFile}
                    onChange={e => setPromptFile(e.target.value)}
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
                  onClick={handleGenerate}
                  disabled={progress.isRunning || !servers[0].path}
                  startIcon={progress.isRunning ? <Stop /> : <PlayArrow />}
                  size="large"
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
                    completed
                  </Typography>
                </Box>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Status: {progress.status || 'Ready to generate'}
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
                    <div key={index}>{log}</div>
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
                      console.log('Download file:', outputFile);
                    }}
                  >
                    Download Results
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
                Quick Tips
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
              <Typography variant="body2">
                • Existing files help avoid generating duplicate tasks
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TaskGenerator;
