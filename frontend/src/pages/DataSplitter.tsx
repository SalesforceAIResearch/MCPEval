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
  Slider,
  Divider,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  ContentCut as SplitIcon,
  Upload,
  Download,
  Info,
  Shuffle,
} from '@mui/icons-material';

interface SplitRatios {
  train: number;
  valid: number;
  test: number;
}

const DataSplitter: React.FC = () => {
  const [inputFile, setInputFile] = useState('');
  const [outputPrefix, setOutputPrefix] = useState('data/split');
  const [splitRatios, setSplitRatios] = useState<SplitRatios>({
    train: 70,
    valid: 15,
    test: 15,
  });
  const [randomSeed, setRandomSeed] = useState(42);
  const [shuffleData, setShuffleData] = useState(true);
  const [stratified, setStratified] = useState(false);
  const [isSplitting, setIsSplitting] = useState(false);
  const [splittingResult, setSplittingResult] = useState<string | null>(null);

  const handleRatioChange = (split: keyof SplitRatios, value: number) => {
    setSplitRatios(prev => {
      const newRatios = { ...prev, [split]: value };
      const total = newRatios.train + newRatios.valid + newRatios.test;

      if (total !== 100) {
        // Adjust other ratios proportionally
        const remaining = 100 - value;
        const otherKeys = Object.keys(newRatios).filter(
          k => k !== split
        ) as (keyof SplitRatios)[];
        const otherTotal = otherKeys.reduce((sum, key) => sum + prev[key], 0);

        if (otherTotal > 0) {
          otherKeys.forEach(key => {
            newRatios[key] = Math.round((prev[key] / otherTotal) * remaining);
          });
        }
      }

      return newRatios;
    });
  };

  const handleSplit = async () => {
    setIsSplitting(true);
    setSplittingResult(null);

    try {
      const payload = {
        input_file: inputFile,
        output_prefix: outputPrefix,
        train_ratio: splitRatios.train / 100,
        valid_ratio: splitRatios.valid / 100,
        test_ratio: splitRatios.test / 100,
        random_seed: randomSeed,
        shuffle: shuffleData,
        stratified,
      };

      // TODO: Replace with actual API call
      console.log('Split payload:', payload);

      // Simulate splitting
      await new Promise(resolve => setTimeout(resolve, 3000));

      setSplittingResult(
        `Successfully split ${inputFile} into:\n` +
          `• ${outputPrefix}_train.jsonl (${splitRatios.train}%)\n` +
          `• ${outputPrefix}_valid.jsonl (${splitRatios.valid}%)\n` +
          `• ${outputPrefix}_test.jsonl (${splitRatios.test}%)`
      );
    } catch (error) {
      setSplittingResult(`Error: ${error}`);
    } finally {
      setIsSplitting(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          ✂️ Split Data
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Randomly split JSONL task files into train/valid/test sets for machine
          learning workflows
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Splitting Configuration
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            This tool randomly splits your task dataset into training,
            validation, and test sets while maintaining data integrity.
          </Alert>

          {/* File Configuration */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Input File"
                value={inputFile}
                onChange={e => setInputFile(e.target.value)}
                placeholder="data/all_tasks.jsonl"
                helperText="Path to input JSONL file to split"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Output Prefix"
                value={outputPrefix}
                onChange={e => setOutputPrefix(e.target.value)}
                placeholder="data/split"
                helperText="Prefix for output files (will add _train, _valid, _test)"
                required
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* Split Ratios */}
          <Typography variant="subtitle1" gutterBottom>
            Split Ratios (%)
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Box sx={{ px: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Training Set: {splitRatios.train}%
                </Typography>
                <Slider
                  value={splitRatios.train}
                  onChange={(_, value) =>
                    handleRatioChange('train', value as number)
                  }
                  min={10}
                  max={80}
                  valueLabelDisplay="auto"
                  color="primary"
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ px: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Validation Set: {splitRatios.valid}%
                </Typography>
                <Slider
                  value={splitRatios.valid}
                  onChange={(_, value) =>
                    handleRatioChange('valid', value as number)
                  }
                  min={5}
                  max={30}
                  valueLabelDisplay="auto"
                  color="secondary"
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ px: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Test Set: {splitRatios.test}%
                </Typography>
                <Slider
                  value={splitRatios.test}
                  onChange={(_, value) =>
                    handleRatioChange('test', value as number)
                  }
                  min={5}
                  max={30}
                  valueLabelDisplay="auto"
                  color="warning"
                />
              </Box>
            </Grid>
          </Grid>

          {/* Validation */}
          {splitRatios.train + splitRatios.valid + splitRatios.test !== 100 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Split ratios must sum to 100%. Current total:{' '}
              {splitRatios.train + splitRatios.valid + splitRatios.test}%
            </Alert>
          )}

          <Divider sx={{ my: 3 }} />

          {/* Advanced Options */}
          <Typography variant="subtitle1" gutterBottom>
            Advanced Options
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Random Seed"
                value={randomSeed}
                onChange={e => setRandomSeed(parseInt(e.target.value) || 42)}
                helperText="Seed for reproducible random splits"
                inputProps={{ min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ pt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={shuffleData}
                      onChange={e => setShuffleData(e.target.checked)}
                    />
                  }
                  label="Shuffle Data"
                />
                <Typography variant="body2" color="text.secondary">
                  Randomly shuffle data before splitting
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={stratified}
                  onChange={e => setStratified(e.target.checked)}
                />
              }
              label="Stratified Splitting"
            />
            <Typography variant="body2" color="text.secondary">
              Maintain class distribution across splits (if applicable)
            </Typography>
          </Box>

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
              Upload File
            </Button>
            <Button
              variant="contained"
              onClick={handleSplit}
              disabled={
                isSplitting ||
                !inputFile ||
                !outputPrefix ||
                splitRatios.train + splitRatios.valid + splitRatios.test !== 100
              }
              startIcon={isSplitting ? <Shuffle /> : <SplitIcon />}
              size="large"
            >
              {isSplitting ? 'Splitting...' : 'Split Dataset'}
            </Button>
          </Box>

          {/* Splitting Result */}
          {splittingResult && (
            <Box sx={{ mt: 3 }}>
              <Alert
                severity={
                  splittingResult.includes('Error') ? 'error' : 'success'
                }
                sx={{ mb: 2 }}
              >
                <pre style={{ margin: 0, fontFamily: 'inherit' }}>
                  {splittingResult}
                </pre>
              </Alert>

              {!splittingResult.includes('Error') && (
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={() => console.log('Download train set')}
                    >
                      Download Train
                    </Button>
                  </Grid>
                  <Grid item xs={4}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={() => console.log('Download valid set')}
                    >
                      Download Valid
                    </Button>
                  </Grid>
                  <Grid item xs={4}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={() => console.log('Download test set')}
                    >
                      Download Test
                    </Button>
                  </Grid>
                </Grid>
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
            Splitting Guidelines
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            Recommended Split Ratios:
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  Small Dataset (&lt;1K)
                </Typography>
                <Typography variant="body2">
                  60% Train, 20% Valid, 20% Test
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  Medium Dataset (1K-10K)
                </Typography>
                <Typography variant="body2">
                  70% Train, 15% Valid, 15% Test
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  Large Dataset (&gt;10K)
                </Typography>
                <Typography variant="body2">
                  80% Train, 10% Valid, 10% Test
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Always use the same random seed for reproducible results across
            experiments.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default DataSplitter;
