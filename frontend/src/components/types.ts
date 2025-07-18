// Shared types for MCP server configuration across different pages

export interface ServerConfig {
  path: string;
  args: string[];
  env: { [key: string]: string };
}

// For MCPChatClient which has additional properties
export interface MCPServer extends ServerConfig {
  id: string;
  name: string;
  type: 'local' | 'npm';
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  tools?: Tool[];
  error?: string;
}

export interface Tool {
  name: string;
  description: string;
  inputSchema?: any;
}

// Utility functions for environment variable parsing
export const parseEnvString = (
  envString: string
): { [key: string]: string } => {
  const env: { [key: string]: string } = {};

  if (envString.trim()) {
    // Parse environment variables in format: KEY1=value1,KEY2=value2
    const envPairs = envString
      .split(',')
      .map(pair => pair.trim())
      .filter(pair => pair);
    envPairs.forEach(pair => {
      const [key, ...valueParts] = pair.split('=');
      if (key && valueParts.length > 0) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    });
  }

  return env;
};

export const formatEnvString = (env: { [key: string]: string }): string => {
  return Object.entries(env)
    .map(([key, value]) => `${key}=${value}`)
    .join(', ');
};
