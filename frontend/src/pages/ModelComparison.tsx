import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  ListItemText,
  OutlinedInput,
} from '@mui/material';
import {
  CompareArrows as CompareIcon,
  Leaderboard as LeaderboardIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';

interface RunSummary {
  id: string;
  model_name: string;
  created_at: string;
  status: string;
  num_tasks: number;
  success_count: number;
  fail_count: number;
  total_tokens: number;
  total_cost: number;
}

interface ComparisonReport {
  labels: string[];
  common_tasks: number;
  confidence_level: number;
  runs: {
    label: string;
    success_rate: number;
    ci_lower: number;
    ci_upper: number;
    n_tasks: number;
    n_pass: number;
    n_fail: number;
  }[];
  pairwise: {
    a: string;
    b: string;
    delta_success_rate: number;
    mcnemar?: {
      p_value: number;
      significant: boolean;
      b_wins_exclusive: number;
      c_wins_exclusive: number;
    };
  }[];
}

interface LeaderboardEntry {
  rank: number;
  model_name: string;
  runs: number;
  total_tasks: number;
  total_pass: number;
  total_fail: number;
  success_rate: number;
  total_tokens: number;
  total_cost: number;
}

const COLORS = ['#1976d2', '#9c27b0', '#2e7d32', '#ed6c02', '#d32f2f', '#0288d1'];

const ModelComparison: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonReport | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'compare' | 'leaderboard'>('leaderboard');

  // Fetch runs from v1 API
  useEffect(() => {
    fetch('/api/v1/runs?limit=100')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setRuns(data);
      })
      .catch(() => {});

    fetch('/api/v1/leaderboard')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setLeaderboard(data);
      })
      .catch(() => {});
  }, []);

  const handleCompare = async () => {
    if (selectedRunIds.length < 2) {
      setError('Select at least 2 runs to compare');
      return;
    }
    setLoading(true);
    setError('');
    try {
      // For now, compare via file paths if available, or via the API
      const res = await fetch('/api/v1/runs/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_ids: selectedRunIds,
          confidence: 0.95,
        }),
      });
      if (!res.ok) throw new Error('Comparison failed');
      const data = await res.json();
      setComparison(data);
    } catch (e: any) {
      setError(e.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data from runs
  const selectedRuns = runs.filter(r => selectedRunIds.includes(r.id));

  const barChartData = selectedRuns.map(r => ({
    name: r.model_name,
    'Success Rate': r.num_tasks > 0 ? ((r.success_count / r.num_tasks) * 100) : 0,
    'Tasks': r.num_tasks,
  }));

  const radarData = [
    { metric: 'Success Rate' },
    { metric: 'Task Count' },
    { metric: 'Efficiency' },
  ].map(d => {
    const result: any = { ...d };
    selectedRuns.forEach(r => {
      const rate = r.num_tasks > 0 ? (r.success_count / r.num_tasks) : 0;
      if (d.metric === 'Success Rate') result[r.model_name] = rate * 100;
      else if (d.metric === 'Task Count') result[r.model_name] = Math.min(r.num_tasks, 100);
      else if (d.metric === 'Efficiency') result[r.model_name] = r.total_tokens > 0
        ? Math.min((r.success_count / (r.total_tokens / 1000)) * 100, 100)
        : 0;
    });
    return result;
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Model Comparison
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Compare model performance across evaluation runs with statistical significance testing.
      </Typography>

      {/* Tab toggle */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        <Button
          variant={tab === 'leaderboard' ? 'contained' : 'outlined'}
          startIcon={<LeaderboardIcon />}
          onClick={() => setTab('leaderboard')}
        >
          Leaderboard
        </Button>
        <Button
          variant={tab === 'compare' ? 'contained' : 'outlined'}
          startIcon={<CompareIcon />}
          onClick={() => setTab('compare')}
        >
          Compare Runs
        </Button>
      </Box>

      {tab === 'leaderboard' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Model Leaderboard</Typography>
            {leaderboard.length === 0 ? (
              <Alert severity="info">
                No completed runs yet. Import results with <code>mcp-eval import</code> or run evaluations to populate the leaderboard.
              </Alert>
            ) : (
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Rank</strong></TableCell>
                      <TableCell><strong>Model</strong></TableCell>
                      <TableCell align="right"><strong>Runs</strong></TableCell>
                      <TableCell align="right"><strong>Tasks</strong></TableCell>
                      <TableCell align="right"><strong>Pass</strong></TableCell>
                      <TableCell align="right"><strong>Fail</strong></TableCell>
                      <TableCell align="right"><strong>Success Rate</strong></TableCell>
                      <TableCell align="right"><strong>Tokens</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {leaderboard.map(entry => (
                      <TableRow key={entry.model_name}>
                        <TableCell>
                          {entry.rank <= 3 ? (
                            <Chip label={`#${entry.rank}`} size="small"
                              color={entry.rank === 1 ? 'success' : entry.rank === 2 ? 'primary' : 'default'}
                            />
                          ) : entry.rank}
                        </TableCell>
                        <TableCell><strong>{entry.model_name}</strong></TableCell>
                        <TableCell align="right">{entry.runs}</TableCell>
                        <TableCell align="right">{entry.total_tasks}</TableCell>
                        <TableCell align="right">{entry.total_pass}</TableCell>
                        <TableCell align="right">{entry.total_fail}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${(entry.success_rate * 100).toFixed(1)}%`}
                            size="small"
                            color={entry.success_rate >= 0.8 ? 'success' : entry.success_rate >= 0.6 ? 'warning' : 'error'}
                          />
                        </TableCell>
                        <TableCell align="right">{entry.total_tokens.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'compare' && (
        <>
          {/* Run selection */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={9}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Select Runs to Compare</InputLabel>
                    <Select
                      multiple
                      value={selectedRunIds}
                      onChange={e => setSelectedRunIds(e.target.value as string[])}
                      input={<OutlinedInput label="Select Runs to Compare" />}
                      renderValue={selected =>
                        selected.map(id => {
                          const r = runs.find(run => run.id === id);
                          return r ? r.model_name : id;
                        }).join(', ')
                      }
                    >
                      {runs.map(r => (
                        <MenuItem key={r.id} value={r.id}>
                          <Checkbox checked={selectedRunIds.includes(r.id)} />
                          <ListItemText
                            primary={`${r.model_name} (${r.num_tasks} tasks)`}
                            secondary={`${r.status} - ${r.created_at?.slice(0, 10) || 'N/A'}`}
                          />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={3}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={handleCompare}
                    disabled={selectedRunIds.length < 2 || loading}
                    startIcon={loading ? <CircularProgress size={16} /> : <CompareIcon />}
                  >
                    Compare
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {/* Charts */}
          {selectedRuns.length >= 2 && (
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={7}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Success Rate Comparison</Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={barChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="Success Rate" fill="#1976d2" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={5}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Multi-Metric Radar</Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                        {selectedRuns.map((r, i) => (
                          <Radar
                            key={r.id}
                            name={r.model_name}
                            dataKey={r.model_name}
                            stroke={COLORS[i % COLORS.length]}
                            fill={COLORS[i % COLORS.length]}
                            fillOpacity={0.15}
                          />
                        ))}
                        <Legend />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Comparison results table */}
          {comparison && comparison.runs && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Statistical Comparison ({comparison.common_tasks} common tasks, {(comparison.confidence_level * 100).toFixed(0)}% CI)
                </Typography>
                <TableContainer component={Paper} elevation={0}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Run</strong></TableCell>
                        <TableCell align="right"><strong>Success Rate</strong></TableCell>
                        <TableCell align="right"><strong>CI Lower</strong></TableCell>
                        <TableCell align="right"><strong>CI Upper</strong></TableCell>
                        <TableCell align="right"><strong>Pass</strong></TableCell>
                        <TableCell align="right"><strong>Fail</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {comparison.runs.map(r => (
                        <TableRow key={r.label}>
                          <TableCell><strong>{r.label}</strong></TableCell>
                          <TableCell align="right">{(r.success_rate * 100).toFixed(1)}%</TableCell>
                          <TableCell align="right">{(r.ci_lower * 100).toFixed(1)}%</TableCell>
                          <TableCell align="right">{(r.ci_upper * 100).toFixed(1)}%</TableCell>
                          <TableCell align="right">{r.n_pass}</TableCell>
                          <TableCell align="right">{r.n_fail}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {comparison.pairwise.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom><strong>Pairwise Significance Tests</strong></Typography>
                    {comparison.pairwise.map((p, i) => (
                      <Box key={i} sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2">
                          <strong>{p.a}</strong> vs <strong>{p.b}</strong>:
                          delta = {p.delta_success_rate > 0 ? '+' : ''}{(p.delta_success_rate * 100).toFixed(1)}%
                        </Typography>
                        {p.mcnemar && (
                          <Chip
                            label={p.mcnemar.significant
                              ? `p=${p.mcnemar.p_value.toFixed(4)} (significant)`
                              : `p=${p.mcnemar.p_value.toFixed(4)} (not significant)`
                            }
                            size="small"
                            color={p.mcnemar.significant ? 'error' : 'default'}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  );
};

export default ModelComparison;
