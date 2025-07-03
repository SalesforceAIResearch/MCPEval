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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import {
  Transform as ConvertIcon,
  Upload,
  Download,
  Info,
} from '@mui/icons-material';

const DataConverter: React.FC = () => {
  const [inputFile, setInputFile] = useState('');
  const [outputFile, setOutputFile] = useState('');
  const [prefix, setPrefix] = useState('task');
  const [split, setSplit] = useState('train');
  const [taskId, setTaskId] = useState('');
  const [instruction, setInstruction] = useState(
    'You are a helpful assistant that can use tools to complete tasks.'
  );
  const [systemMessage, setSystemMessage] = useState('-1');
  const [isConverting, setIsConverting] = useState(false);
  const [conversionResult, setConversionResult] = useState<string | null>(null);

  const handleConvert = async () => {
    setIsConverting(true);
    setConversionResult(null);

    try {
      const payload = {
        input: inputFile,
        output: outputFile,
        prefix,
        split,
        task_id: taskId || null,
        instruction,
        system_message: systemMessage === '-1' ? null : systemMessage,
      };

      // TODO: Replace with actual API call
      console.log('Conversion payload:', payload);

      // Simulate conversion
      await new Promise(resolve => setTimeout(resolve, 2000));

      setConversionResult(
        `Successfully converted ${inputFile} to ${outputFile} in XLAM format`
      );
    } catch (error) {
      setConversionResult(`Error: ${error}`);
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🔄 Convert Data
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Convert task data to different formats (e.g., XLAM) for training or
          evaluation
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Conversion Configuration
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            This tool converts JSONL task files to XLAM format, which is
            commonly used for training and evaluation of language models.
          </Alert>

          {/* File Configuration */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Input File"
                value={inputFile}
                onChange={e => setInputFile(e.target.value)}
                placeholder="data/verified_tasks.jsonl"
                helperText="Path to input JSONL or JSON file"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Output File"
                value={outputFile}
                onChange={e => setOutputFile(e.target.value)}
                placeholder="data/xlam_format.json"
                helperText="Path for the converted output file"
                required
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* Conversion Settings */}
          <Typography variant="subtitle1" gutterBottom>
            Conversion Settings
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Trajectory ID Prefix"
                value={prefix}
                onChange={e => setPrefix(e.target.value)}
                helperText="Prefix for unique trajectory IDs"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Dataset Split</InputLabel>
                <Select
                  value={split}
                  label="Dataset Split"
                  onChange={e => setSplit(e.target.value)}
                >
                  <MenuItem value="train">Train</MenuItem>
                  <MenuItem value="test">Test</MenuItem>
                  <MenuItem value="val">Validation</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <TextField
              fullWidth
              label="Task ID (Optional)"
              value={taskId}
              onChange={e => setTaskId(e.target.value)}
              placeholder="task_123"
              helperText="Extract specific task from evaluation results (for single JSON input)"
            />
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Message Configuration */}
          <Typography variant="subtitle1" gutterBottom>
            Message Configuration
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Default Instruction"
                value={instruction}
                onChange={e => setInstruction(e.target.value)}
                helperText="Default instruction if no specific task_instruction is provided"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="System Message"
                value={systemMessage}
                onChange={e => setSystemMessage(e.target.value)}
                helperText="System message to include (use '-1' to ignore system messages)"
              />
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Box
            sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 4 }}
          >
            <Button
              variant="outlined"
              startIcon={<Upload />}
              onClick={() => {
                // TODO: Implement file upload
                console.log('Upload input file');
              }}
            >
              Upload Input File
            </Button>
            <Button
              variant="contained"
              onClick={handleConvert}
              disabled={isConverting || !inputFile || !outputFile}
              startIcon={<ConvertIcon />}
              size="large"
            >
              {isConverting ? 'Converting...' : 'Convert Data'}
            </Button>
          </Box>

          {/* Conversion Result */}
          {conversionResult && (
            <Box sx={{ mt: 3 }}>
              <Alert
                severity={
                  conversionResult.includes('Error') ? 'error' : 'success'
                }
                sx={{ mb: 2 }}
              >
                {conversionResult}
              </Alert>

              {!conversionResult.includes('Error') && (
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => {
                    // TODO: Implement file download
                    console.log('Download converted file');
                  }}
                >
                  Download Converted File
                </Button>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Help Card */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Info sx={{ mr: 1 }} />
            Conversion Examples
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            Common Use Cases:
          </Typography>

          <Box sx={{ mb: 2 }}>
            <Chip
              label="JSONL → XLAM"
              variant="outlined"
              sx={{ mr: 1, mb: 1 }}
            />
            <Typography variant="body2" component="span">
              Convert task files to XLAM format for model training
            </Typography>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Chip
              label="Evaluation Results"
              variant="outlined"
              sx={{ mr: 1, mb: 1 }}
            />
            <Typography variant="body2" component="span">
              Extract specific tasks from evaluation result files
            </Typography>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Chip
              label="Dataset Splits"
              variant="outlined"
              sx={{ mr: 1, mb: 1 }}
            />
            <Typography variant="body2" component="span">
              Prepare data for train/test/validation splits
            </Typography>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            The XLAM format is widely used in the research community for
            tool-using language model evaluation and training.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default DataConverter;
