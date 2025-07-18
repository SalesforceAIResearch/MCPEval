import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
} from '@mui/material';
import {
  Code as CodeIcon,
  Functions as FunctionsIcon,
  ExpandMore as ExpandMoreIcon,
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  Description as DescriptionIcon,
  Refresh as RefreshIcon,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';

interface ServerInfo {
  name: string;
  path: string;
  description: string;
  tools: string[];
  size: number;
  modified: string;
  error?: string;
}

interface ServerDebugInfo {
  configured_path: string | null;
  used_path: string | null;
  searched_locations: string[];
  locations_status: Array<{
    path: string;
    exists: boolean;
    has_content: boolean;
  }>;
}

const ServerFiles: React.FC = () => {
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [serverDebugInfo, setServerDebugInfo] =
    useState<ServerDebugInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/servers');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch servers');
      }

      setServers(data.servers || []);
      setServerDebugInfo(data.debug_info || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch servers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography
          variant="h4"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center' }}
        >
          <CodeIcon sx={{ mr: 1 }} />
          MCP Server Files
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* MCP Server Files Section */}
      <Box mb={4}>
        {servers.length === 0 ? (
          <Paper sx={{ p: 3 }}>
            <Box textAlign="center" mb={3}>
              <StorageIcon
                sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }}
              />
              <Typography variant="body1" color="text.secondary" gutterBottom>
                No MCP Server Files Found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                No server files were found in the expected directories.
              </Typography>
            </Box>

            {/* Debug Information */}
            {serverDebugInfo && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Search Debug Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" gutterBottom>
                      <strong>Configured Path:</strong>{' '}
                      {serverDebugInfo.configured_path || 'Not configured'}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Used Path:</strong>{' '}
                      {serverDebugInfo.used_path || 'No valid path found'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" gutterBottom>
                      <strong>Searched Locations:</strong>
                    </Typography>
                    <List dense>
                      {serverDebugInfo.locations_status.map(
                        (location, index) => (
                          <ListItem key={index} disablePadding>
                            <ListItemIcon sx={{ minWidth: 36 }}>
                              {location.exists ? (
                                location.has_content ? (
                                  <CheckCircle
                                    color="success"
                                    fontSize="small"
                                  />
                                ) : (
                                  <Cancel color="warning" fontSize="small" />
                                )
                              ) : (
                                <Cancel color="error" fontSize="small" />
                              )}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Typography
                                  variant="body2"
                                  sx={{ fontFamily: 'monospace' }}
                                >
                                  {location.path}
                                </Typography>
                              }
                              secondary={
                                <Typography variant="caption">
                                  {location.exists
                                    ? location.has_content
                                      ? 'Exists with content'
                                      : 'Exists but empty'
                                    : 'Does not exist'}
                                </Typography>
                              }
                            />
                          </ListItem>
                        )
                      )}
                    </List>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {servers.map(server => (
              <Grid item xs={12} md={6} lg={4} key={server.name}>
                <Card
                  elevation={2}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box display="flex" alignItems="center" mb={2}>
                      <CodeIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6" component="h2">
                        {server.name}
                      </Typography>
                      <Chip
                        label=".py"
                        size="small"
                        sx={{ ml: 'auto', fontSize: '0.7rem' }}
                      />
                    </Box>

                    {server.error ? (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        Error reading server: {server.error}
                      </Alert>
                    ) : (
                      <>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          gutterBottom
                        >
                          <DescriptionIcon
                            sx={{
                              fontSize: 16,
                              mr: 0.5,
                              verticalAlign: 'middle',
                            }}
                          />
                          {server.description}
                        </Typography>

                        <Box mb={2}>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            gutterBottom
                          >
                            <StorageIcon
                              sx={{
                                fontSize: 16,
                                mr: 0.5,
                                verticalAlign: 'middle',
                              }}
                            />
                            Path: {server.path}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            gutterBottom
                          >
                            Size: {formatFileSize(server.size)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            <ScheduleIcon
                              sx={{
                                fontSize: 16,
                                mr: 0.5,
                                verticalAlign: 'middle',
                              }}
                            />
                            Modified: {formatDate(server.modified)}
                          </Typography>
                        </Box>

                        {server.tools && server.tools.length > 0 && (
                          <Accordion sx={{ mt: 2 }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box display="flex" alignItems="center">
                                <FunctionsIcon sx={{ mr: 1, fontSize: 20 }} />
                                <Typography variant="body2">
                                  Tools ({server.tools.length})
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <List dense>
                                {server.tools.map((tool, index) => (
                                  <ListItem key={index} disablePadding>
                                    <ListItemIcon sx={{ minWidth: 36 }}>
                                      <FunctionsIcon fontSize="small" />
                                    </ListItemIcon>
                                    <ListItemText
                                      primary={
                                        <Typography
                                          variant="body2"
                                          sx={{ fontFamily: 'monospace' }}
                                        >
                                          {tool}
                                        </Typography>
                                      }
                                    />
                                  </ListItem>
                                ))}
                              </List>
                            </AccordionDetails>
                          </Accordion>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      <Box mt={4} textAlign="center">
        <Typography variant="body2" color="text.secondary">
          Found {servers.length} MCP server file
          {servers.length !== 1 ? 's' : ''} in the workspace
        </Typography>
      </Box>
    </Box>
  );
};

export default ServerFiles;
