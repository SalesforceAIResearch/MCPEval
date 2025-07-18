import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  IconButton,
  Chip,
  Tooltip,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { MCPServer } from './types';

interface MCPChatServerConfigurationProps {
  servers: MCPServer[];
  onRemoveServer: (serverId: string) => void;
}

const MCPChatServerConfiguration: React.FC<MCPChatServerConfigurationProps> = ({
  servers,
  onRemoveServer,
}) => {
  const getServerStatusColor = (status: MCPServer['status']) => {
    switch (status) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {servers.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No servers configured. Add a server to get started.
        </Typography>
      ) : (
        <List>
          {servers.map(server => (
            <ListItem key={server.id}>
              <Box sx={{ width: '100%' }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box>
                    <Typography
                      variant="subtitle1"
                      sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                    >
                      {server.name}
                      <Chip
                        label={server.type}
                        size="small"
                        color={
                          server.type === 'local' ? 'primary' : 'secondary'
                        }
                      />
                      <Chip
                        label={server.status}
                        size="small"
                        color={getServerStatusColor(server.status)}
                      />
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {server.path}
                    </Typography>
                    {server.args.length > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        Args: {server.args.join(', ')}
                      </Typography>
                    )}
                    {server.env && Object.keys(server.env).length > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        Env:{' '}
                        {Object.entries(server.env)
                          .map(
                            ([key, value]) =>
                              `${key}=${value.length > 10 ? value.substring(0, 10) + '...' : value}`
                          )
                          .join(', ')}
                      </Typography>
                    )}
                    {server.error && (
                      <Typography variant="caption" color="error">
                        Error: {server.error}
                      </Typography>
                    )}
                  </Box>

                  <IconButton
                    onClick={() => onRemoveServer(server.id)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>

                {server.tools && server.tools.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Available Tools ({server.tools.length}):
                    </Typography>
                    <Box
                      sx={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: 0.5,
                        mt: 0.5,
                      }}
                    >
                      {server.tools.map((tool, index) => (
                        <Tooltip key={index} title={tool.description}>
                          <Chip
                            label={tool.name}
                            size="small"
                            variant="outlined"
                          />
                        </Tooltip>
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
};

export default MCPChatServerConfiguration;
