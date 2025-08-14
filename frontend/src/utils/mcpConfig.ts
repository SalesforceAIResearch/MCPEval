import { ServerConfig } from '../components/types';

export type ServerType = 'local' | 'npm' | 'http';

export interface MappedServer extends ServerConfig {
  name?: string;
  type: ServerType;
}

export const inferTypeFromPath = (path: string): ServerType => {
  if (!path) return 'local';
  if (path.startsWith('http://') || path.startsWith('https://')) return 'http';
  if (path.startsWith('@')) return 'npm';
  const looksLikeBareNpm = !path.includes('/') && !path.includes('\\') && !path.includes('.') && /mcp/i.test(path);
  if (looksLikeBareNpm) return 'npm';
  return 'local';
};

const coerceEnv = (env: unknown): Record<string, string> => {
  if (!env || typeof env !== 'object') return {};
  return Object.fromEntries(
    Object.entries(env as Record<string, unknown>).map(([k, v]) => [k, String(v)])
  );
};

/**
 * Map a variety of JSON shapes (array, { servers: [...] }, { mcpServers: {...} })
 * into a normalized list of frontend server configs.
 */
export const mapJsonConfigToServers = (data: unknown): MappedServer[] => {
  const ensureMapped = (partial: Partial<MappedServer>): MappedServer => {
    const path = (partial.path || '').trim();
    return {
      name: partial.name?.trim() || undefined,
      type: (partial.type as ServerType) || inferTypeFromPath(path),
      path,
      args: Array.isArray(partial.args) ? partial.args as string[] : [],
      env: partial.env || {},
    };
  };

  const fromArrayLike = (arr: any[]): MappedServer[] =>
    arr.map((item: any) => {
      if (typeof item === 'string') {
        const path = String(item).trim();
        return ensureMapped({ path });
      }
      const path = String(item.path || '').trim();
      const args: string[] = Array.isArray(item.args)
        ? item.args.map((a: any) => String(a))
        : [];
      const env = coerceEnv(item.env);
      const name = item.name ? String(item.name) : undefined;
      const type: ServerType = item.type && ['local', 'npm', 'http'].includes(String(item.type))
        ? String(item.type) as ServerType
        : inferTypeFromPath(path);
      if (!path) throw new Error('Each server must have a non-empty path');
      return ensureMapped({ name, type, path, args, env });
    });

  // Case A: array or { servers: [...] }
  if (Array.isArray(data)) return fromArrayLike(data);
  if (data && typeof data === 'object' && Array.isArray((data as any).servers)) {
    return fromArrayLike((data as any).servers);
  }

  // Case B: { mcpServers: { name: { command, args, env, transport } | { url, headers } } }
  const obj = data as any;
  if (obj && obj.mcpServers && typeof obj.mcpServers === 'object') {
    const normalized: MappedServer[] = [];
    for (const [name, cfg] of Object.entries<any>(obj.mcpServers)) {
      if (!cfg || typeof cfg !== 'object') continue;

      let path = '';
      let args: string[] = [];
      const env = coerceEnv(cfg.env);
      const transport = typeof cfg.transport === 'string' ? String(cfg.transport).toLowerCase() : undefined;
      const command = typeof cfg.command === 'string' ? String(cfg.command).toLowerCase() : undefined;

      // Prefer explicit URL when provided (HTTP/SSE)
      if (typeof cfg.url === 'string' && cfg.url.trim()) {
        path = cfg.url.trim();
      } else if (Array.isArray(cfg.args)) {
        // Extract npm package from npx-style args
        const rawArgs = (cfg.args as any[]).map((a: any) => String(a).trim()).filter((v: string) => Boolean(v));
        let pkgIndex = -1;
        for (let i = 0; i < rawArgs.length; i++) {
          const s = rawArgs[i];
          if (s.startsWith('-')) continue;
          if (s.startsWith('@') || (/mcp/i.test(s) && !s.includes('.') && !s.includes('/') && !s.includes('\\'))) {
            pkgIndex = i;
            break;
          }
        }
        if (pkgIndex >= 0) {
          path = rawArgs[pkgIndex];
          args = rawArgs.slice(pkgIndex + 1).filter(a => !a.startsWith('--transport='));
        } else if (rawArgs.length > 0) {
          path = rawArgs[rawArgs.length - 1];
          args = [];
        }
      }

      if (!path) continue;

      let type: ServerType;
      if (transport && (transport.includes('http') || transport === 'sse')) {
        type = 'http';
      } else if (command === 'npx') {
        type = 'npm';
      } else {
        type = inferTypeFromPath(path);
      }

      normalized.push(ensureMapped({ name: String(name), path, args, env, type }));
    }
    return normalized;
  }

  return [];
};


