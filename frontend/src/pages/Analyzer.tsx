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
  Alert,
  Divider,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Analytics as AnalyzeIcon,
  Upload,
  Download,
  Info,
  TrendingUp,
} from '@mui/icons-material';

interface AnalysisResult {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  totalTasks: number;
  successfulTasks: number;
  failedTasks: number;
  averageSteps: number;
  report: string;
}

const Analyzer: React.FC = () => {
  const [evaluationFile, setEvaluationFile] = useState('');
  const [groundTruthFile, setGroundTruthFile] = useState('');
  const [outputFile, setOutputFile] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null
  );

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      const payload = {
        evaluation_file: evaluationFile,
        ground_truth_file: groundTruthFile,
        output_file: outputFile,
      };

      // TODO: Replace with actual API call
      console.log('Analysis payload:', payload);

      // Simulate analysis
      await new Promise(resolve => setTimeout(resolve, 4000));

      // Mock analysis results
      setAnalysisResult({
        accuracy: 0.85,
        precision: 0.82,
        recall: 0.88,
        f1Score: 0.85,
        totalTasks: 50,
        successfulTasks: 42,
        failedTasks: 8,
        averageSteps: 3.2,
        report:
          'Analysis completed successfully. Model shows strong performance on most task categories with some challenges in complex multi-step tasks.',
      });
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🔍 Analyze Results
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Analyze evaluation results against ground truth to generate
          comprehensive performance reports
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Configuration
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                Compare evaluation results with ground truth to get detailed
                performance metrics and insights.
              </Alert>

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Evaluation Results File"
                    value={evaluationFile}
                    onChange={e => setEvaluationFile(e.target.value)}
                    placeholder="data/evaluation_results.json"
                    helperText="JSON file containing model evaluation results"
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Ground Truth File"
                    value={groundTruthFile}
                    onChange={e => setGroundTruthFile(e.target.value)}
                    placeholder="data/ground_truth.jsonl"
                    helperText="JSONL file containing expected results/answers"
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Output Report File"
                    value={outputFile}
                    onChange={e => setOutputFile(e.target.value)}
                    placeholder="analysis_report.json"
                    helperText="Path for the generated analysis report"
                    required
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<Upload />}
                  onClick={() => {
                    // TODO: Implement file upload
                    console.log('Upload files');
                  }}
                >
                  Upload Files
                </Button>
                <Button
                  variant="contained"
                  onClick={handleAnalyze}
                  disabled={
                    isAnalyzing ||
                    !evaluationFile ||
                    !groundTruthFile ||
                    !outputFile
                  }
                  startIcon={isAnalyzing ? <TrendingUp /> : <AnalyzeIcon />}
                  size="large"
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Results'}
                </Button>
              </Box>

              {isAnalyzing && (
                <Box sx={{ mt: 3 }}>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Analyzing evaluation results...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Results Panel */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Results
              </Typography>

              {!analysisResult && !isAnalyzing && (
                <Alert severity="info">
                  Run analysis to see performance metrics and detailed insights
                </Alert>
              )}

              {analysisResult && (
                <>
                  {/* Key Metrics */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6} md={3}>
                      <Box
                        sx={{
                          textAlign: 'center',
                          p: 2,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="h4" color="primary">
                          {(analysisResult.accuracy * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Accuracy
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box
                        sx={{
                          textAlign: 'center',
                          p: 2,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="h4" color="secondary">
                          {(analysisResult.f1Score * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          F1 Score
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box
                        sx={{
                          textAlign: 'center',
                          p: 2,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="h4" color="success.main">
                          {analysisResult.successfulTasks}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Successful
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box
                        sx={{
                          textAlign: 'center',
                          p: 2,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="h4" color="error.main">
                          {analysisResult.failedTasks}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Failed
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  {/* Detailed Metrics */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Detailed Performance Metrics
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Chip
                          label={`Precision: ${(analysisResult.precision * 100).toFixed(1)}%`}
                          variant="outlined"
                          sx={{ mb: 1, mr: 1 }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <Chip
                          label={`Recall: ${(analysisResult.recall * 100).toFixed(1)}%`}
                          variant="outlined"
                          sx={{ mb: 1, mr: 1 }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <Chip
                          label={`Total Tasks: ${analysisResult.totalTasks}`}
                          variant="outlined"
                          sx={{ mb: 1, mr: 1 }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <Chip
                          label={`Avg Steps: ${analysisResult.averageSteps}`}
                          variant="outlined"
                          sx={{ mb: 1, mr: 1 }}
                        />
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Summary Report */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Analysis Summary
                    </Typography>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      {analysisResult.report}
                    </Alert>
                  </Box>

                  {/* Download Button */}
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => {
                      // TODO: Implement file download
                      console.log('Download analysis report');
                    }}
                  >
                    Download Full Report
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Help Section */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Info sx={{ mr: 1 }} />
            Analysis Overview
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                What This Analysis Provides:
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Accuracy, Precision, Recall, F1 Score
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Task-by-task comparison results
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Performance breakdown by categories
              </Typography>
              <Typography variant="body2">
                • Detailed error analysis and insights
              </Typography>
            </Grid>

            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Required File Formats:
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Evaluation results: JSON format
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Ground truth: JSONL format
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Both files must have matching task IDs
              </Typography>
              <Typography variant="body2">
                • Expected outcomes clearly defined
              </Typography>
            </Grid>

            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Best Practices:
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Use verified tasks for ground truth
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Ensure consistent task identifiers
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                • Review failed cases for patterns
              </Typography>
              <Typography variant="body2">
                • Compare multiple model results
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Analyzer;
