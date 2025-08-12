import React from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  IconButton,
  Tooltip,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [pasteOpen, setPasteOpen] = React.useState(false);
  const [pasteValue, setPasteValue] = React.useState('');
  const [pasteError, setPasteError] = React.useState<string | null>(null);

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

  const normalizeServersFromJson = (data: unknown): ServerConfig[] | null => {
    try {
      const pickPackageFromArgs = (args: any[]): string | null => {
        for (const a of args) {
          const s = String(a);
          if (s.startsWith('@')) return s; // npm scoped package
          if (/mcp/i.test(s)) return s; // heuristic: contains mcp
        }
        return args.length > 0 ? String(args[args.length - 1]) : null;
      };

      const asArrayIfPresent = (obj: any): any[] | null => {
        if (Array.isArray(obj)) return obj;
        if (obj && Array.isArray(obj.servers)) return obj.servers;
        return null;
      };

      // Case 1: array or { servers: [...] }
      const rawListOrNull = asArrayIfPresent(data as any);
      if (rawListOrNull) {
        const normalized: ServerConfig[] = rawListOrNull.map((item: any) => {
          if (typeof item === 'string') {
            return { path: item, args: [], env: {} } as ServerConfig;
          }
          const path: string = String(item.path || '').trim();
          const args: string[] = Array.isArray(item.args)
            ? item.args.map((a: any) => String(a))
            : typeof item.args === 'string'
              ? String(item.args)
                  .split(' ')
                  .map(s => s.trim())
                  .filter(Boolean)
              : [];
          const env: Record<string, string> = item.env && typeof item.env === 'object' ? Object.fromEntries(
            Object.entries(item.env).map(([k, v]) => [k, String(v)])
          ) : {};

          if (!path) {
            throw new Error('Each server must have a non-empty path');
          }
          return { path, args, env } as ServerConfig;
        });
        return normalized;
      }

      // Case 2: { mcpServers: { name: { command, args, env } | { url } } }
      const obj = data as any;
      if (obj && obj.mcpServers && typeof obj.mcpServers === 'object') {
        const normalized: ServerConfig[] = [];
        for (const [_name, cfg] of Object.entries<any>(obj.mcpServers)) {
          if (!cfg || typeof cfg !== 'object') continue;
          let path = '';
          let args: string[] = [];
          const env: Record<string, string> = cfg.env && typeof cfg.env === 'object' ? Object.fromEntries(
            Object.entries(cfg.env).map(([k, v]) => [k, String(v)])
          ) : {};

          if (typeof cfg.url === 'string' && cfg.url.trim()) {
            path = cfg.url.trim();
          } else if (Array.isArray(cfg.args)) {
            const pkg = pickPackageFromArgs(cfg.args);
            if (pkg) path = pkg.trim();
            // We intentionally do not forward npx flags like -y as server args.
            // If cfg.serverArgs is provided in future, we could merge them here.
            args = [];
          }

          if (path) normalized.push({ path, args, env });
        }
        if (normalized.length > 0) return normalized;
      }

      return null;
    } catch (err) {
      console.error('Failed to normalize MCP servers JSON:', err);
      return null;
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      const normalized = normalizeServersFromJson(json);
      if (!normalized || normalized.length === 0) {
        window.alert('Invalid MCP servers JSON. Expected { "servers": [...] } or an array.');
        return;
      }
      onServersChange(normalized);
    } catch (err: any) {
      console.error('Error importing MCP servers JSON:', err);
      window.alert(`Failed to import JSON: ${err?.message || String(err)}`);
    } finally {
      // Reset input so importing the same file again triggers change
      if (e.target) e.target.value = '';
    }
  };

  const handleExport = () => {
    const payload = { servers };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mcp_servers.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleOpenPaste = () => {
    setPasteValue('');
    setPasteError(null);
    setPasteOpen(true);
  };

  const handleClosePaste = () => {
    setPasteOpen(false);
    setPasteError(null);
  };

  const handleApplyPaste = () => {
    try {
      setPasteError(null);
      const json = JSON.parse(pasteValue);
      const normalized = normalizeServersFromJson(json);
      if (!normalized || normalized.length === 0) {
        setPasteError('Invalid MCP servers JSON. Expected an array, { "servers": [...] }, or { "mcpServers": { ... } }');
        return;
      }
      onServersChange(normalized);
      setPasteOpen(false);
    } catch (err: any) {
      setPasteError(err?.message || 'Failed to parse JSON');
    }
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
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <Tooltip title="Paste servers from JSON content">
            <span>
              <Button size="small" variant="outlined" onClick={handleOpenPaste}>
                Paste JSON
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="Import servers from JSON">
            <span>
              <Button size="small" variant="outlined" onClick={handleImportClick}>
                Import JSON
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="Export current servers to JSON">
            <span>
              <Button size="small" variant="outlined" onClick={handleExport}>
                Export JSON
              </Button>
            </span>
          </Tooltip>
          {showAddButton && (
            <Tooltip title="Add another server">
              <IconButton onClick={addServer} color="primary">
                <AddIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      <Dialog open={pasteOpen} onClose={handleClosePaste} maxWidth="md" fullWidth>
        <DialogTitle>Paste MCP Servers JSON</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            multiline
            minRows={10}
            fullWidth
            placeholder='{"servers": [...]} or {"mcpServers": {...}}'
            value={pasteValue}
            onChange={e => setPasteValue(e.target.value)}
            error={!!pasteError}
            helperText={pasteError || 'Paste your JSON and click Apply'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePaste}>Cancel</Button>
          <Button variant="contained" onClick={handleApplyPaste}>Apply</Button>
        </DialogActions>
      </Dialog>

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
