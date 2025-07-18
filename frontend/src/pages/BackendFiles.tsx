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
  Paper,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Refresh as RefreshIcon,
  InsertDriveFile as FileIcon,
  Settings as SettingsIcon,
  Terminal as TerminalIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
  Settings as BackendIcon,
} from '@mui/icons-material';

interface BackendFile {
  name: string;
  path: string;
  extension: string;
  size: number;
  modified: string;
  type: string;
  description: string;
  error?: string;
}

const BackendFiles: React.FC = () => {
  const [backendFiles, setBackendFiles] = useState<BackendFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBackendFiles = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/backend-files');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch backend files');
      }

      setBackendFiles(data.files || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch backend files'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackendFiles();
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

  const getFileTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'python':
        return <CodeIcon />;
      case 'yaml':
      case 'json':
        return <SettingsIcon />;
      case 'markdown':
        return <DescriptionIcon />;
      case 'shell':
        return <TerminalIcon />;
      default:
        return <FileIcon />;
    }
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
          onClick={fetchBackendFiles}
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
          <BackendIcon sx={{ mr: 1 }} />
          Backend Files
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchBackendFiles}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {backendFiles.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <BackendIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body1" color="text.secondary" gutterBottom>
            No Backend Files Found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No files were found in the backend directory.
          </Typography>
        </Paper>
      ) : (
        <>
          <Grid container spacing={3}>
            {backendFiles.map(file => (
              <Grid item xs={12} md={6} lg={4} key={file.name}>
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
                      {React.cloneElement(getFileTypeIcon(file.type), {
                        color: 'primary',
                        sx: { mr: 1 },
                      })}
                      <Typography variant="h6" component="h2">
                        {file.name}
                      </Typography>
                      <Chip
                        label={file.extension}
                        size="small"
                        sx={{ ml: 'auto', fontSize: '0.7rem' }}
                      />
                    </Box>

                    {file.error ? (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        Error reading file: {file.error}
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
                          {file.description}
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
                            Path: {file.path}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            gutterBottom
                          >
                            Size: {formatFileSize(file.size)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            <ScheduleIcon
                              sx={{
                                fontSize: 16,
                                mr: 0.5,
                                verticalAlign: 'middle',
                              }}
                            />
                            Modified: {formatDate(file.modified)}
                          </Typography>
                        </Box>

                        <Chip
                          label={file.type.toUpperCase()}
                          variant="outlined"
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Box mt={4} textAlign="center">
            <Typography variant="body2" color="text.secondary">
              Found {backendFiles.length} backend file
              {backendFiles.length !== 1 ? 's' : ''} in the workspace
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
};

export default BackendFiles;
