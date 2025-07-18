import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  Button,
  Grid,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import {
  Assessment as ReportsIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DescriptionIcon,
  Analytics as AnalyticsIcon,
  DataObject as DataIcon,
  BarChart as ChartIcon,
  Gavel as JudgeIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Storage as StorageIcon,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';

interface ReportInfo {
  name: string;
  path: string;
  domain: string;
  type: string;
  extension: string;
  size: number;
  modified: string;
  preview?: string;
}

interface ReportDebugInfo {
  searched_locations: string[];
  locations_status: Array<{
    path: string;
    exists: boolean;
    has_content: boolean;
  }>;
}

const Results: React.FC = () => {
  const [reports, setReports] = useState<ReportInfo[]>([]);
  const [reportDebugInfo, setReportDebugInfo] =
    useState<ReportDebugInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [viewContent, setViewContent] = useState<string>('');
  const [viewTitle, setViewTitle] = useState<string>('');
  const [viewType, setViewType] = useState<'json' | 'markdown' | 'text'>(
    'text'
  );
  const [contentLoading, setContentLoading] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/reports');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch reports');
      }

      setReports(data.reports || []);
      setReportDebugInfo(data.debug_info || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reports');
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

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'analysis':
        return <AnalyticsIcon />;
      case 'summary':
        return <DescriptionIcon />;
      case 'judging':
        return <JudgeIcon />;
      case 'data':
        return <DataIcon />;
      case 'chart':
        return <ChartIcon />;
      default:
        return <ReportsIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'analysis':
        return 'primary';
      case 'summary':
        return 'secondary';
      case 'judging':
        return 'warning';
      case 'data':
        return 'info';
      case 'chart':
        return 'success';
      default:
        return 'default';
    }
  };

  const groupReportsByDomain = (reports: ReportInfo[]) => {
    const groups: Record<string, ReportInfo[]> = {};
    reports.forEach(report => {
      if (!groups[report.domain]) {
        groups[report.domain] = [];
      }
      groups[report.domain].push(report);
    });
    return groups;
  };

  const handleDownload = (path: string) => {
    const link = document.createElement('a');
    link.href = `/api/download/${encodeURIComponent(path)}`;
    link.download = path.split('/').pop() || 'report';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleView = async (report: ReportInfo) => {
    try {
      setContentLoading(true);
      setViewTitle(report.name);

      const response = await fetch(
        `/api/file-content/${encodeURIComponent(report.path)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch file content');
      }

      setViewContent(data.content || '');

      // Determine view type based on file extension
      if (report.extension === '.json') {
        setViewType('json');
      } else if (report.extension === '.md') {
        setViewType('markdown');
      } else {
        setViewType('text');
      }

      setViewModalOpen(true);
    } catch (err) {
      console.error('Failed to load content:', err);
      // You could also set an error state here if needed
    } finally {
      setContentLoading(false);
    }
  };

  const renderContent = () => {
    if (contentLoading) {
      return (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="200px"
        >
          <CircularProgress />
        </Box>
      );
    }

    if (viewType === 'json') {
      try {
        const jsonData = JSON.parse(viewContent);
        return (
          <Paper
            sx={{
              p: 2,
              bgcolor: 'grey.50',
              maxHeight: '60vh',
              overflow: 'auto',
            }}
          >
            <pre
              style={{
                margin: 0,
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
              }}
            >
              {JSON.stringify(jsonData, null, 2)}
            </pre>
          </Paper>
        );
      } catch (e) {
        return (
          <Paper
            sx={{
              p: 2,
              bgcolor: 'grey.50',
              maxHeight: '60vh',
              overflow: 'auto',
            }}
          >
            <pre
              style={{
                margin: 0,
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
              }}
            >
              {viewContent}
            </pre>
          </Paper>
        );
      }
    } else if (viewType === 'markdown') {
      return (
        <Paper
          sx={{ p: 3, bgcolor: 'white', maxHeight: '60vh', overflow: 'auto' }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              // Custom styling for markdown elements
              h1: ({ children }) => (
                <Typography
                  variant="h4"
                  component="h1"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    borderBottom: '2px solid #e0e0e0',
                    pb: 1,
                  }}
                >
                  {children}
                </Typography>
              ),
              h2: ({ children }) => (
                <Typography
                  variant="h5"
                  component="h2"
                  gutterBottom
                  sx={{ color: 'primary.main', mt: 3, mb: 2 }}
                >
                  {children}
                </Typography>
              ),
              h3: ({ children }) => (
                <Typography
                  variant="h6"
                  component="h3"
                  gutterBottom
                  sx={{ color: 'primary.main', mt: 2, mb: 1 }}
                >
                  {children}
                </Typography>
              ),
              h4: ({ children }) => (
                <Typography
                  variant="subtitle1"
                  component="h4"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 2,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              h5: ({ children }) => (
                <Typography
                  variant="subtitle2"
                  component="h5"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 1,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              h6: ({ children }) => (
                <Typography
                  variant="body1"
                  component="h6"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 1,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              p: ({ children }) => (
                <Typography variant="body1" paragraph sx={{ mb: 2 }}>
                  {children}
                </Typography>
              ),
              ul: ({ children }) => (
                <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              ol: ({ children }) => (
                <Box component="ol" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              li: ({ children }) => (
                <Typography component="li" variant="body1" sx={{ mb: 0.5 }}>
                  {children}
                </Typography>
              ),
              blockquote: ({ children }) => (
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: 'grey.100',
                    borderLeft: '4px solid #1976d2',
                    mb: 2,
                  }}
                >
                  <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                    {children}
                  </Typography>
                </Paper>
              ),
              code: ({ children, className }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <Box
                      component="code"
                      sx={{
                        bgcolor: 'grey.100',
                        px: 0.5,
                        py: 0.25,
                        borderRadius: 1,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      {children}
                    </Box>
                  );
                }
                return (
                  <Paper
                    sx={{ p: 2, bgcolor: 'grey.100', mb: 2, overflow: 'auto' }}
                  >
                    <pre
                      style={{
                        margin: 0,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      <code>{children}</code>
                    </pre>
                  </Paper>
                );
              },
              table: ({ children }) => (
                <Box sx={{ overflow: 'auto', mb: 2 }}>
                  <Box
                    component="table"
                    sx={{ minWidth: '100%', border: '1px solid #e0e0e0' }}
                  >
                    {children}
                  </Box>
                </Box>
              ),
              th: ({ children }) => (
                <Box
                  component="th"
                  sx={{
                    p: 1,
                    bgcolor: 'grey.100',
                    border: '1px solid #e0e0e0',
                    fontWeight: 'bold',
                    textAlign: 'left',
                  }}
                >
                  {children}
                </Box>
              ),
              td: ({ children }) => (
                <Box
                  component="td"
                  sx={{
                    p: 1,
                    border: '1px solid #e0e0e0',
                  }}
                >
                  {children}
                </Box>
              ),
            }}
          >
            {viewContent}
          </ReactMarkdown>
        </Paper>
      );
    } else {
      return (
        <Paper
          sx={{ p: 2, bgcolor: 'grey.50', maxHeight: '60vh', overflow: 'auto' }}
        >
          <pre
            style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}
          >
            {viewContent}
          </pre>
        </Paper>
      );
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="400px"
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
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
      </Container>
    );
  }

  const groupedReports = groupReportsByDomain(reports);

  return (
    <Container maxWidth="lg">
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Box>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <ReportsIcon sx={{ mr: 1 }} />
            📊 Results & Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and download evaluation results, reports, and performance
            analytics
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {reports.length === 0 ? (
        <Paper sx={{ p: 3 }}>
          <Box textAlign="center" mb={3}>
            <ReportsIcon
              sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }}
            />
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No Report Files Found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              No report files were found in the expected directories.
            </Typography>
          </Box>

          {/* Debug Information */}
          {reportDebugInfo && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Search Debug Information
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Searched Locations:</strong>
              </Typography>
              <List dense>
                {reportDebugInfo.locations_status.map((location, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {location.exists ? (
                        location.has_content ? (
                          <CheckCircle color="success" fontSize="small" />
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
                ))}
              </List>
            </Box>
          )}
        </Paper>
      ) : (
        <Box>
          {Object.entries(groupedReports).map(([domain, domainReports]) => (
            <Box key={domain} mb={4}>
              <Typography
                variant="h5"
                gutterBottom
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <StorageIcon sx={{ mr: 1 }} />
                {domain === 'unknown' ? 'Other Reports' : domain}
              </Typography>
              <Grid container spacing={3}>
                {domainReports.map((report, index) => (
                  <Grid item xs={12} md={6} lg={4} key={index}>
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
                          {getTypeIcon(report.type)}
                          <Typography
                            variant="h6"
                            component="h2"
                            sx={{ ml: 1, flexGrow: 1 }}
                          >
                            {report.name}
                          </Typography>
                          <Chip
                            label={report.type}
                            size="small"
                            color={getTypeColor(report.type) as any}
                            sx={{ ml: 1 }}
                          />
                        </Box>

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
                            Path: {report.path}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            gutterBottom
                          >
                            Size: {formatFileSize(report.size)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            <ScheduleIcon
                              sx={{
                                fontSize: 16,
                                mr: 0.5,
                                verticalAlign: 'middle',
                              }}
                            />
                            Modified: {formatDate(report.modified)}
                          </Typography>
                        </Box>

                        {report.preview && (
                          <Box mb={2}>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              gutterBottom
                            >
                              Preview:
                            </Typography>
                            <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                              <Typography
                                variant="body2"
                                sx={{ fontStyle: 'italic' }}
                              >
                                {report.preview}
                              </Typography>
                            </Paper>
                          </Box>
                        )}

                        <Box display="flex" justifyContent="flex-end" gap={1}>
                          <Tooltip title="View file">
                            <IconButton
                              size="small"
                              onClick={() => handleView(report)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download file">
                            <IconButton
                              size="small"
                              onClick={() => handleDownload(report.path)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}
        </Box>
      )}

      <Box mt={4} textAlign="center">
        <Typography variant="body2" color="text.secondary">
          Found {reports.length} report file{reports.length !== 1 ? 's' : ''}{' '}
          across {Object.keys(groupedReports).length} domain
          {Object.keys(groupedReports).length !== 1 ? 's' : ''}
        </Typography>
      </Box>

      {/* View Content Modal */}
      <Dialog
        open={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <ReportsIcon sx={{ mr: 1 }} />
            {viewTitle}
          </Box>
        </DialogTitle>
        <DialogContent>{renderContent()}</DialogContent>
        <DialogActions>
          <Button onClick={() => setViewModalOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Results;
