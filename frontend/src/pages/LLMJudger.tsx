import React, { useState } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
} from '@mui/material';
import { Gavel as JudgeIcon } from '@mui/icons-material';

const LLMJudger: React.FC = () => {
  const [evaluationFile, setEvaluationFile] = useState('');

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🧠 LLM Judge
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Evaluate execution results using LLM judges for automated assessment
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            AI-powered evaluation of task execution quality and correctness
          </Alert>

          <TextField
            fullWidth
            label="Evaluation Results File"
            value={evaluationFile}
            onChange={e => setEvaluationFile(e.target.value)}
            placeholder="data/evaluation_results.json"
            sx={{ mb: 3 }}
          />

          <Button variant="contained" startIcon={<JudgeIcon />} size="large">
            Start LLM Judging
          </Button>
        </CardContent>
      </Card>
    </Container>
  );
};

export default LLMJudger;
