import React, { useState, useEffect } from 'react';
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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormGroup,
  Tab,
  Tabs,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Save,
  Upload,
  Info,
  Add as AddIcon,
  Delete as DeleteIcon,
  Settings,
  AutoAwesome,
  Folder,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';

interface AutoConfig {
  workspace: string;
  servers: string[];
  model_configs: string[];
  num_tasks: number;
  max_concurrent: number;
  task_model: string;
  max_turns: number;
  enable_llm_judge: boolean;
  llm_judge_model: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

interface AutoProgress {
  isRunning: boolean;
  currentPhase: string;
  progress: number;
  status: string;
  logs: string[];
  job_id?: string;
}

interface SavedConfig {
  name: string;
  path: string;
  modified: number;
}

const AutoWorkflow: React.FC = () => {
  const [config, setConfig] = useState<AutoConfig>({
    workspace: '',
    servers: [],
    model_configs: [],
    num_tasks: 10,
    max_concurrent: 3,
    task_model: 'gpt-4.1-2025-04-14',
    max_turns: 30,
    enable_llm_judge: false,
    llm_judge_model: 'gpt-4o',
  });

  const [progress, setProgress] = useState<AutoProgress>({
    isRunning: false,
    currentPhase: '',
    progress: 0,
    status: '',
    logs: [],
  });

  const [validation, setValidation] = useState<ValidationResult>({
    valid: true,
    errors: [],
    warnings: [],
  });

  const [availableServers, setAvailableServers] = useState<string[]>([]);
  const [availableModelConfigs, setAvailableModelConfigs] = useState<string[]>(
    []
  );
  const [savedConfigs, setSavedConfigs] = useState<SavedConfig[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showServerDialog, setShowServerDialog] = useState(false);
  const [showModelDialog, setShowModelDialog] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [configName, setConfigName] = useState('');

  // Load initial data
  useEffect(() => {
    loadAvailableServers();
    loadAvailableModelConfigs();
    loadSavedConfigs();
  }, []);

  const loadAvailableServers = async () => {
    try {
      const response = await fetch('/api/servers');
      const data = await response.json();
      setAvailableServers(
        data.servers?.map((server: any) => server.path) || []
      );
    } catch (error) {
      console.error('Error loading servers:', error);
    }
  };

  const loadAvailableModelConfigs = async () => {
    try {
      const response = await fetch('/api/model-configs');
      const data = await response.json();
      setAvailableModelConfigs(
        data.configs?.map((config: any) => config.path) || []
      );
    } catch (error) {
      console.error('Error loading model configs:', error);
    }
  };

  const loadSavedConfigs = async () => {
    try {
      const response = await fetch('/api/auto/config/list');
      const data = await response.json();
      setSavedConfigs(data.configs || []);
    } catch (error) {
      console.error('Error loading saved configs:', error);
    }
  };

  const validateConfig = async () => {
    try {
      const response = await fetch('/api/auto/config/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      const data = await response.json();
      setValidation(data);
      return data.valid;
    } catch (error) {
      console.error('Error validating config:', error);
      setValidation({
        valid: false,
        errors: ['Failed to validate configuration'],
        warnings: [],
      });
      return false;
    }
  };

  const saveConfig = async () => {
    try {
      const response = await fetch('/api/auto/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...config,
          config_name: configName,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setShowSaveDialog(false);
        setConfigName('');
        loadSavedConfigs();
        alert('Configuration saved successfully!');
      } else {
        alert('Failed to save configuration');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    }
  };

  const loadConfig = async (name: string) => {
    try {
      const response = await fetch(`/api/auto/config/load/${name}`);
      const data = await response.json();
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const runAutoWorkflow = async () => {
    const isValid = await validateConfig();
    if (!isValid) {
      return;
    }

    setProgress({
      isRunning: true,
      currentPhase: 'Initializing',
      progress: 0,
      status: 'Starting auto workflow...',
      logs: ['Initializing auto workflow...'],
    });

    try {
      const response = await fetch('/api/auto/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (data.success) {
        setProgress(prev => ({
          ...prev,
          job_id: data.job_id,
          status: 'Workflow started successfully',
          logs: [...prev.logs, 'Workflow started successfully'],
        }));

        // Start polling for progress
        pollJobProgress(data.job_id);
      } else {
        setProgress(prev => ({
          ...prev,
          isRunning: false,
          status: `Error: ${data.error}`,
          logs: [...prev.logs, `Error: ${data.error}`],
        }));
      }
    } catch (error) {
      setProgress(prev => ({
        ...prev,
        isRunning: false,
        status: `Error: ${error}`,
        logs: [...prev.logs, `Error: ${error}`],
      }));
    }
  };

  const pollJobProgress = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/job/${jobId}`);
        const data = await response.json();

        if (data.progress?.status === 'completed') {
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            progress: 100,
            status: 'Workflow completed successfully',
            logs: [...prev.logs, 'Workflow completed successfully'],
          }));
          clearInterval(interval);
        } else if (data.progress?.status === 'failed') {
          setProgress(prev => ({
            ...prev,
            isRunning: false,
            status: `Workflow failed: ${data.progress?.error || 'Unknown error'}`,
            logs: [
              ...prev.logs,
              `Workflow failed: ${data.progress?.error || 'Unknown error'}`,
            ],
          }));
          clearInterval(interval);
        } else {
          setProgress(prev => ({
            ...prev,
            progress: data.progress?.progress || 0,
            status: data.progress?.status || 'Running...',
            logs: data.logs || prev.logs,
          }));
        }
      } catch (error) {
        console.error('Error polling job progress:', error);
        clearInterval(interval);
      }
    }, 2000);
  };

  const stopWorkflow = async () => {
    // Note: Backend doesn't currently support stopping jobs
    // For now, just stop the polling and mark as stopped locally
    setProgress(prev => ({
      ...prev,
      isRunning: false,
      status: 'Workflow stopped (polling stopped)',
      logs: [...prev.logs, 'Workflow polling stopped by user'],
    }));
  };

  const renderConfigTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Settings sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Basic Configuration
            </Typography>
            <TextField
              fullWidth
              label="Workspace Name"
              value={config.workspace}
              onChange={e =>
                setConfig({ ...config, workspace: e.target.value })
              }
              margin="normal"
              helperText="Name for this evaluation workspace"
            />
            <TextField
              fullWidth
              type="number"
              label="Number of Tasks"
              value={config.num_tasks}
              onChange={e =>
                setConfig({ ...config, num_tasks: parseInt(e.target.value) })
              }
              margin="normal"
              helperText="Number of tasks to generate"
            />
            <TextField
              fullWidth
              type="number"
              label="Max Concurrent"
              value={config.max_concurrent}
              onChange={e =>
                setConfig({
                  ...config,
                  max_concurrent: parseInt(e.target.value),
                })
              }
              margin="normal"
              helperText="Maximum concurrent evaluations"
            />
            <TextField
              fullWidth
              type="number"
              label="Max Turns"
              value={config.max_turns}
              onChange={e =>
                setConfig({ ...config, max_turns: parseInt(e.target.value) })
              }
              margin="normal"
              helperText="Maximum turns per task"
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <AutoAwesome sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Model Configuration
            </Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel>Task Generation Model</InputLabel>
              <Select
                value={config.task_model}
                onChange={e =>
                  setConfig({ ...config, task_model: e.target.value })
                }
              >
                <MenuItem value="gpt-4.1-2025-04-14">
                  GPT-4.1 (2025-04-14)
                </MenuItem>
                <MenuItem value="gpt-4o">GPT-4o</MenuItem>
                <MenuItem value="gpt-4o-mini">GPT-4o Mini</MenuItem>
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={config.enable_llm_judge}
                  onChange={e =>
                    setConfig({ ...config, enable_llm_judge: e.target.checked })
                  }
                />
              }
              label="Enable LLM Judge"
            />
            {config.enable_llm_judge && (
              <FormControl fullWidth margin="normal">
                <InputLabel>LLM Judge Model</InputLabel>
                <Select
                  value={config.llm_judge_model}
                  onChange={e =>
                    setConfig({ ...config, llm_judge_model: e.target.value })
                  }
                >
                  <MenuItem value="gpt-4o">GPT-4o</MenuItem>
                  <MenuItem value="gpt-4.1-2025-04-14">
                    GPT-4.1 (2025-04-14)
                  </MenuItem>
                  <MenuItem value="gpt-4o-mini">GPT-4o Mini</MenuItem>
                </Select>
              </FormControl>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Folder sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Servers & Models
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <Typography variant="subtitle1">Selected Servers</Typography>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => setShowServerDialog(true)}
                    size="small"
                  >
                    Add Server
                  </Button>
                </Box>
                <List dense>
                  {config.servers.map((server, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={server} />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() =>
                            setConfig({
                              ...config,
                              servers: config.servers.filter(
                                (_, i) => i !== index
                              ),
                            })
                          }
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <Typography variant="subtitle1">
                    Model Configurations
                  </Typography>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => setShowModelDialog(true)}
                    size="small"
                  >
                    Add Model
                  </Button>
                </Box>
                <List dense>
                  {config.model_configs.map((model, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={model} />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() =>
                            setConfig({
                              ...config,
                              model_configs: config.model_configs.filter(
                                (_, i) => i !== index
                              ),
                            })
                          }
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderSavedConfigsTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Saved Configurations
        </Typography>
        <List>
          {savedConfigs.map(savedConfig => (
            <ListItem key={savedConfig.name}>
              <ListItemText
                primary={savedConfig.name}
                secondary={`Modified: ${new Date(savedConfig.modified * 1000).toLocaleString()}`}
              />
              <ListItemSecondaryAction>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => loadConfig(savedConfig.name)}
                >
                  Load
                </Button>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <AutoAwesome sx={{ mr: 2, verticalAlign: 'bottom' }} />
          Auto Workflow
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Complete automated evaluation pipeline for MCP servers
        </Typography>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={(e, newValue) => setSelectedTab(newValue)}
        >
          <Tab label="Configuration" />
          <Tab label="Saved Configs" />
        </Tabs>
      </Box>

      {selectedTab === 0 && renderConfigTab()}
      {selectedTab === 1 && renderSavedConfigsTab()}

      {/* Validation Results */}
      {validation.errors.length > 0 && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="subtitle2">Configuration Errors:</Typography>
          <ul>
            {validation.errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      {validation.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="subtitle2">Warnings:</Typography>
          <ul>
            {validation.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={progress.isRunning ? <Stop /> : <PlayArrow />}
          onClick={progress.isRunning ? stopWorkflow : runAutoWorkflow}
          disabled={
            config.servers.length === 0 || config.model_configs.length === 0
          }
        >
          {progress.isRunning ? 'Stop Workflow' : 'Run Auto Workflow'}
        </Button>
        <Button
          variant="outlined"
          startIcon={<Save />}
          onClick={() => setShowSaveDialog(true)}
        >
          Save Configuration
        </Button>
        <Button variant="outlined" onClick={validateConfig}>
          Validate Configuration
        </Button>
      </Box>

      {/* Progress Display */}
      {progress.isRunning && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Workflow Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={progress.progress}
              sx={{ mb: 2 }}
            />
            <Typography variant="body2" color="text.secondary">
              {progress.status}
            </Typography>
            <Box sx={{ mt: 2, maxHeight: 200, overflow: 'auto' }}>
              {progress.logs.map((log, index) => (
                <Typography key={index} variant="body2" component="div">
                  {log}
                </Typography>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Server Selection Dialog */}
      <Dialog
        open={showServerDialog}
        onClose={() => setShowServerDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Select Servers</DialogTitle>
        <DialogContent>
          <FormGroup>
            {availableServers.map(server => (
              <FormControlLabel
                key={server}
                control={
                  <Checkbox
                    checked={config.servers.includes(server)}
                    onChange={e => {
                      if (e.target.checked) {
                        setConfig({
                          ...config,
                          servers: [...config.servers, server],
                        });
                      } else {
                        setConfig({
                          ...config,
                          servers: config.servers.filter(s => s !== server),
                        });
                      }
                    }}
                  />
                }
                label={server}
              />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowServerDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Model Config Selection Dialog */}
      <Dialog
        open={showModelDialog}
        onClose={() => setShowModelDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Select Model Configurations</DialogTitle>
        <DialogContent>
          <FormGroup>
            {availableModelConfigs.map(model => (
              <FormControlLabel
                key={model}
                control={
                  <Checkbox
                    checked={config.model_configs.includes(model)}
                    onChange={e => {
                      if (e.target.checked) {
                        setConfig({
                          ...config,
                          model_configs: [...config.model_configs, model],
                        });
                      } else {
                        setConfig({
                          ...config,
                          model_configs: config.model_configs.filter(
                            m => m !== model
                          ),
                        });
                      }
                    }}
                  />
                }
                label={model}
              />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowModelDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Save Configuration Dialog */}
      <Dialog
        open={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Configuration Name"
            value={configName}
            onChange={e => setConfigName(e.target.value)}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>Cancel</Button>
          <Button
            onClick={saveConfig}
            variant="contained"
            disabled={!configName}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AutoWorkflow;
