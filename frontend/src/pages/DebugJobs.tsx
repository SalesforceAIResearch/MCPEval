import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  TextField,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Refresh, Stop, Visibility } from '@mui/icons-material';

interface JobInfo {
  job_id: string;
  progress: {
    status: string;
    progress: number;
  };
  logs: string[];
  type?: string;
  title?: string;
}

const DebugJobs: React.FC = () => {
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [selectedJob, setSelectedJob] = useState<JobInfo | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [testJobId, setTestJobId] = useState<string>('');

  const fetchJobs = async () => {
    setLoading(true);
    setError('');

    try {
      // Since we don't have an endpoint to list all jobs, we'll need to check recent activities
      const response = await fetch('/api/recent-activities');
      if (!response.ok) {
        throw new Error('Failed to fetch recent activities');
      }

      const data = await response.json();
      const activities = data.activities || [];

      // Get detailed status for each job
      const jobPromises = activities.map(async (activity: any) => {
        try {
          const statusResponse = await fetch(`/api/job/${activity.id}`);
          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            return {
              job_id: activity.id,
              progress: statusData.progress || {
                status: 'unknown',
                progress: 0,
              },
              logs: statusData.logs || [],
              title: activity.title || 'Unknown Job',
              type: activity.type || 'Unknown Type',
            };
          }
          return null;
        } catch (err) {
          return null;
        }
      });

      const jobResults = await Promise.all(jobPromises);
      const validJobs = jobResults.filter(job => job !== null);
      setJobs(validJobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const killJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/job/${jobId}/kill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        alert(`Job ${jobId} killed successfully`);
        fetchJobs(); // Refresh the list
      } else {
        const errorData = await response.json();
        alert(`Failed to kill job: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      alert(
        `Error killing job: ${err instanceof Error ? err.message : 'Unknown error'}`
      );
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'warning';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const testJobStatus = async () => {
    if (!testJobId) return;

    try {
      const response = await fetch(`/api/job/${testJobId}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedJob({
          job_id: testJobId,
          progress: data.progress || { status: 'unknown', progress: 0 },
          logs: data.logs || [],
        });
        setDialogOpen(true);
      } else {
        const errorData = await response.json();
        alert(`Job not found: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      alert(
        `Error fetching job: ${err instanceof Error ? err.message : 'Unknown error'}`
      );
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🐛 Debug Jobs
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Debug and manage running jobs, useful for troubleshooting hanging
          verification
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Quick Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Test Job ID"
                value={testJobId}
                onChange={e => setTestJobId(e.target.value)}
                placeholder="Enter job ID to check status"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Button
                variant="outlined"
                onClick={testJobStatus}
                disabled={!testJobId}
                sx={{ mr: 1 }}
              >
                Check Status
              </Button>
              <Button
                variant="outlined"
                onClick={fetchJobs}
                disabled={loading}
                startIcon={<Refresh />}
              >
                Refresh Jobs
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Jobs List */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Jobs
          </Typography>

          {loading ? (
            <Typography>Loading jobs...</Typography>
          ) : jobs.length === 0 ? (
            <Typography color="text.secondary">No jobs found</Typography>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Job ID</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {jobs.map(job => (
                    <TableRow key={job.job_id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {job.job_id.slice(0, 8)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {job.type || 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={job.progress.status}
                          color={getStatusColor(job.progress.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {job.progress.progress}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => {
                            setSelectedJob(job);
                            setDialogOpen(true);
                          }}
                          size="small"
                        >
                          <Visibility />
                        </IconButton>
                        {job.progress.status === 'running' && (
                          <IconButton
                            onClick={() => killJob(job.job_id)}
                            size="small"
                            color="error"
                          >
                            <Stop />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Job Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Job Details: {selectedJob?.job_id.slice(0, 8)}...
        </DialogTitle>
        <DialogContent>
          {selectedJob && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Status: {selectedJob.progress.status} (
                {selectedJob.progress.progress}%)
              </Typography>

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Logs ({selectedJob.logs.length} entries):
              </Typography>

              <Box
                sx={{
                  maxHeight: 400,
                  overflow: 'auto',
                  backgroundColor: '#f5f5f5',
                  p: 2,
                  borderRadius: 1,
                  fontSize: '0.8rem',
                  fontFamily: 'monospace',
                }}
              >
                {selectedJob.logs.length === 0 ? (
                  <Typography color="text.secondary">
                    No logs available
                  </Typography>
                ) : (
                  selectedJob.logs.map((log, index) => (
                    <div key={index}>{log}</div>
                  ))
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {selectedJob?.progress.status === 'running' && (
            <Button
              onClick={() => {
                killJob(selectedJob.job_id);
                setDialogOpen(false);
              }}
              color="error"
              startIcon={<Stop />}
            >
              Kill Job
            </Button>
          )}
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DebugJobs;
