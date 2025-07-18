import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import TaskGenerator from './pages/TaskGenerator';
import TaskVerifier from './pages/TaskVerifier';
import DataConverter from './pages/DataConverter';
import DataSplitter from './pages/DataSplitter';
import ModelEvaluator from './pages/ModelEvaluator';
import Analyzer from './pages/Analyzer';
import LLMJudger from './pages/LLMJudger';
import JudgeRubric from './pages/JudgeRubric';
import Results from './pages/Results';
import ServerFiles from './pages/ServerFiles';
import BackendFiles from './pages/BackendFiles';
import DataFiles from './pages/DataFiles';
import MCPChatClient from './pages/MCPChatClient';
import AutoWorkflow from './pages/AutoWorkflow';
import DebugJobs from './pages/DebugJobs';
import ReportGenerator from './pages/ReportGenerator';
import Activities from './pages/Activities';
import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#9c27b0',
      light: '#ba68c8',
      dark: '#7b1fa2',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#1976d2',
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '12px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Sidebar />
          <Box
            component="main"
            sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}
          >
            <Header />
            <Box
              sx={{ flexGrow: 1, p: 3, backgroundColor: 'background.default' }}
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/generate-tasks" element={<TaskGenerator />} />
                <Route path="/verify-tasks" element={<TaskVerifier />} />
                <Route path="/convert-data" element={<DataConverter />} />
                <Route path="/split-data" element={<DataSplitter />} />
                <Route path="/evaluate" element={<ModelEvaluator />} />
                <Route path="/analyze" element={<Analyzer />} />
                <Route path="/judge" element={<LLMJudger />} />
                <Route path="/judge-rubric" element={<JudgeRubric />} />
                <Route path="/results" element={<Results />} />
                <Route path="/server-files" element={<ServerFiles />} />
                <Route path="/backend-files" element={<BackendFiles />} />
                <Route path="/data-files" element={<DataFiles />} />
                <Route path="/mcp-chat" element={<MCPChatClient />} />
                <Route path="/auto-workflow" element={<AutoWorkflow />} />
                <Route path="/debug-jobs" element={<DebugJobs />} />
                <Route path="/generate-report" element={<ReportGenerator />} />
                <Route path="/activities" element={<Activities />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
