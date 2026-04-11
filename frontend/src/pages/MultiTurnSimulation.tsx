import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Alert,
  Chip,
  Divider,
  Tabs,
  Tab,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  ExpandMore as ExpandMoreIcon,
  RecordVoiceOver as SimulateIcon,
  TheaterComedy as ScenarioIcon,
  Grading as EvalIcon,
} from '@mui/icons-material';
import { ServerConfig } from '../components/types';
import UnifiedMCPServerConfiguration from '../components/UnifiedMCPServerConfiguration';

interface ModelConfig {
  model: string;
  temperature: number;
  max_tokens: number;
  api_key: string;
  base_url: string;
}

interface JobProgress {
  isRunning: boolean;
  status: string;
  progress: number;
  logs: string[];
  jobId?: string;
}

const defaultModelConfig = (): ModelConfig => ({
  model: 'gpt-4o-mini',
  temperature: 0.7,
  max_tokens: 2000,
  api_key: 'dummy',
  base_url: 'http://localhost:8008/v1',
});

const defaultAgentConfig = (): ModelConfig => ({
  model: 'gpt-4o-mini',
  temperature: 0.1,
  max_tokens: 4000,
  api_key: 'dummy',
  base_url: 'http://localhost:8008/v1',
});

const MultiTurnSimulation: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  // Shared state
  const [servers, setServers] = useState<(ServerConfig & { id?: string; name?: string; type?: 'local' | 'npm' | 'http' })[]>([{ path: '', args: [], env: {} }]);
  const [jobProgress, setJobProgress] = useState<JobProgress>({
    isRunning: false, status: '', progress: 0, logs: [],
  });
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Simulate tab state
  const [simulatorConfig, setSimulatorConfig] = useState<ModelConfig>(defaultModelConfig());
  const [agentConfig, setAgentConfig] = useState<ModelConfig>(defaultAgentConfig());
  const [tasksFile, setTasksFile] = useState('');
  const [scenariosFile, setScenariosFile] = useState('');
  const [simOutput, setSimOutput] = useState('multiturn_results.jsonl');
  const [numScenarios, setNumScenarios] = useState(5);
  const [maxTurns, setMaxTurns] = useState(5);
  const [maxAgentSteps, setMaxAgentSteps] = useState(10);
  const [scenarioType, setScenarioType] = useState('standard');

  // Generate scenarios tab state
  const [genModelConfig, setGenModelConfig] = useState<ModelConfig>(defaultModelConfig());
  const [genTasksFile, setGenTasksFile] = useState('');
  const [genOutput, setGenOutput] = useState('scenarios.jsonl');
  const [genNumScenarios, setGenNumScenarios] = useState(10);
  const [genMaxTurns, setGenMaxTurns] = useState(5);
  const [genScenarioType, setGenScenarioType] = useState('standard');

  // Evaluate multiturn tab state
  const [evalInput, setEvalInput] = useState('multiturn_results.jsonl');
  const [evalOutput, setEvalOutput] = useState('multiturn_evaluation.jsonl');
  const [evalModelConfig, setEvalModelConfig] = useState<ModelConfig>(defaultModelConfig());
  const [evalNumSamples, setEvalNumSamples] = useState(-1);
  const [evalResume, setEvalResume] = useState(false);

  // Available files
  const [files, setFiles] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/files')
      .then(res => res.json())
      .then(data => {
        const jsonlFiles = (data.files || [])
          .filter((f: any) => f.name?.endsWith('.jsonl'))
          .map((f: any) => f.name);
        setFiles(jsonlFiles);
      })
      .catch(() => {});
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const pollJob = (jobId: string) => {
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/job/${jobId}`);
        const data = await res.json();
        const status = data.progress?.status || 'unknown';
        const progress = data.progress?.progress || 0;
        const logs = data.logs || [];

        setJobProgress({
          isRunning: status === 'running',
          status,
          progress,
          logs,
          jobId,
        });

        if (status === 'completed' || status === 'failed' || status === 'cancelled') {
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch {
        // ignore
      }
    }, 2000);
  };

  const buildServerPayload = () => {
    return servers
      .filter(s => s.path)
      .map(s => ({
        path: s.path,
        args: s.args || [],
        env: s.env || {},
      }));
  };

  const handleRunSimulation = async () => {
    setJobProgress({ isRunning: true, status: 'starting', progress: 0, logs: [] });
    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          servers: buildServerPayload(),
          simulator_model: simulatorConfig,
          agent_model: agentConfig,
          tasks_file: tasksFile,
          scenarios_file: scenariosFile,
          output: simOutput,
          num_scenarios: numScenarios,
          max_turns: maxTurns,
          max_agent_steps: maxAgentSteps,
          scenario_type: scenarioType,
        }),
      });
      const data = await res.json();
      if (data.job_id) {
        setJobProgress(p => ({ ...p, jobId: data.job_id }));
        pollJob(data.job_id);
      } else {
        setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [data.error || 'Unknown error'] });
      }
    } catch (e: any) {
      setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [e.message] });
    }
  };

  const handleGenerateScenarios = async () => {
    setJobProgress({ isRunning: true, status: 'starting', progress: 0, logs: [] });
    try {
      const res = await fetch('/api/generate-scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          servers: buildServerPayload(),
          tasks_file: genTasksFile,
          model_config: genModelConfig,
          output: genOutput,
          num_scenarios: genNumScenarios,
          max_turns: genMaxTurns,
          scenario_type: genScenarioType,
        }),
      });
      const data = await res.json();
      if (data.job_id) {
        setJobProgress(p => ({ ...p, jobId: data.job_id }));
        pollJob(data.job_id);
      } else {
        setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [data.error || 'Unknown error'] });
      }
    } catch (e: any) {
      setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [e.message] });
    }
  };

  const handleEvaluateMultiturn = async () => {
    setJobProgress({ isRunning: true, status: 'starting', progress: 0, logs: [] });
    try {
      const res = await fetch('/api/evaluate-multiturn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: evalInput,
          output: evalOutput,
          model_config: evalModelConfig,
          model: evalModelConfig.model,
          num_samples: evalNumSamples,
          resume: evalResume,
        }),
      });
      const data = await res.json();
      if (data.job_id) {
        setJobProgress(p => ({ ...p, jobId: data.job_id }));
        pollJob(data.job_id);
      } else {
        setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [data.error || 'Unknown error'] });
      }
    } catch (e: any) {
      setJobProgress({ isRunning: false, status: 'failed', progress: 0, logs: [e.message] });
    }
  };

  const handleStopJob = async () => {
    if (jobProgress.jobId) {
      await fetch(`/api/job/${jobProgress.jobId}/kill`, { method: 'POST' });
      if (pollingRef.current) clearInterval(pollingRef.current);
      setJobProgress(p => ({ ...p, isRunning: false, status: 'cancelled' }));
    }
  };

  const renderModelConfigFields = (
    config: ModelConfig,
    setConfig: React.Dispatch<React.SetStateAction<ModelConfig>>,
    label: string,
  ) => (
    <Accordion defaultExpanded={false}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle2">{label}: {config.model}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField fullWidth size="small" label="Model" value={config.model}
              onChange={e => setConfig(c => ({ ...c, model: e.target.value }))} />
          </Grid>
          <Grid item xs={3}>
            <TextField fullWidth size="small" label="Temperature" type="number"
              inputProps={{ step: 0.1, min: 0, max: 2 }}
              value={config.temperature}
              onChange={e => setConfig(c => ({ ...c, temperature: parseFloat(e.target.value) || 0 }))} />
          </Grid>
          <Grid item xs={3}>
            <TextField fullWidth size="small" label="Max Tokens" type="number"
              value={config.max_tokens}
              onChange={e => setConfig(c => ({ ...c, max_tokens: parseInt(e.target.value) || 2000 }))} />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth size="small" label="Base URL" value={config.base_url}
              onChange={e => setConfig(c => ({ ...c, base_url: e.target.value }))} />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth size="small" label="API Key" value={config.api_key}
              onChange={e => setConfig(c => ({ ...c, api_key: e.target.value }))} />
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );

  const renderProgressPanel = () => {
    if (!jobProgress.status) return null;
    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Job Progress</Typography>
              <Chip
                label={jobProgress.status}
                size="small"
                color={
                  jobProgress.status === 'completed' ? 'success' :
                  jobProgress.status === 'failed' ? 'error' :
                  jobProgress.status === 'running' ? 'primary' : 'default'
                }
              />
            </Box>
            {jobProgress.isRunning && (
              <Button size="small" color="error" startIcon={<Stop />} onClick={handleStopJob}>
                Stop
              </Button>
            )}
          </Box>
          {jobProgress.isRunning && (
            <LinearProgress variant="determinate" value={jobProgress.progress} sx={{ mb: 2 }} />
          )}
          {jobProgress.logs.length > 0 && (
            <Paper
              elevation={0}
              sx={{
                maxHeight: 300,
                overflow: 'auto',
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.8rem',
              }}
            >
              {jobProgress.logs.slice(-50).map((log, i) => (
                <Box key={i} sx={{ py: 0.25 }}>{log}</Box>
              ))}
            </Paper>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Multi-Turn Simulation
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Generate scenarios, run user simulations, and evaluate multi-turn conversations.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab icon={<SimulateIcon />} label="Run Simulation" iconPosition="start" />
          <Tab icon={<ScenarioIcon />} label="Generate Scenarios" iconPosition="start" />
          <Tab icon={<EvalIcon />} label="Evaluate Conversations" iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab 0: Run Simulation */}
      {activeTab === 0 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>MCP Servers</Typography>
              <UnifiedMCPServerConfiguration servers={servers} onServersChange={setServers} />
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Model Configurations</Typography>
              {renderModelConfigFields(simulatorConfig, setSimulatorConfig, 'Simulator LLM (plays the user)')}
              <Box sx={{ mt: 1 }} />
              {renderModelConfigFields(agentConfig, setAgentConfig, 'Agent LLM (under test)')}
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Simulation Settings</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField fullWidth size="small" label="Tasks File (optional)"
                    value={tasksFile} onChange={e => setTasksFile(e.target.value)}
                    helperText="JSONL with tasks to convert to scenarios" />
                </Grid>
                <Grid item xs={6}>
                  <TextField fullWidth size="small" label="Scenarios File (optional)"
                    value={scenariosFile} onChange={e => setScenariosFile(e.target.value)}
                    helperText="Pre-generated scenarios JSONL" />
                </Grid>
                <Grid item xs={4}>
                  <TextField fullWidth size="small" label="Output File"
                    value={simOutput} onChange={e => setSimOutput(e.target.value)} />
                </Grid>
                <Grid item xs={2}>
                  <TextField fullWidth size="small" label="# Scenarios" type="number"
                    value={numScenarios} onChange={e => setNumScenarios(parseInt(e.target.value) || -1)} />
                </Grid>
                <Grid item xs={2}>
                  <TextField fullWidth size="small" label="Max Turns" type="number"
                    value={maxTurns} onChange={e => setMaxTurns(parseInt(e.target.value) || 5)} />
                </Grid>
                <Grid item xs={2}>
                  <TextField fullWidth size="small" label="Max Agent Steps" type="number"
                    value={maxAgentSteps} onChange={e => setMaxAgentSteps(parseInt(e.target.value) || 10)} />
                </Grid>
                <Grid item xs={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Type</InputLabel>
                    <Select value={scenarioType} label="Type" onChange={e => setScenarioType(e.target.value)}>
                      <MenuItem value="standard">Standard</MenuItem>
                      <MenuItem value="missing_params">Missing Params</MenuItem>
                      <MenuItem value="missing_functions">Missing Functions</MenuItem>
                      <MenuItem value="composite">Composite</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Button
            variant="contained"
            size="large"
            startIcon={jobProgress.isRunning ? <Stop /> : <PlayArrow />}
            onClick={jobProgress.isRunning ? handleStopJob : handleRunSimulation}
            color={jobProgress.isRunning ? 'error' : 'primary'}
            disabled={servers.every(s => !s.path)}
          >
            {jobProgress.isRunning ? 'Stop Simulation' : 'Start Simulation'}
          </Button>
        </Box>
      )}

      {/* Tab 1: Generate Scenarios */}
      {activeTab === 1 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>MCP Servers (optional for scratch generation)</Typography>
              <UnifiedMCPServerConfiguration servers={servers} onServersChange={setServers} />
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Generation Settings</Typography>
              {renderModelConfigFields(genModelConfig, setGenModelConfig, 'Generation LLM')}
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={4}>
                  <TextField fullWidth size="small" label="Tasks File (optional)"
                    value={genTasksFile} onChange={e => setGenTasksFile(e.target.value)}
                    helperText="Convert existing tasks to scenarios" />
                </Grid>
                <Grid item xs={3}>
                  <TextField fullWidth size="small" label="Output File"
                    value={genOutput} onChange={e => setGenOutput(e.target.value)} />
                </Grid>
                <Grid item xs={2}>
                  <TextField fullWidth size="small" label="# Scenarios" type="number"
                    value={genNumScenarios} onChange={e => setGenNumScenarios(parseInt(e.target.value) || -1)} />
                </Grid>
                <Grid item xs={1}>
                  <TextField fullWidth size="small" label="Turns" type="number"
                    value={genMaxTurns} onChange={e => setGenMaxTurns(parseInt(e.target.value) || 5)} />
                </Grid>
                <Grid item xs={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Type</InputLabel>
                    <Select value={genScenarioType} label="Type" onChange={e => setGenScenarioType(e.target.value)}>
                      <MenuItem value="standard">Standard</MenuItem>
                      <MenuItem value="missing_params">Missing Params</MenuItem>
                      <MenuItem value="missing_functions">Missing Functions</MenuItem>
                      <MenuItem value="composite">Composite</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Button
            variant="contained"
            size="large"
            startIcon={jobProgress.isRunning ? <Stop /> : <ScenarioIcon />}
            onClick={jobProgress.isRunning ? handleStopJob : handleGenerateScenarios}
            color={jobProgress.isRunning ? 'error' : 'primary'}
          >
            {jobProgress.isRunning ? 'Stop' : 'Generate Scenarios'}
          </Button>
        </Box>
      )}

      {/* Tab 2: Evaluate Multi-Turn */}
      {activeTab === 2 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Evaluation Settings</Typography>
              {renderModelConfigFields(evalModelConfig, setEvalModelConfig, 'Judge LLM')}
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={4}>
                  <TextField fullWidth size="small" label="Input File (required)"
                    value={evalInput} onChange={e => setEvalInput(e.target.value)}
                    helperText="JSONL with multi-turn conversation results" />
                </Grid>
                <Grid item xs={4}>
                  <TextField fullWidth size="small" label="Output File"
                    value={evalOutput} onChange={e => setEvalOutput(e.target.value)} />
                </Grid>
                <Grid item xs={2}>
                  <TextField fullWidth size="small" label="# Samples" type="number"
                    value={evalNumSamples}
                    onChange={e => setEvalNumSamples(parseInt(e.target.value) || -1)}
                    helperText="-1 = all" />
                </Grid>
                <Grid item xs={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Resume</InputLabel>
                    <Select value={evalResume ? 'yes' : 'no'} label="Resume"
                      onChange={e => setEvalResume(e.target.value === 'yes')}>
                      <MenuItem value="no">No</MenuItem>
                      <MenuItem value="yes">Yes</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Button
            variant="contained"
            size="large"
            startIcon={jobProgress.isRunning ? <Stop /> : <EvalIcon />}
            onClick={jobProgress.isRunning ? handleStopJob : handleEvaluateMultiturn}
            color={jobProgress.isRunning ? 'error' : 'primary'}
            disabled={!evalInput}
          >
            {jobProgress.isRunning ? 'Stop' : 'Evaluate Conversations'}
          </Button>
        </Box>
      )}

      {renderProgressPanel()}
    </Box>
  );
};

export default MultiTurnSimulation;
