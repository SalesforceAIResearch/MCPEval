import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Paper,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
  Storage as ServerIcon,
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Code as CodeIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { MCPServer, Tool, parseEnvString } from '../components/types';
import MCPChatServerConfiguration from '../components/MCPChatServerConfiguration';

interface LLMConfig {
  model: string;
  apiKey: string;
  baseUrl: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCalls?: any[];
  toolResults?: any[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MCPChatClient: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [availableServers, setAvailableServers] = useState<any[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddServerDialog, setShowAddServerDialog] = useState(false);
  const [showServerSelectionDialog, setShowServerSelectionDialog] =
    useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info' as 'success' | 'error' | 'info' | 'warning',
  });
  const [expandedResults, setExpandedResults] = useState<Set<string>>(
    new Set()
  );

  // Server configuration state
  const [newServer, setNewServer] = useState({
    name: '',
    path: '',
    args: '',
    env: '',
    type: 'local' as 'local' | 'npm',
  });

  // LLM configuration state
  const [llmConfig, setLLMConfig] = useState<LLMConfig>({
    model: 'gpt-4o',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    maxTokens: 2000,
    systemPrompt:
      'You are a helpful AI assistant with access to various tools through MCP servers.',
  });

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load saved configuration on component mount
    loadSavedConfig();

    // Fetch available servers from the workspace
    fetchAvailableServers();

    // Check MCP status on mount
    checkMCPStatus();
  }, []);

  const checkMCPStatus = async () => {
    try {
      const response = await fetch('/api/mcp/status');
      const result = await response.json();

      if (result.connected) {
        setIsConnected(true);
        const systemMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'system',
          content: `Found existing connection with ${result.tool_count} tools available`,
          timestamp: new Date(),
        };
        setChatMessages([systemMessage]);
      }
    } catch (error) {
      console.log('No existing MCP connection found');
    }
  };

  const fetchAvailableServers = async () => {
    try {
      const response = await fetch('/api/servers');
      const result = await response.json();

      if (result.servers) {
        setAvailableServers(result.servers);
      }
    } catch (error) {
      console.error('Error fetching available servers:', error);
    }
  };

  useEffect(() => {
    // Auto-scroll to bottom when new messages are added
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadSavedConfig = () => {
    try {
      const savedServers = localStorage.getItem('mcp-chat-servers');
      const savedLLMConfig = localStorage.getItem('mcp-chat-llm-config');

      if (savedServers) {
        const parsedServers = JSON.parse(savedServers);
        // Ensure all servers have the env property
        const serversWithEnv = parsedServers.map((server: any) => ({
          ...server,
          env: server.env || {},
        }));
        setServers(serversWithEnv);
      }

      if (savedLLMConfig) {
        setLLMConfig(JSON.parse(savedLLMConfig));
      }
    } catch (error) {
      console.error('Error loading saved configuration:', error);
    }
  };

  const saveConfig = (newServers?: MCPServer[], newLLMConfig?: LLMConfig) => {
    try {
      if (newServers) {
        localStorage.setItem('mcp-chat-servers', JSON.stringify(newServers));
      }
      if (newLLMConfig) {
        localStorage.setItem(
          'mcp-chat-llm-config',
          JSON.stringify(newLLMConfig)
        );
      }
    } catch (error) {
      console.error('Error saving configuration:', error);
    }
  };

  const addServer = () => {
    if (!newServer.name || !newServer.path) {
      setSnackbar({
        open: true,
        message: 'Please fill in all required fields',
        severity: 'error',
      });
      return;
    }

    const server: MCPServer = {
      id: Date.now().toString(),
      name: newServer.name,
      path: newServer.path,
      args: newServer.args
        ? newServer.args.split(',').map(arg => arg.trim())
        : [],
      env: parseEnvString(newServer.env),
      type: newServer.type,
      status: 'disconnected',
    };

    const updatedServers = [...servers, server];
    setServers(updatedServers);
    saveConfig(updatedServers);

    setNewServer({ name: '', path: '', args: '', env: '', type: 'local' });
    setShowAddServerDialog(false);
    setSnackbar({
      open: true,
      message: 'Server added successfully',
      severity: 'success',
    });
  };

  const addServerFromWorkspace = (workspaceServer: any) => {
    // Check if server is already added
    const existingServer = servers.find(s => s.path === workspaceServer.path);
    if (existingServer) {
      setSnackbar({
        open: true,
        message: 'Server already added',
        severity: 'warning',
      });
      return;
    }

    const server: MCPServer = {
      id: Date.now().toString(),
      name: workspaceServer.name,
      path: workspaceServer.path,
      args: [],
      env: {},
      type: 'local',
      status: 'disconnected',
    };

    const updatedServers = [...servers, server];
    setServers(updatedServers);
    saveConfig(updatedServers);

    setShowServerSelectionDialog(false);
    setSnackbar({
      open: true,
      message: `Added ${workspaceServer.name} server`,
      severity: 'success',
    });
  };

  const removeServer = (serverId: string) => {
    const updatedServers = servers.filter(s => s.id !== serverId);
    setServers(updatedServers);
    saveConfig(updatedServers);
    setSnackbar({ open: true, message: 'Server removed', severity: 'info' });
  };

  const connectToServers = async () => {
    if (servers.length === 0) {
      setSnackbar({
        open: true,
        message: 'No servers configured',
        severity: 'warning',
      });
      return;
    }

    // Validate API key - only warn if it's explicitly set to test-key
    if (llmConfig.apiKey === 'test-key') {
      setSnackbar({
        open: true,
        message:
          'Please provide a valid OpenAI API key in the LLM configuration or set OPENAI_API_KEY environment variable',
        severity: 'warning',
      });
      return;
    }

    setIsLoading(true);

    try {
      // Update all servers to connecting status
      const connectingServers = servers.map(s => ({
        ...s,
        status: 'connecting' as const,
      }));
      setServers(connectingServers);

      const serverPaths = servers.map(s => s.path);
      const serverArgs = servers.map(s => s.args);
      const serverTypes = servers.map(s => s.type);
      const serverEnvs = servers.map(s => s.env);

      const response = await fetch('/api/mcp/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          servers: serverPaths,
          server_args: serverArgs,
          server_types: serverTypes,
          server_envs: serverEnvs,
          llm_config: llmConfig,
        }),
      });

      const result = await response.json();

      if (result.success) {
        // Update server statuses and tools
        const connectedServers = servers.map(server => {
          const serverInfo = result.server_mapping?.[server.path];
          return {
            ...server,
            status: serverInfo?.connected
              ? ('connected' as const)
              : ('error' as const),
            tools: serverInfo?.tools || [],
            error: serverInfo?.connected ? undefined : 'Failed to connect',
          };
        });

        setServers(connectedServers);
        setIsConnected(true);
        setSnackbar({
          open: true,
          message: `Connected to ${result.connected_count} server(s)`,
          severity: 'success',
        });

        // Add system message
        const systemMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'system',
          content: `Connected to ${result.connected_count} server(s). Available tools: ${result.total_tools}`,
          timestamp: new Date(),
        };
        setChatMessages([systemMessage]);
      } else {
        // Update servers with error status
        const errorServers = servers.map(s => ({
          ...s,
          status: 'error' as const,
          error: result.error,
        }));
        setServers(errorServers);

        // Check for API key related errors
        if (result.error && result.error.includes('API key')) {
          setSnackbar({
            open: true,
            message:
              'Invalid API key. Please check your OpenAI API key in the LLM configuration.',
            severity: 'error',
          });
        } else {
          setSnackbar({
            open: true,
            message: result.error || 'Failed to connect to servers',
            severity: 'error',
          });
        }
      }
    } catch (error) {
      const errorServers = servers.map(s => ({
        ...s,
        status: 'error' as const,
        error: 'Network error',
      }));
      setServers(errorServers);
      setSnackbar({
        open: true,
        message: 'Network error connecting to servers',
        severity: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const disconnectFromServers = async () => {
    try {
      await fetch('/api/mcp/disconnect', { method: 'POST' });

      const disconnectedServers = servers.map(s => ({
        ...s,
        status: 'disconnected' as const,
        tools: undefined,
        error: undefined,
      }));
      setServers(disconnectedServers);
      setIsConnected(false);
      setSnackbar({
        open: true,
        message: 'Disconnected from servers',
        severity: 'info',
      });

      // Clear chat messages
      setChatMessages([]);
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error disconnecting from servers',
        severity: 'error',
      });
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !isConnected) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/mcp/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
        }),
      });

      const result = await response.json();

      if (result.success) {
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: result.response,
          timestamp: new Date(),
          toolCalls: result.tool_calls,
          toolResults: result.tool_results,
        };

        setChatMessages(prev => [...prev, assistantMessage]);
      } else {
        // Provide better error messages for common issues
        let errorContent = result.error;
        if (result.error && result.error.includes('API key')) {
          errorContent =
            'Invalid API key. Please check your OpenAI API key in the LLM configuration.';
        }

        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'system',
          content: `Error: ${errorContent}`,
          timestamp: new Date(),
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Network error: ${error}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const saveLLMConfig = () => {
    saveConfig(undefined, llmConfig);
    setSnackbar({
      open: true,
      message: 'LLM configuration saved',
      severity: 'success',
    });
  };

  const getAvailableTools = () => {
    return servers
      .filter(s => s.status === 'connected')
      .flatMap(s => s.tools || []);
  };

  const truncateText = (text: string, maxLength: number = 500) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const shouldTruncateResult = (result: string) => {
    return result.length > 500;
  };

  const formatMessage = (message: ChatMessage) => {
    if (message.role === 'system') {
      return (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ fontStyle: 'italic' }}
        >
          {message.content}
        </Typography>
      );
    }

    return (
      <Box>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
          {message.content}
        </Typography>

        {message.toolCalls && message.toolCalls.length > 0 && (
          <Accordion sx={{ mt: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="body2" color="primary">
                🔧 Tool Calls ({message.toolCalls.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {message.toolCalls.map((call, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography
                    variant="subtitle2"
                    color="primary"
                    sx={{ fontWeight: 'bold' }}
                  >
                    🔧 {call.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 1 }}
                  >
                    Arguments:
                  </Typography>
                  <SyntaxHighlighter
                    language="json"
                    style={tomorrow}
                    customStyle={{
                      fontSize: '0.8rem',
                      margin: '8px 0',
                      maxHeight: '200px',
                      overflow: 'auto',
                      wordWrap: 'break-word',
                      whiteSpace: 'pre-wrap',
                    }}
                    wrapLongLines={true}
                  >
                    {JSON.stringify(call.arguments, null, 2)}
                  </SyntaxHighlighter>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        )}

        {message.toolResults && message.toolResults.length > 0 && (
          <Accordion sx={{ mt: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="body2" color="secondary">
                📊 Tool Results ({message.toolResults.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {message.toolResults.map((result, index) => {
                const resultText =
                  typeof result.result === 'string'
                    ? result.result
                    : JSON.stringify(result.result, null, 2);
                const resultKey = `${message.id}-result-${index}`;
                const isExpanded = expandedResults.has(resultKey);
                const isTooLong = shouldTruncateResult(resultText);
                const displayText =
                  isTooLong && !isExpanded
                    ? truncateText(resultText)
                    : resultText;

                const toggleExpanded = () => {
                  const newExpanded = new Set(expandedResults);
                  if (isExpanded) {
                    newExpanded.delete(resultKey);
                  } else {
                    newExpanded.add(resultKey);
                  }
                  setExpandedResults(newExpanded);
                };

                return (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        mb: 1,
                      }}
                    >
                      <Typography
                        variant="subtitle2"
                        color="secondary"
                        sx={{ fontWeight: 'bold' }}
                      >
                        📊 {result.name}
                      </Typography>
                      {isTooLong && (
                        <Button
                          size="small"
                          variant="text"
                          onClick={toggleExpanded}
                          sx={{ minWidth: 'auto', fontSize: '0.75rem' }}
                        >
                          {isExpanded ? 'Show Less' : 'Show More'}
                        </Button>
                      )}
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 1 }}
                    >
                      Result: {isTooLong && `(${resultText.length} characters)`}
                    </Typography>
                    <Box
                      sx={{
                        maxHeight: isExpanded ? '500px' : '300px',
                        overflow: 'auto',
                        border: '1px solid #e0e0e0',
                        borderRadius: 1,
                        position: 'relative',
                      }}
                    >
                      <SyntaxHighlighter
                        language="json"
                        style={tomorrow}
                        customStyle={{
                          fontSize: '0.8rem',
                          margin: '0',
                          wordWrap: 'break-word',
                          whiteSpace: 'pre-wrap',
                          maxWidth: '100%',
                        }}
                        wrapLongLines={true}
                      >
                        {displayText}
                      </SyntaxHighlighter>
                      {isTooLong && !isExpanded && (
                        <Box
                          sx={{
                            position: 'absolute',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            height: '40px',
                            background:
                              'linear-gradient(transparent, rgba(255,255,255,0.9))',
                            display: 'flex',
                            alignItems: 'end',
                            justifyContent: 'center',
                            pb: 1,
                          }}
                        >
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={toggleExpanded}
                          >
                            Show More (
                            {resultText.length - displayText.length + 3} more
                            characters)
                          </Button>
                        </Box>
                      )}
                    </Box>
                  </Box>
                );
              })}
            </AccordionDetails>
          </Accordion>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography
        variant="h4"
        gutterBottom
        sx={{ display: 'flex', alignItems: 'center', gap: 2 }}
      >
        <ChatIcon />
        MCP Chat Client
      </Typography>

      <Card sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={currentTab}
            onChange={(_, newValue) => setCurrentTab(newValue)}
          >
            <Tab label="Chat" icon={<ChatIcon />} />
            <Tab label="Servers" icon={<ServerIcon />} />
            <Tab label="Settings" icon={<SettingsIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          {/* Chat Tab */}
          <Box
            sx={{ height: '60vh', display: 'flex', flexDirection: 'column' }}
          >
            {/* Chat Header */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Chip
                  label={isConnected ? 'Connected' : 'Disconnected'}
                  color={isConnected ? 'success' : 'default'}
                  size="small"
                />
                <Typography variant="body2" color="text.secondary">
                  {servers.filter(s => s.status === 'connected').length}{' '}
                  server(s) connected
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {getAvailableTools().length} tool(s) available
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                {isConnected ? (
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={disconnectFromServers}
                    size="small"
                  >
                    Disconnect
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={connectToServers}
                    disabled={servers.length === 0 || isLoading}
                    size="small"
                  >
                    Connect
                  </Button>
                )}

                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => setChatMessages([])}
                  size="small"
                >
                  Clear Chat
                </Button>
              </Box>
            </Box>

            {/* Chat Messages */}
            <Paper
              sx={{
                flexGrow: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                p: 2,
                backgroundColor: 'grey.50',
                border: '1px solid',
                borderColor: 'grey.200',
                maxWidth: '100%',
              }}
            >
              {chatMessages.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {isConnected
                      ? 'Start a conversation by typing a message below'
                      : 'Connect to MCP servers to start chatting'}
                  </Typography>
                </Box>
              ) : (
                chatMessages.map(message => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      flexDirection:
                        message.role === 'user' ? 'row-reverse' : 'row',
                      mb: 2,
                      alignItems: 'flex-start',
                    }}
                  >
                    <Box
                      sx={{
                        minWidth: 40,
                        height: 40,
                        borderRadius: '50%',
                        backgroundColor:
                          message.role === 'user'
                            ? 'primary.main'
                            : message.role === 'assistant'
                              ? 'secondary.main'
                              : 'grey.400',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        mx: 1,
                      }}
                    >
                      {message.role === 'user' ? (
                        <PersonIcon />
                      ) : message.role === 'assistant' ? (
                        <BotIcon />
                      ) : (
                        <CodeIcon />
                      )}
                    </Box>

                    <Box
                      sx={{
                        maxWidth: '70%',
                        backgroundColor:
                          message.role === 'user' ? 'primary.light' : 'white',
                        color:
                          message.role === 'user' ? 'white' : 'text.primary',
                        borderRadius: 2,
                        p: 2,
                        boxShadow: 1,
                        overflow: 'hidden',
                        wordBreak: 'break-word',
                      }}
                    >
                      {formatMessage(message)}
                      <Typography
                        variant="caption"
                        sx={{ display: 'block', mt: 1, opacity: 0.7 }}
                      >
                        {message.timestamp.toLocaleTimeString()}
                      </Typography>
                    </Box>
                  </Box>
                ))
              )}
              <div ref={chatEndRef} />
            </Paper>

            {/* Chat Input */}
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder={
                  isConnected
                    ? 'Type your message...'
                    : 'Connect to servers first'
                }
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                disabled={!isConnected || isLoading}
                onKeyPress={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />
              <Button
                variant="contained"
                endIcon={
                  isLoading ? <CircularProgress size={20} /> : <SendIcon />
                }
                onClick={sendMessage}
                disabled={!isConnected || !inputMessage.trim() || isLoading}
                sx={{ minWidth: 100 }}
              >
                Send
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          {/* Servers Tab */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 2,
              }}
            >
              <Typography variant="h6">MCP Servers</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<ServerIcon />}
                  onClick={() => setShowServerSelectionDialog(true)}
                >
                  Select from Workspace
                </Button>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setShowAddServerDialog(true)}
                >
                  Add Custom Server
                </Button>
              </Box>
            </Box>

            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                How to use MCP Chat Client:
              </Typography>
              <Typography variant="body2" component="div">
                1. Configure your LLM settings in the Settings tab
                <br />
                2. Add MCP servers (local .py files, npm packages, or HTTP URLs)
                <br />
                3. Click Connect to establish connections
                <br />
                4. Start chatting with AI that has access to your tools!
              </Typography>
            </Alert>

            <MCPChatServerConfiguration
              servers={servers}
              onRemoveServer={removeServer}
            />
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          {/* Settings Tab */}
          <Box>
            <Typography variant="h6" gutterBottom>
              LLM Configuration
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Model"
                  value={llmConfig.model}
                  onChange={e =>
                    setLLMConfig({ ...llmConfig, model: e.target.value })
                  }
                  helperText="e.g., gpt-4o, gpt-3.5-turbo"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Key"
                  type="password"
                  value={llmConfig.apiKey}
                  onChange={e =>
                    setLLMConfig({ ...llmConfig, apiKey: e.target.value })
                  }
                  helperText="OpenAI API key"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Base URL (Optional)"
                  value={llmConfig.baseUrl}
                  onChange={e =>
                    setLLMConfig({ ...llmConfig, baseUrl: e.target.value })
                  }
                  helperText="Custom API endpoint"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Temperature"
                  type="number"
                  inputProps={{ min: 0, max: 2, step: 0.1 }}
                  value={llmConfig.temperature}
                  onChange={e =>
                    setLLMConfig({
                      ...llmConfig,
                      temperature: parseFloat(e.target.value),
                    })
                  }
                  helperText="0 = deterministic, 2 = very random"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Max Tokens"
                  type="number"
                  inputProps={{ min: 1, max: 4000 }}
                  value={llmConfig.maxTokens}
                  onChange={e =>
                    setLLMConfig({
                      ...llmConfig,
                      maxTokens: parseInt(e.target.value),
                    })
                  }
                  helperText="Maximum response length"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="System Prompt"
                  value={llmConfig.systemPrompt}
                  onChange={e =>
                    setLLMConfig({ ...llmConfig, systemPrompt: e.target.value })
                  }
                  helperText="Instructions for the AI assistant"
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  onClick={saveLLMConfig}
                  startIcon={<SettingsIcon />}
                >
                  Save Configuration
                </Button>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Card>

      {/* Add Server Dialog */}
      <Dialog
        open={showAddServerDialog}
        onClose={() => setShowAddServerDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add MCP Server</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <Alert severity="info" sx={{ mb: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Examples:
              </Typography>
              <Typography variant="body2" component="div">
                • Local: <code>mcp_servers/yfinance/server.py</code>
                <br />• NPM: <code>@openbnb/mcp-server-airbnb</code>
                <br />• NPM:{' '}
                <code>@modelcontextprotocol/server-sequential-thinking</code>
              </Typography>
            </Alert>

            <TextField
              fullWidth
              label="Server Name"
              value={newServer.name}
              onChange={e =>
                setNewServer({ ...newServer, name: e.target.value })
              }
              placeholder="e.g., YFinance Server"
            />

            <FormControl fullWidth>
              <InputLabel>Server Type</InputLabel>
              <Select
                value={newServer.type}
                onChange={e =>
                  setNewServer({
                    ...newServer,
                    type: e.target.value as 'local' | 'npm',
                  })
                }
              >
                <MenuItem value="local">Local Server (.py file)</MenuItem>
                <MenuItem value="npm">NPM Package</MenuItem>
                <MenuItem value="http">HTTP Server</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Server Path"
              value={newServer.path}
              onChange={e =>
                setNewServer({ ...newServer, path: e.target.value })
              }
              placeholder={
                newServer.type === 'local'
                  ? 'mcp_servers/yfinance/server.py'
                  : '@openbnb/mcp-server-airbnb'
              }
              helperText={
                newServer.type === 'local'
                  ? 'Path to your local server script'
                  : newServer.type === 'npm'
                  ? 'NPM package name'
                  : 'HTTP URL (e.g., http://127.0.0.1:8000/mcp)'
              }
            />

            <TextField
              fullWidth
              label="Arguments (Optional)"
              value={newServer.args}
              onChange={e =>
                setNewServer({ ...newServer, args: e.target.value })
              }
              placeholder="--ignore-robots-txt, --debug"
              helperText="Comma-separated arguments to pass to the server"
            />

            <TextField
              fullWidth
              label="Environment Variables (Optional)"
              value={newServer.env}
              onChange={e =>
                setNewServer({ ...newServer, env: e.target.value })
              }
              placeholder="API_KEY=secret123, DEBUG=true"
              helperText="Format: KEY1=value1, KEY2=value2"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddServerDialog(false)}>Cancel</Button>
          <Button onClick={addServer} variant="contained">
            Add Server
          </Button>
        </DialogActions>
      </Dialog>

      {/* Server Selection Dialog */}
      <Dialog
        open={showServerSelectionDialog}
        onClose={() => setShowServerSelectionDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Select Server from Workspace</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {availableServers.length === 0 ? (
              <Alert severity="info">
                No MCP servers found in workspace. Make sure you have servers in
                the mcp_servers directory.
              </Alert>
            ) : (
              <List>
                {availableServers.map((server, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      border: '1px solid',
                      borderColor: 'grey.300',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <Box sx={{ width: '100%' }}>
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <Box>
                          <Typography
                            variant="subtitle1"
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                            }}
                          >
                            {server.name}
                            <Chip label="local" size="small" color="primary" />
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {server.path}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {server.description}
                          </Typography>
                          {server.tools && server.tools.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                              >
                                Tools: {server.tools.join(', ')}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => addServerFromWorkspace(server)}
                          disabled={servers.some(s => s.path === server.path)}
                        >
                          {servers.some(s => s.path === server.path)
                            ? 'Added'
                            : 'Add'}
                        </Button>
                      </Box>
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowServerSelectionDialog(false)}>
            Close
          </Button>
          <Button
            onClick={fetchAvailableServers}
            variant="outlined"
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MCPChatClient;
