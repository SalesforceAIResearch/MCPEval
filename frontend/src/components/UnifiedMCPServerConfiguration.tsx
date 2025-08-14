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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { ServerConfig, MCPServer, parseEnvString, formatEnvString, Tool } from './types';
import { mapJsonConfigToServers } from '../utils/mcpConfig';

type EditableServer = (ServerConfig & {
  id?: string;
  name?: string;
  type?: 'local' | 'npm' | 'http';
  status?: MCPServer['status'];
  tools?: Tool[];
  error?: string;
});

interface UnifiedMCPServerConfigurationProps {
  servers: EditableServer[];
  onServersChange: (servers: EditableServer[]) => void;
  title?: string;
  subtitle?: string;
  showAddButton?: boolean;
  allowRemove?: boolean;
  required?: boolean;
}

const UnifiedMCPServerConfiguration: React.FC<UnifiedMCPServerConfigurationProps> = ({
  servers,
  onServersChange,
  title = 'MCP Servers',
  subtitle = 'Configure servers',
  showAddButton = true,
  allowRemove = true,
  required = false,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [pasteOpen, setPasteOpen] = React.useState(false);
  const [pasteValue, setPasteValue] = React.useState('');
  const [pasteError, setPasteError] = React.useState<string | null>(null);

  const inferTypeFromPath = (path: string): 'local' | 'npm' | 'http' => {
    if (!path) return 'local';
    if (path.startsWith('http://') || path.startsWith('https://')) return 'http';
    if (path.startsWith('@')) return 'npm';
    return 'local';
  };

  const ensureEditable = (s: Partial<EditableServer>): EditableServer => {
    const path = (s.path || '').trim();
    return {
      id: s.id,
      name: s.name || '',
      type: s.type || inferTypeFromPath(path),
      path,
      args: Array.isArray(s.args) ? (s.args as string[]) : [],
      env: s.env || {},
      status: s.status,
      tools: s.tools,
      error: s.error,
    } as EditableServer;
  };

  const addServer = () => {
    const newServers = [
      ...servers,
      ensureEditable({ path: '', args: [], env: {}, name: '', type: 'local' }),
    ];
    onServersChange(newServers);
  };

  const removeServer = (index: number) => {
    const newServers = servers.filter((_, i) => i !== index);
    onServersChange(newServers);
  };

  const updateServer = (index: number, updates: Partial<EditableServer>) => {
    const newServers = [...servers];
    newServers[index] = ensureEditable({ ...newServers[index], ...updates });
    onServersChange(newServers);
  };

  const normalizeServersFromJson = (data: unknown): EditableServer[] | null => {
    try {
      // First, try the shared mapper that supports array, {servers: [...]}, and {mcpServers: {...}}
      const mapped = mapJsonConfigToServers(data);
      if (Array.isArray(mapped) && mapped.length > 0) {
        return mapped.map(ms => ensureEditable({
          name: ms.name || '',
          path: ms.path,
          args: ms.args,
          env: ms.env,
          type: ms.type,
        }));
      }

      const coerceEnv = (env: any): Record<string, string> => {
        if (!env || typeof env !== 'object') return {};
        return Object.fromEntries(Object.entries(env).map(([k, v]) => [k, String(v)]));
      };

      const fromArrayLike = (arr: any[]): EditableServer[] =>
        arr.map((item: any) => {
          if (typeof item === 'string') {
            const path = String(item).trim();
            return ensureEditable({ path, args: [], env: {}, name: '', type: inferTypeFromPath(path) });
          }
          const path = String(item.path || '').trim();
          const args: string[] = Array.isArray(item.args)
            ? item.args.map((a: any) => String(a))
            : typeof item.args === 'string'
              ? String(item.args)
                  .split(/[\s,]+/)
                  .map(s => s.trim())
                  .filter(Boolean)
              : [];
          const env = coerceEnv(item.env);
          const name = item.name ? String(item.name) : '';
          const type: 'local' | 'npm' | 'http' = item.type && ['local', 'npm', 'http'].includes(String(item.type))
            ? String(item.type) as any
            : inferTypeFromPath(path);
          const status = (['disconnected','connecting','connected','error'].includes(String(item.status))
            ? String(item.status)
            : undefined) as MCPServer['status'] | undefined;
          const tools: Tool[] | undefined = Array.isArray(item.tools)
            ? item.tools.map((t: any) => ({ name: String(t.name), description: String(t.description || ''), inputSchema: t.inputSchema }))
            : undefined;
          const error = item.error ? String(item.error) : undefined;
          const id = item.id ? String(item.id) : undefined;
          if (!path) throw new Error('Each server must have a non-empty path');
          return ensureEditable({ id, name, type, path, args, env, status, tools, error });
        });

      // Case A: array or { servers: [...] }
      if (Array.isArray(data)) return fromArrayLike(data);
      if (data && typeof data === 'object' && Array.isArray((data as any).servers)) {
        return fromArrayLike((data as any).servers);
      }

      // Case B: { mcpServers: { name: { command, args, env } | { url } } }
      const obj = data as any;
      if (obj && obj.mcpServers && typeof obj.mcpServers === 'object') {
        const normalized: EditableServer[] = [];
        for (const [name, cfg] of Object.entries<any>(obj.mcpServers)) {
          if (!cfg || typeof cfg !== 'object') continue;
          let path = '';
          let args: string[] = [];
          const env = coerceEnv(cfg.env);
          if (typeof cfg.url === 'string' && cfg.url.trim()) {
            path = cfg.url.trim();
          } else if (Array.isArray(cfg.args)) {
            // try to pick an npm package from args or last arg as path
            const pick = (arr: any[]) => {
              for (const a of arr) {
                const s = String(a);
                if (s.startsWith('@')) return s;
                if (/mcp/i.test(s)) return s;
              }
              return arr.length > 0 ? String(arr[arr.length - 1]) : '';
            };
            const pkg = pick(cfg.args);
            if (pkg) path = pkg.trim();
            args = [];
          }
          if (path) {
            normalized.push(
              ensureEditable({ name: String(name), path, args, env, type: inferTypeFromPath(path) })
            );
          }
        }
        if (normalized.length > 0) return normalized;
      }

      return null;
    } catch (err) {
      console.error('Failed to normalize MCP servers JSON:', err);
      return null;
    }
  };

  const handleImportClick = () => fileInputRef.current?.click();

  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      const normalized = normalizeServersFromJson(json);
      if (!normalized || normalized.length === 0) {
        window.alert('Invalid MCP servers JSON. Expected an array, { "servers": [...] }, or { "mcpServers": { ... } }');
        return;
      }
      onServersChange(normalized);
    } catch (err: any) {
      console.error('Error importing MCP servers JSON:', err);
      window.alert(`Failed to import JSON: ${err?.message || String(err)}`);
    } finally {
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

  const getStatusColor = (status?: MCPServer['status']) => {
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
            <Typography variant="body2" sx={{ fontWeight: 'bold', flexGrow: 1 }}>
              Server {index + 1}
            </Typography>
            {server.status && (
              <Chip
                label={server.status}
                size="small"
                color={getStatusColor(server.status) as any}
                sx={{ mr: 1 }}
              />
            )}
            {allowRemove && servers.length > 1 && (
              <IconButton onClick={() => removeServer(index)} color="error" size="small">
                <DeleteIcon />
              </IconButton>
            )}
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Server Name (Optional)"
                value={server.name || ''}
                onChange={e => updateServer(index, { name: e.target.value })}
                placeholder="e.g., YFinance Server"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Server Type</InputLabel>
                <Select
                  value={server.type || inferTypeFromPath(server.path)}
                  label="Server Type"
                  onChange={e => updateServer(index, { type: e.target.value as any })}
                >
                  <MenuItem value="local">Local Server (.py file)</MenuItem>
                  <MenuItem value="npm">NPM Package</MenuItem>
                  <MenuItem value="http">HTTP Server</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Server Path"
                value={server.path}
                onChange={e => updateServer(index, { path: e.target.value })}
                placeholder="mcp_servers/healthcare/server.py or @modelcontextprotocol/server-name or http://..."
                size="small"
                required={required}
                helperText="Path to local server script, NPM package name, or HTTP URL"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Server Arguments (Optional)"
                value={(server.args || []).join(' ')}
                onChange={e => updateServer(index, { args: e.target.value.split(' ').filter(a => a.trim()) })}
                placeholder="--debug --timeout 30"
                size="small"
                helperText="Space-separated arguments"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Environment Variables (Optional)"
                value={formatEnvString(server.env || {})}
                onChange={e => updateServer(index, { env: parseEnvString(e.target.value) })}
                placeholder="API_KEY=secret123, DEBUG=true"
                size="small"
                helperText="Format: KEY1=value1, KEY2=value2"
              />
            </Grid>
          </Grid>

          {server.env && Object.keys(server.env).length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
                Environment Variables:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(server.env).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}=${String(value).length > 10 ? String(value).substring(0, 10) + '...' : String(value)}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                ))}
              </Box>
            </Box>
          )}

          {server.tools && server.tools.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
                Available Tools ({server.tools.length}):
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {server.tools.map((tool, idx) => (
                  <Tooltip key={idx} title={tool.description}>
                    <Chip label={tool.name} size="small" variant="outlined" />
                  </Tooltip>
                ))}
              </Box>
            </Box>
          )}

          {server.error && (
            <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
              Error: {server.error}
            </Typography>
          )}
        </Box>
      ))}
    </Box>
  );
};

export default UnifiedMCPServerConfiguration;


