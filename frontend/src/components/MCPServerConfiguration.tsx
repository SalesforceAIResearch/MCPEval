import React from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { ServerConfig, parseEnvString, formatEnvString } from './types';

interface MCPServerConfigurationProps {
  servers: ServerConfig[];
  onServersChange: (servers: ServerConfig[]) => void;
  title?: string;
  subtitle?: string;
  showAddButton?: boolean;
  allowRemove?: boolean;
  required?: boolean;
}

const MCPServerConfiguration: React.FC<MCPServerConfigurationProps> = ({
  servers,
  onServersChange,
  title = 'MCP Servers',
  subtitle = 'Configure servers for task processing',
  showAddButton = true,
  allowRemove = true,
  required = false,
}) => {
  const addServer = () => {
    const newServers = [...servers, { path: '', args: [], env: {} }];
    onServersChange(newServers);
  };

  const removeServer = (index: number) => {
    const newServers = servers.filter((_, i) => i !== index);
    onServersChange(newServers);
  };

  const updateServerPath = (index: number, path: string) => {
    const newServers = [...servers];
    newServers[index].path = path;
    onServersChange(newServers);
  };

  const updateServerArgs = (index: number, argsString: string) => {
    const newServers = [...servers];
    newServers[index].args = argsString.split(' ').filter(arg => arg.trim());
    onServersChange(newServers);
  };

  const updateServerEnv = (index: number, envString: string) => {
    const newServers = [...servers];
    newServers[index].env = parseEnvString(envString);
    onServersChange(newServers);
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1" gutterBottom>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        {showAddButton && (
          <Tooltip title="Add another server">
            <IconButton onClick={addServer} color="primary">
              <AddIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {servers.map((server, index) => (
        <Box
          key={index}
          sx={{
            mb: 2,
            p: 2,
            border: '1px solid #e0e0e0',
            borderRadius: 1,
            backgroundColor: '#fafafa',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography
              variant="body2"
              sx={{ fontWeight: 'bold', flexGrow: 1 }}
            >
              Server {index + 1}
            </Typography>
            {allowRemove && servers.length > 1 && (
              <IconButton
                onClick={() => removeServer(index)}
                color="error"
                size="small"
              >
                <DeleteIcon />
              </IconButton>
            )}
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Server Path"
                value={server.path}
                onChange={e => updateServerPath(index, e.target.value)}
                placeholder="mcp_servers/healthcare/server.py or @modelcontextprotocol/server-name"
                size="small"
                required={required}
                helperText="Path to local server script, NPM package name, or HTTP URL"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Server Arguments (Optional)"
                value={server.args.join(' ')}
                onChange={e => updateServerArgs(index, e.target.value)}
                placeholder="--debug --timeout 30"
                size="small"
                helperText="Space-separated arguments"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Environment Variables (Optional)"
                value={formatEnvString(server.env)}
                onChange={e => updateServerEnv(index, e.target.value)}
                placeholder="API_KEY=secret123, DEBUG=true"
                size="small"
                helperText="Format: KEY1=value1, KEY2=value2"
              />
            </Grid>
          </Grid>

          {/* Show current environment variables as chips */}
          {server.env && Object.keys(server.env).length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography
                variant="body2"
                sx={{ mb: 1, color: 'text.secondary' }}
              >
                Environment Variables:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(server.env).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}=${value.length > 10 ? value.substring(0, 10) + '...' : value}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      ))}
    </Box>
  );
};

export default MCPServerConfiguration;
