import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Divider,
  IconButton,
  Tooltip,
  Grid,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Build as ToolIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  NavigateBefore,
  NavigateNext,
  Replay as ReplayIcon,
} from '@mui/icons-material';

interface ToolCallDetail {
  tool_name: string;
  tool_parameters: Record<string, any>;
}

interface Message {
  role: string;
  content: string | null;
  tool_calls?: any[];
  tool_call_id?: string;
}

interface TaskResult {
  task_id: string;
  success: boolean;
  tool_calls: ToolCallDetail[];
  final_response: string;
  conversation: Message[];
  task?: {
    name?: string;
    description?: string;
    goal?: string;
  };
  error?: string;
}

const ConversationReplay: React.FC = () => {
  const [resultsFile, setResultsFile] = useState('');
  const [files, setFiles] = useState<string[]>([]);
  const [results, setResults] = useState<TaskResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedTurn, setExpandedTurn] = useState<number | false>(0);

  // Fetch available files
  useEffect(() => {
    fetch('/api/files?directory=workspace')
      .then(res => res.json())
      .then(data => {
        const jsonlFiles = (data.files || [])
          .filter((f: any) => f.name?.endsWith('.jsonl') || f.name?.endsWith('.json'))
          .map((f: any) => f.name);
        setFiles(jsonlFiles);
      })
      .catch(() => {});
  }, []);

  const loadResults = async () => {
    if (!resultsFile) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/file-content/${encodeURIComponent(resultsFile)}`);
      if (!res.ok) throw new Error('Failed to load file');
      const text = await res.text();

      // Parse JSONL
      const lines = text.trim().split('\n').filter(Boolean);
      const parsed = lines.map(line => JSON.parse(line));
      const withConversation = parsed.filter(
        (r: any) => r.conversation && r.conversation.length > 0
      );

      if (withConversation.length === 0) {
        setError('No conversations found in this file.');
        setResults([]);
      } else {
        setResults(withConversation);
        setSelectedIndex(0);
        setExpandedTurn(0);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to parse file');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const current = results[selectedIndex] || null;

  // Group messages into turns (user message + assistant responses + tool results)
  const getTurns = (conversation: Message[]) => {
    const turns: { userMessage?: Message; responses: Message[] }[] = [];
    let currentTurn: { userMessage?: Message; responses: Message[] } | null = null;

    for (const msg of conversation) {
      if (msg.role === 'system') continue;
      if (msg.role === 'user') {
        if (currentTurn) turns.push(currentTurn);
        currentTurn = { userMessage: msg, responses: [] };
      } else {
        if (!currentTurn) currentTurn = { responses: [] };
        currentTurn.responses.push(msg);
      }
    }
    if (currentTurn) turns.push(currentTurn);
    return turns;
  };

  const renderMessage = (msg: Message, index: number) => {
    const isUser = msg.role === 'user';
    const isAssistant = msg.role === 'assistant';
    const isTool = msg.role === 'tool';

    const bgColor = isUser ? '#e3f2fd' : isTool ? '#fff3e0' : '#f5f5f5';
    const icon = isUser ? <PersonIcon /> : isTool ? <ToolIcon /> : <BotIcon />;
    const label = isUser ? 'User' : isTool ? 'Tool Result' : 'Assistant';

    return (
      <Paper
        key={index}
        elevation={0}
        sx={{
          p: 2,
          mb: 1,
          backgroundColor: bgColor,
          borderRadius: 2,
          borderLeft: `4px solid ${isUser ? '#1976d2' : isTool ? '#ff9800' : '#4caf50'}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
          {icon}
          <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 600 }}>
            {label}
          </Typography>
          {msg.tool_call_id && (
            <Chip label={`call: ${msg.tool_call_id.slice(0, 12)}...`} size="small" sx={{ ml: 1 }} />
          )}
        </Box>

        {msg.content && (
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1 }}>
            {msg.content}
          </Typography>
        )}

        {msg.tool_calls && msg.tool_calls.length > 0 && (
          <Box sx={{ mt: 1 }}>
            {msg.tool_calls.map((tc: any, i: number) => (
              <Paper key={i} elevation={1} sx={{ p: 1.5, mt: 1, backgroundColor: '#e8f5e9', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ToolIcon fontSize="small" sx={{ color: '#2e7d32', mr: 1 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2e7d32' }}>
                    {tc.function?.name || tc.tool_name || 'unknown'}
                  </Typography>
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    mt: 0.5,
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    backgroundColor: 'rgba(0,0,0,0.04)',
                    p: 1,
                    borderRadius: 1,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  {typeof tc.function?.arguments === 'string'
                    ? tc.function.arguments
                    : JSON.stringify(tc.function?.arguments || tc.tool_parameters || {}, null, 2)}
                </Typography>
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Conversation Replay
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Step through evaluation conversations turn-by-turn to debug tool calls and responses.
      </Typography>

      {/* File selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={8}>
              <FormControl fullWidth size="small">
                <InputLabel>Results File</InputLabel>
                <Select
                  value={resultsFile}
                  label="Results File"
                  onChange={e => setResultsFile(e.target.value as string)}
                >
                  {files.map(f => (
                    <MenuItem key={f} value={f}>{f}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={2}>
              <TextField
                fullWidth
                size="small"
                label="Or paste path"
                value={resultsFile}
                onChange={e => setResultsFile(e.target.value)}
              />
            </Grid>
            <Grid item xs={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadResults}
                disabled={!resultsFile || loading}
                startIcon={loading ? <CircularProgress size={16} /> : <ReplayIcon />}
              >
                Load
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {results.length > 0 && current && (
        <>
          {/* Task navigation */}
          <Card sx={{ mb: 2 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Tooltip title="Previous task">
                    <span>
                      <IconButton
                        size="small"
                        disabled={selectedIndex === 0}
                        onClick={() => { setSelectedIndex(i => i - 1); setExpandedTurn(0); }}
                      >
                        <NavigateBefore />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, minWidth: 120, textAlign: 'center' }}>
                    Task {selectedIndex + 1} / {results.length}
                  </Typography>
                  <Tooltip title="Next task">
                    <span>
                      <IconButton
                        size="small"
                        disabled={selectedIndex === results.length - 1}
                        onClick={() => { setSelectedIndex(i => i + 1); setExpandedTurn(0); }}
                      >
                        <NavigateNext />
                      </IconButton>
                    </span>
                  </Tooltip>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    icon={current.success ? <SuccessIcon /> : <ErrorIcon />}
                    label={current.success ? 'Passed' : 'Failed'}
                    color={current.success ? 'success' : 'error'}
                    size="small"
                  />
                  <Chip label={`${current.tool_calls?.length || 0} tool calls`} size="small" variant="outlined" />
                  <Chip label={`${current.conversation?.length || 0} messages`} size="small" variant="outlined" />
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Task info */}
          {current.task && (
            <Card sx={{ mb: 2 }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="subtitle2" color="text.secondary">
                  {current.task_id || current.task?.name || 'Unnamed Task'}
                </Typography>
                {current.task.goal && (
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    <strong>Goal:</strong> {current.task.goal}
                  </Typography>
                )}
                {current.error && (
                  <Alert severity="error" sx={{ mt: 1 }}>{current.error}</Alert>
                )}
              </CardContent>
            </Card>
          )}

          {/* Conversation turns */}
          {getTurns(current.conversation).map((turn, turnIdx) => (
            <Accordion
              key={turnIdx}
              expanded={expandedTurn === turnIdx}
              onChange={(_, isExpanded) => setExpandedTurn(isExpanded ? turnIdx : false)}
              sx={{ mb: 1 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip label={`Turn ${turnIdx + 1}`} size="small" color="primary" variant="outlined" />
                  {turn.userMessage && (
                    <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 500 }}>
                      {turn.userMessage.content?.slice(0, 80)}
                      {(turn.userMessage.content?.length || 0) > 80 ? '...' : ''}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary">
                    ({turn.responses.length} response{turn.responses.length !== 1 ? 's' : ''})
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                {turn.userMessage && renderMessage(turn.userMessage, 0)}
                <Divider sx={{ my: 1 }} />
                {turn.responses.map((msg, i) => renderMessage(msg, i + 1))}
              </AccordionDetails>
            </Accordion>
          ))}

          {/* Final response */}
          {current.final_response && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Final Response
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {current.final_response}
                </Typography>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  );
};

export default ConversationReplay;
