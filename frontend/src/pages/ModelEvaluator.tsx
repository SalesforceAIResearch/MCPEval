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
  Switch,
  FormControlLabel,
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
} from '@mui/icons-material';

interface ModelConfig {
  name: string;
  model: string;
  temperature: number;
  maxTokens: number;
  apiKey: string;
  baseUrl: string;
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
}

const ModelEvaluator: React.FC = () => {
  const [serverPath, setServerPath] = useState('');
  const [serverArgs, setServerArgs] = useState('');
  const [tasksFile, setTasksFile] = useState('');
  const [outputFile, setOutputFile] = useState('');
  const [maxTurns, setMaxTurns] = useState(30);
  const [promptFile, setPromptFile] = useState('');
  const [multiServer, setMultiServer] = useState(false);

  const [models, setModels] = useState<ModelConfig[]>([
    {
      name: 'GPT-4o',
      model: 'gpt-4o',
      temperature: 0.1,
      maxTokens: 4000,
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
  });

  const addModel = () => {
    setModels([
      ...models,
      {
        name: `Model ${models.length + 1}`,
        model: 'gpt-4o',
        temperature: 0.1,
        maxTokens: 4000,
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

  const handleEvaluate = async () => {
    const totalTasks = 25; // Simulate 25 tasks
    setProgress({
      isRunning: true,
      currentTask: 0,
      totalTasks,
      currentModel: models[0].name,
      successfulTasks: 0,
      failedTasks: 0,
      status: 'Starting model evaluation...',
      logs: [
        'Initializing evaluation environment...',
        'Loading tasks and connecting to servers...',
      ],
    });

    try {
      const payload = {
        server: serverPath,
        server_args: serverArgs.split(' ').filter(arg => arg.trim()),
        tasks_file: tasksFile,
        output: outputFile,
        models: models.map(m => ({
          name: m.name,
          config: {
            model: m.model,
            temperature: m.temperature,
            max_tokens: m.maxTokens,
            api_key: m.apiKey || null,
            base_url: m.baseUrl || null,
          },
        })),
        max_turns: maxTurns,
        prompt_file: promptFile || null,
        multi_server: multiServer,
      };

      // TODO: Replace with actual API call
      console.log('Evaluation payload:', payload);

      // Simulate evaluation progress for each model
      for (let modelIndex = 0; modelIndex < models.length; modelIndex++) {
        const currentModel = models[modelIndex];
        setProgress(prev => ({
          ...prev,
          currentModel: currentModel.name,
          status: `Evaluating ${currentModel.name}...`,
          logs: [...prev.logs, `Starting evaluation with ${currentModel.name}`],
        }));

        for (let i = 1; i <= totalTasks; i++) {
          await new Promise(resolve => setTimeout(resolve, 2000));

          const success = Math.random() > 0.15; // 85% success rate simulation
          setProgress(prev => ({
            ...prev,
            currentTask: i + modelIndex * totalTasks,
            successfulTasks: prev.successfulTasks + (success ? 1 : 0),
            failedTasks: prev.failedTasks + (success ? 0 : 1),
            status: `${currentModel.name}: Task ${i}/${totalTasks}`,
            logs: [
              ...prev.logs,
              `${currentModel.name} - Task ${i}: ${success ? 'SUCCESS' : 'FAILED'}`,
            ],
          }));
        }
      }

      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: `Evaluation completed! ${prev.successfulTasks}/${prev.totalTasks * models.length} tasks successful`,
        logs: [
          ...prev.logs,
          `Evaluation complete. Results saved to ${outputFile}`,
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
      status: 'Evaluation stopped by user',
      logs: [...prev.logs, 'Evaluation stopped by user'],
    }));
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Model Evaluation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Evaluate models using MCP servers and tasks with comprehensive
          performance analysis
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

              {/* Server Configuration */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <TextField
                    fullWidth
                    label="MCP Server Path"
                    value={serverPath}
                    onChange={e => setServerPath(e.target.value)}
                    placeholder="@openbnb/mcp-server-airbnb"
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
                  />
                </Grid>
              </Grid>

              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={multiServer}
                      onChange={e => setMultiServer(e.target.checked)}
                    />
                  }
                  label="Multi-server evaluation"
                />
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Task Configuration */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Tasks File"
                    value={tasksFile}
                    onChange={e => setTasksFile(e.target.value)}
                    placeholder="data/verified_tasks.jsonl"
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Output File"
                    value={outputFile}
                    onChange={e => setOutputFile(e.target.value)}
                    placeholder="evaluation_results.json"
                    required
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
                        />
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Model</InputLabel>
                          <Select
                            value={model.model}
                            label="Model"
                            onChange={e =>
                              updateModel(index, 'model', e.target.value)
                            }
                          >
                            <MenuItem value="gpt-4o">GPT-4o</MenuItem>
                            <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
                            <MenuItem value="gpt-4">GPT-4</MenuItem>
                            <MenuItem value="gpt-3.5-turbo">
                              GPT-3.5 Turbo
                            </MenuItem>
                            <MenuItem value="claude-3-opus">
                              Claude 3 Opus
                            </MenuItem>
                            <MenuItem value="claude-3-sonnet">
                              Claude 3 Sonnet
                            </MenuItem>
                          </Select>
                        </FormControl>
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
                              parseFloat(e.target.value) || 0.1
                            )
                          }
                          inputProps={{ min: 0, max: 2, step: 0.1 }}
                        />
                      </Grid>
                      <Grid item xs={12} md={2}>
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
                          type="password"
                          label="API Key (Optional)"
                          value={model.apiKey}
                          onChange={e =>
                            updateModel(index, 'apiKey', e.target.value)
                          }
                          helperText="Uses environment variable if not provided"
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
                    console.log('Upload tasks file');
                  }}
                >
                  Upload Tasks
                </Button>
                <Button
                  variant="contained"
                  onClick={handleEvaluate}
                  disabled={
                    progress.isRunning ||
                    !serverPath ||
                    !tasksFile ||
                    !outputFile
                  }
                  startIcon={progress.isRunning ? <Stop /> : <EvaluateIcon />}
                  size="large"
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
                    variant="determinate"
                    value={
                      (progress.currentTask /
                        (progress.totalTasks * models.length)) *
                      100
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    {progress.currentTask} /{' '}
                    {progress.totalTasks * models.length} total tasks
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

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Status: {progress.status || 'Ready to evaluate'}
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
                        color: log.includes('SUCCESS')
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
                      console.log('Download evaluation results');
                    }}
                    sx={{ mb: 1 }}
                  >
                    Download Results
                  </Button>
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
                Evaluates how well models perform on your MCP tasks
              </Alert>

              <Typography variant="body2" sx={{ mb: 1 }}>
                • Use verified tasks for accurate results
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Compare multiple models simultaneously
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Adjust max turns based on task complexity
              </Typography>
              <Typography variant="body2">
                • Results include conversation logs and metrics
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ModelEvaluator;
