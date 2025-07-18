import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Paper,
  Breadcrumbs,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Snackbar,
  Checkbox,
  FormControlLabel,
  TextField,
  Fab,
  Backdrop,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import {
  Storage as StorageIcon,
  Refresh as RefreshIcon,
  InsertDriveFile as FileIcon,
  Folder as FolderIcon,
  Schedule as ScheduleIcon,
  GetApp as DownloadIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
  Home as HomeIcon,
  DataObject as DataIcon,
  ContentCopy as CopyIcon,
  Delete as DeleteIcon,
  Merge as MergeIcon,
  SelectAll as SelectAllIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';

interface DataFile {
  name: string;
  path: string;
  size: number;
  modified: string;
  details?: {
    taskCount?: number;
    recordCount?: number;
    lineCount?: number;
    type?: string;
  };
}

interface DirectoryInfo {
  name: string;
  path: string;
  fileCount: number;
  totalSize: number;
  lastModified: string;
}

const DataFiles: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [files, setFiles] = useState<DataFile[]>([]);
  const [directories, setDirectories] = useState<DirectoryInfo[]>([]);
  const [currentPath, setCurrentPath] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<DataFile | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [highlightedFile, setHighlightedFile] = useState<string | null>(null);

  // File selection and processing states
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [selectionMode, setSelectionMode] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [mergeFileName, setMergeFileName] = useState('');
  const [processing, setProcessing] = useState(false);

  const fetchData = async (path: string = '') => {
    try {
      setLoading(true);
      setError(null);

      const endpoint = path
        ? `/api/files?directory=${encodeURIComponent(path)}`
        : '/api/files?directory=data';
      const response = await fetch(endpoint);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch data files');
      }

      const files = data.files || [];
      setFiles(files);

      // Fetch subdirectories for both root and domain directories
      if (!path || path === 'data') {
        await fetchDirectories('data');
      } else {
        // Check if this is a domain directory (not a stage directory)
        const isStageDir =
          path.includes('/tasks') ||
          path.includes('/verified_tasks') ||
          path.includes('/evaluations') ||
          path.includes('/judging') ||
          path.includes('/reports') ||
          path.includes('/analysis');

        if (!isStageDir) {
          await fetchDirectories(path);
        }
      }

      // Fetch file details for JSON/JSONL files
      if (files.length > 0) {
        setDetailsLoading(true);
        try {
          const filesWithDetails = await Promise.all(
            files.map(async (file: DataFile) => {
              if (
                file.name.endsWith('.json') ||
                file.name.endsWith('.jsonl') ||
                file.name.endsWith('.md')
              ) {
                const details = await fetchFileDetails(file);
                return { ...file, details };
              }
              return file;
            })
          );
          setFiles(filesWithDetails);
        } catch (err) {
          console.error('Error fetching file details:', err);
        } finally {
          setDetailsLoading(false);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch data files'
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchDirectories = async (path: string = 'data') => {
    try {
      // Use the new API endpoint to get all directories under the specified path
      const response = await fetch(
        `/api/directories?directory=${encodeURIComponent(path)}`
      );
      const data = await response.json();

      if (response.ok && data.directories) {
        // Convert the directory data to match our expected format
        const dirInfos: DirectoryInfo[] = data.directories.map((dir: any) => ({
          name: dir.name,
          path: dir.path,
          fileCount: dir.fileCount,
          totalSize: dir.totalSize,
          lastModified: dir.lastModified,
        }));

        setDirectories(dirInfos);
      } else {
        console.error('Failed to fetch directories:', data.error);
      }
    } catch (err) {
      console.error('Error fetching directories:', err);
    }
  };

  const fetchFileDetails = async (
    file: DataFile
  ): Promise<DataFile['details']> => {
    try {
      const response = await fetch(
        `/api/file-content/${encodeURIComponent(file.path)}`
      );
      const data = await response.json();

      if (!response.ok) {
        return undefined;
      }

      const content = data.content;
      if (!content) return undefined;

      const details: DataFile['details'] = {};

      // Count lines
      const lines = content.split('\n').filter((line: string) => line.trim());
      details.lineCount = lines.length;

      // For JSONL files (task files), count valid JSON objects
      if (file.name.endsWith('.jsonl')) {
        let taskCount = 0;
        let recordCount = 0;

        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            recordCount++;

            // Check if this looks like a task (has common task properties)
            if (
              parsed.task ||
              parsed.prompt ||
              parsed.description ||
              parsed.query ||
              parsed.instruction
            ) {
              taskCount++;
            }
          } catch {
            // Skip invalid JSON lines
          }
        }

        details.taskCount = taskCount;
        details.recordCount = recordCount;
        details.type = 'tasks';
      }

      // For JSON files, analyze structure
      else if (file.name.endsWith('.json')) {
        try {
          const parsed = JSON.parse(content);

          if (Array.isArray(parsed)) {
            details.recordCount = parsed.length;

            // Check if array contains task-like objects
            if (
              parsed.length > 0 &&
              parsed[0] &&
              typeof parsed[0] === 'object'
            ) {
              const sample = parsed[0];
              if (
                sample.task ||
                sample.prompt ||
                sample.description ||
                sample.query ||
                sample.instruction
              ) {
                details.taskCount = parsed.length;
                details.type = 'tasks';
              }
            }
          } else if (typeof parsed === 'object' && parsed !== null) {
            // Check if it's a single task object
            if (
              parsed.task ||
              parsed.prompt ||
              parsed.description ||
              parsed.query ||
              parsed.instruction
            ) {
              details.taskCount = 1;
              details.recordCount = 1;
              details.type = 'tasks';
            }
          }
        } catch {
          // Skip invalid JSON
        }
      }

      // For Markdown files, analyze content
      else if (file.name.endsWith('.md')) {
        // Count headers, paragraphs, and words
        const lines = content.split('\n');
        const headerCount = lines.filter((line: string) =>
          line.trim().startsWith('#')
        ).length;
        const paragraphs = content
          .split('\n\n')
          .filter((p: string) => p.trim()).length;
        const words = content
          .split(/\s+/)
          .filter((w: string) => w.trim()).length;

        details.recordCount = headerCount; // Use header count as record count for reports
        details.lineCount = lines.length;
        details.type = 'report';

        // Store additional markdown-specific info in a way that can be displayed
        if (words > 0) {
          details.taskCount = Math.round(words / 100); // Rough estimate: ~100 words per "section"
        }
      }

      return details;
    } catch {
      return undefined;
    }
  };

  const fetchFileContent = async (file: DataFile) => {
    try {
      setContentLoading(true);

      const response = await fetch(
        `/api/file-content/${encodeURIComponent(file.path)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch file content');
      }

      setFileContent(data.content);
      setSelectedFile(file);
      setViewDialogOpen(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch file content'
      );
    } finally {
      setContentLoading(false);
    }
  };

  const formatFileContent = (content: string, fileName: string) => {
    if (!content) return '';

    // Format JSONL files by parsing each line as JSON
    if (fileName.endsWith('.jsonl')) {
      try {
        const lines = content.split('\n').filter(line => line.trim());
        return lines
          .map(line => {
            try {
              const parsed = JSON.parse(line);
              return JSON.stringify(parsed, null, 2);
            } catch {
              return line; // Return original line if parsing fails
            }
          })
          .join('\n\n---\n\n');
      } catch {
        return content; // Return original if any error
      }
    }

    // Format regular JSON files
    if (fileName.endsWith('.json')) {
      try {
        const parsed = JSON.parse(content);
        return JSON.stringify(parsed, null, 2);
      } catch {
        return content; // Return original if parsing fails
      }
    }

    // For markdown files, return content as-is (will be rendered by ReactMarkdown)
    if (fileName.endsWith('.md')) {
      return content;
    }

    return content; // Return as-is for other file types
  };

  const renderFileContent = (content: string, fileName: string) => {
    if (!content) return null;

    // Render markdown files with ReactMarkdown
    if (fileName.endsWith('.md')) {
      return (
        <Box sx={{ p: 3, bgcolor: 'white', height: '100%', overflow: 'auto' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              // Custom image renderer to handle relative paths
              img: ({ src, alt, title }) => {
                // Convert relative image paths to absolute paths pointing to backend API
                let imageSrc = src;
                if (
                  src &&
                  selectedFile &&
                  !src.startsWith('http') &&
                  !src.startsWith('data:')
                ) {
                  // Get the directory path of the current file
                  const filePath = selectedFile.path;
                  const fileDir = filePath.substring(
                    0,
                    filePath.lastIndexOf('/')
                  );

                  // Handle relative paths
                  if (src.startsWith('./')) {
                    // Remove ./ prefix and join with file directory
                    const relativePath = src.substring(2);
                    imageSrc = `/api/download/${fileDir}/${relativePath}`;
                  } else if (src.startsWith('../')) {
                    // Handle ../ paths - go up one directory
                    const parts = fileDir.split('/');
                    parts.pop(); // Remove last directory
                    const relativePath = src.substring(3);
                    imageSrc = `/api/download/${parts.join('/')}/${relativePath}`;
                  } else if (!src.startsWith('/')) {
                    // Handle paths without prefix (treat as relative to current directory)
                    imageSrc = `/api/download/${fileDir}/${src}`;
                  }
                }

                return (
                  <Box
                    component="img"
                    src={imageSrc}
                    alt={alt}
                    title={title}
                    sx={{
                      maxWidth: '100%',
                      height: 'auto',
                      mb: 2,
                      border: '1px solid #e0e0e0',
                      borderRadius: 1,
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    }}
                    onError={e => {
                      // Handle image loading errors
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      // Create a replacement element
                      const replacement = document.createElement('div');
                      replacement.innerHTML = `
                        <div style="
                          border: 2px dashed #ccc; 
                          padding: 20px; 
                          text-align: center; 
                          color: #666;
                          margin: 16px 0;
                          border-radius: 4px;
                          background-color: #f9f9f9;
                        ">
                          <p style="margin: 0; font-size: 14px;">
                            📷 Image not found: ${alt || src}
                          </p>
                          <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">
                            Path: ${imageSrc}
                          </p>
                        </div>
                      `;
                      target.parentNode?.insertBefore(replacement, target);
                    }}
                  />
                );
              },
              // Custom styling for markdown elements
              h1: ({ children }) => (
                <Typography
                  variant="h4"
                  component="h1"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    borderBottom: '2px solid #e0e0e0',
                    pb: 1,
                  }}
                >
                  {children}
                </Typography>
              ),
              h2: ({ children }) => (
                <Typography
                  variant="h5"
                  component="h2"
                  gutterBottom
                  sx={{ color: 'primary.main', mt: 3, mb: 2 }}
                >
                  {children}
                </Typography>
              ),
              h3: ({ children }) => (
                <Typography
                  variant="h6"
                  component="h3"
                  gutterBottom
                  sx={{ color: 'primary.main', mt: 2, mb: 1 }}
                >
                  {children}
                </Typography>
              ),
              h4: ({ children }) => (
                <Typography
                  variant="subtitle1"
                  component="h4"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 2,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              h5: ({ children }) => (
                <Typography
                  variant="subtitle2"
                  component="h5"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 1,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              h6: ({ children }) => (
                <Typography
                  variant="body1"
                  component="h6"
                  gutterBottom
                  sx={{
                    color: 'primary.main',
                    mt: 1,
                    mb: 1,
                    fontWeight: 'bold',
                  }}
                >
                  {children}
                </Typography>
              ),
              p: ({ children }) => (
                <Typography variant="body1" paragraph sx={{ mb: 2 }}>
                  {children}
                </Typography>
              ),
              ul: ({ children }) => (
                <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              ol: ({ children }) => (
                <Box component="ol" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              li: ({ children }) => (
                <Typography component="li" variant="body1" sx={{ mb: 0.5 }}>
                  {children}
                </Typography>
              ),
              blockquote: ({ children }) => (
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: 'grey.100',
                    borderLeft: '4px solid #1976d2',
                    mb: 2,
                  }}
                >
                  <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                    {children}
                  </Typography>
                </Paper>
              ),
              code: ({ children, className }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <Box
                      component="code"
                      sx={{
                        bgcolor: 'grey.100',
                        px: 0.5,
                        py: 0.25,
                        borderRadius: 1,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      {children}
                    </Box>
                  );
                }
                return (
                  <Paper
                    sx={{ p: 2, bgcolor: 'grey.100', mb: 2, overflow: 'auto' }}
                  >
                    <pre
                      style={{
                        margin: 0,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      <code>{children}</code>
                    </pre>
                  </Paper>
                );
              },
              table: ({ children }) => (
                <Box sx={{ overflow: 'auto', mb: 2 }}>
                  <Box
                    component="table"
                    sx={{ minWidth: '100%', border: '1px solid #e0e0e0' }}
                  >
                    {children}
                  </Box>
                </Box>
              ),
              th: ({ children }) => (
                <Box
                  component="th"
                  sx={{
                    p: 1,
                    bgcolor: 'grey.100',
                    border: '1px solid #e0e0e0',
                    fontWeight: 'bold',
                    textAlign: 'left',
                  }}
                >
                  {children}
                </Box>
              ),
              td: ({ children }) => (
                <Box
                  component="td"
                  sx={{
                    p: 1,
                    border: '1px solid #e0e0e0',
                  }}
                >
                  {children}
                </Box>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </Box>
      );
    }

    // For JSON/JSONL and other text files, use the existing formatting
    const formattedContent = formatFileContent(content, fileName);
    return (
      <Box
        component="pre"
        sx={{
          backgroundColor: '#f8f9fa',
          border: '1px solid #e9ecef',
          m: 0,
          p: 3,
          overflow: 'auto',
          height: '100%',
          fontSize: '0.85rem',
          fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f1f1',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#c1c1c1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#a8a8a8',
          },
        }}
      >
        {formattedContent}
      </Box>
    );
  };

  const downloadFile = async (file: DataFile) => {
    try {
      const response = await fetch(
        `/api/download/${encodeURIComponent(file.path)}`
      );

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download file');
    }
  };

  const navigateToDirectory = (path: string) => {
    setCurrentPath(path);
    fetchData(path);
  };

  const navigateToRoot = () => {
    setCurrentPath('');
    fetchData('');
  };

  const copyFileName = async (fileName: string) => {
    try {
      await navigator.clipboard.writeText(fileName);
      setCopySuccess(fileName);
      setTimeout(() => setCopySuccess(null), 2000); // Clear success message after 2 seconds
    } catch (err) {
      console.error('Failed to copy filename:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = fileName;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopySuccess(fileName);
      setTimeout(() => setCopySuccess(null), 2000);
    }
  };

  const copyFileContent = async () => {
    if (!fileContent || !selectedFile) return;

    try {
      const formattedContent = formatFileContent(
        fileContent,
        selectedFile.name
      );
      await navigator.clipboard.writeText(formattedContent);
      setCopySuccess('file-content');
      setTimeout(() => setCopySuccess(null), 2000);
    } catch (err) {
      console.error('Failed to copy file content:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = formatFileContent(fileContent, selectedFile.name);
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopySuccess('file-content');
      setTimeout(() => setCopySuccess(null), 2000);
    }
  };

  // File selection functions
  const toggleFileSelection = (filePath: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(filePath)) {
      newSelection.delete(filePath);
    } else {
      newSelection.add(filePath);
    }
    setSelectedFiles(newSelection);
  };

  const selectAllFiles = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files.map(file => file.path)));
    }
  };

  const clearSelection = () => {
    setSelectedFiles(new Set());
    setSelectionMode(false);
  };

  // File processing functions
  const deleteFiles = async (filePaths: string[]) => {
    try {
      setProcessing(true);
      const response = await fetch('/api/files/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filePaths }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to delete files');
      }

      // Refresh the file list
      await fetchData(currentPath);
      clearSelection();
      setDeleteDialogOpen(false);

      setCopySuccess(
        `${filePaths.length} file${filePaths.length !== 1 ? 's' : ''} deleted successfully`
      );
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete files');
    } finally {
      setProcessing(false);
    }
  };

  const mergeFiles = async (filePaths: string[], outputFileName: string) => {
    try {
      setProcessing(true);
      const response = await fetch('/api/files/merge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filePaths,
          outputFileName,
          outputDirectory: currentPath || 'data',
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to merge files');
      }

      // Refresh the file list
      await fetchData(currentPath);
      clearSelection();
      setMergeDialogOpen(false);
      setMergeFileName('');

      setCopySuccess(`Files merged successfully into ${outputFileName}`);
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge files');
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteSingleFile = (file: DataFile) => {
    setSelectedFiles(new Set([file.path]));
    setDeleteDialogOpen(true);
  };

  const handleMergeFiles = () => {
    if (selectedFiles.size === 0) return;

    // Generate a default merge filename
    const firstFile = files.find(f => selectedFiles.has(f.path));
    if (firstFile) {
      const extension = firstFile.name.split('.').pop() || 'jsonl';
      const baseName = currentPath ? currentPath.split('/').pop() : 'merged';
      setMergeFileName(`${baseName}_merged.${extension}`);
    }

    setMergeDialogOpen(true);
  };

  useEffect(() => {
    // Handle URL parameters on component mount
    const pathParam = searchParams.get('path');
    const highlightParam = searchParams.get('highlight');

    if (pathParam) {
      setCurrentPath(pathParam);
      setHighlightedFile(highlightParam);
      fetchData(pathParam);

      // Clear highlight after 5 seconds
      if (highlightParam) {
        setTimeout(() => {
          setHighlightedFile(null);
        }, 5000);
      }
    } else {
      fetchData();
    }
  }, [searchParams]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const isJsonFile = (filename: string): boolean => {
    return filename.endsWith('.json') || filename.endsWith('.jsonl');
  };

  const isViewableFile = (filename: string): boolean => {
    return (
      filename.endsWith('.json') ||
      filename.endsWith('.jsonl') ||
      filename.endsWith('.md')
    );
  };

  const getFileStageIcon = (path: string) => {
    if (path.includes('/tasks/')) return '📝';
    if (path.includes('/verified_tasks/')) return '✅';
    if (path.includes('/evaluations/')) return '⚡';
    if (path.includes('/judging/')) return '🧠';
    if (path.includes('/reports/')) return '📊';
    if (path.includes('/analysis/')) return '🔍';
    return '📄';
  };

  const getFileStageDescription = (path: string) => {
    if (path.includes('/tasks/')) return 'Task Generation';
    if (path.includes('/verified_tasks/')) return 'Task Verification';
    if (path.includes('/evaluations/')) return 'Model Evaluation';
    if (path.includes('/judging/')) return 'LLM Judging';
    if (path.includes('/reports/')) return 'Analysis Reports';
    if (path.includes('/analysis/')) return 'Comparative Analysis';
    return 'Data Files';
  };

  const getDirectoryStageInfo = (name: string) => {
    const stageMap: {
      [key: string]: { icon: string; description: string; order: number };
    } = {
      tasks: { icon: '📝', description: 'Generated tasks', order: 1 },
      verified_tasks: {
        icon: '✅',
        description: 'Verified and approved tasks',
        order: 2,
      },
      evaluations: {
        icon: '⚡',
        description: 'Model evaluation results',
        order: 3,
      },
      judging: { icon: '🧠', description: 'LLM judge scoring', order: 4 },
      reports: {
        icon: '📊',
        description: 'Analysis reports and summaries',
        order: 5,
      },
      analysis: {
        icon: '🔍',
        description: 'Comparative analysis and charts',
        order: 6,
      },
    };

    return stageMap[name] || { icon: '📁', description: 'Files', order: 999 };
  };

  const renderPathBreadcrumbs = () => {
    if (!currentPath) return null;

    // Remove 'data/' prefix from path if present for breadcrumb display
    const displayPath = currentPath.startsWith('data/')
      ? currentPath.slice(5)
      : currentPath;
    const pathParts = displayPath.split('/').filter(part => part);

    return (
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          component="button"
          variant="body2"
          onClick={navigateToRoot}
          sx={{ display: 'flex', alignItems: 'center' }}
        >
          <HomeIcon sx={{ mr: 0.5, fontSize: 16 }} />
          Data
        </Link>
        {pathParts.map((part, index) => {
          const isLast = index === pathParts.length - 1;
          // Reconstruct the full path for navigation
          const partPath = 'data/' + pathParts.slice(0, index + 1).join('/');

          // Get stage info for better breadcrumb display
          const stageInfo = getDirectoryStageInfo(part);
          const displayName =
            stageInfo.icon !== '📁' ? `${stageInfo.icon} ${part}` : part;

          return isLast ? (
            <Typography key={part} color="text.primary" variant="body2">
              {displayName}
            </Typography>
          ) : (
            <Link
              key={part}
              component="button"
              variant="body2"
              onClick={() => navigateToDirectory(partPath)}
            >
              {displayName}
            </Link>
          );
        })}
      </Breadcrumbs>
    );
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={() => fetchData(currentPath)}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography
          variant="h4"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center' }}
        >
          <DataIcon sx={{ mr: 1 }} />
          Data Files
        </Typography>
        <Box display="flex" gap={1}>
          {files.length > 0 && (
            <Button
              variant={selectionMode ? 'contained' : 'outlined'}
              startIcon={selectionMode ? <CancelIcon /> : <SelectAllIcon />}
              onClick={() => {
                if (selectionMode) {
                  clearSelection();
                } else {
                  setSelectionMode(true);
                }
              }}
            >
              {selectionMode ? 'Cancel' : 'Select'}
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => fetchData(currentPath)}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {renderPathBreadcrumbs()}

      {/* Show directories if at root */}
      {!currentPath && directories.length > 0 && (
        <Box mb={4}>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <FolderIcon sx={{ mr: 1 }} />
            Server Data Directories
          </Typography>
          <Grid container spacing={2}>
            {directories.map(dir => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={dir.name}>
                <Card
                  elevation={2}
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      elevation: 4,
                      backgroundColor: 'action.hover',
                    },
                  }}
                  onClick={() => navigateToDirectory(dir.path)}
                >
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={1}>
                      <FolderIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6" component="h3">
                        {dir.name}
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      gutterBottom
                    >
                      {dir.fileCount} files • {formatFileSize(dir.totalSize)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last modified: {formatDate(dir.lastModified)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          <Divider sx={{ my: 3 }} />
        </Box>
      )}

      {/* Show subdirectories if in a domain directory (not in a stage directory) */}
      {currentPath &&
        directories.length > 0 &&
        !currentPath.includes('/tasks') &&
        !currentPath.includes('/verified_tasks') &&
        !currentPath.includes('/evaluations') &&
        !currentPath.includes('/judging') &&
        !currentPath.includes('/reports') &&
        !currentPath.includes('/analysis') && (
          <Box mb={4}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              <FolderIcon sx={{ mr: 1 }} />
              Evaluation Pipeline Stages
            </Typography>
            <Grid container spacing={2}>
              {directories
                .sort(
                  (a, b) =>
                    getDirectoryStageInfo(a.name).order -
                    getDirectoryStageInfo(b.name).order
                )
                .map(dir => {
                  const stageInfo = getDirectoryStageInfo(dir.name);
                  return (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={dir.name}>
                      <Card
                        elevation={2}
                        sx={{
                          cursor: 'pointer',
                          '&:hover': {
                            elevation: 4,
                            backgroundColor: 'action.hover',
                          },
                        }}
                        onClick={() => navigateToDirectory(dir.path)}
                      >
                        <CardContent>
                          <Box display="flex" alignItems="center" mb={1}>
                            <Typography variant="h5" sx={{ mr: 1 }}>
                              {stageInfo.icon}
                            </Typography>
                            <Box>
                              <Typography variant="h6" component="h3">
                                {dir.name}
                              </Typography>
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{ fontSize: '0.8rem' }}
                              >
                                {stageInfo.description}
                              </Typography>
                            </Box>
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            gutterBottom
                          >
                            {dir.fileCount} files •{' '}
                            {formatFileSize(dir.totalSize)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Last modified: {formatDate(dir.lastModified)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
            </Grid>
            <Divider sx={{ my: 3 }} />
          </Box>
        )}

      {/* Show files */}
      {files.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <StorageIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body1" color="text.secondary" gutterBottom>
            No Data Files Found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {currentPath
              ? `No files found in ${currentPath}`
              : 'No data files were found. Generate some tasks to see them here.'}
          </Typography>
        </Paper>
      ) : (
        <>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <FileIcon sx={{ mr: 1 }} />
            Files {currentPath && `in ${currentPath}`}
            {currentPath && (
              <Chip
                label={getFileStageDescription(currentPath)}
                size="small"
                variant="outlined"
                sx={{ ml: 2, fontSize: '0.7rem' }}
              />
            )}
          </Typography>

          {/* Summary of file details */}
          {files.length > 0 && (
            <Box sx={{ mb: 2 }}>
              {(() => {
                const totalTasks = files.reduce(
                  (sum, file) => sum + (file.details?.taskCount || 0),
                  0
                );
                const totalRecords = files.reduce(
                  (sum, file) => sum + (file.details?.recordCount || 0),
                  0
                );
                const filesWithDetails = files.filter(file => file.details);

                if (totalTasks > 0) {
                  return (
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Chip
                        icon={<span style={{ fontSize: '0.8rem' }}>📝</span>}
                        label={`${totalTasks} total task${totalTasks !== 1 ? 's' : ''}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      {totalRecords > totalTasks && (
                        <Chip
                          icon={<span style={{ fontSize: '0.8rem' }}>📄</span>}
                          label={`${totalRecords} total record${totalRecords !== 1 ? 's' : ''}`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                      {filesWithDetails.length > 0 && (
                        <Chip
                          icon={<span style={{ fontSize: '0.8rem' }}>📁</span>}
                          label={`${filesWithDetails.length} analyzed file${filesWithDetails.length !== 1 ? 's' : ''}`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  );
                }
                return null;
              })()}
            </Box>
          )}

          {/* Selection mode controls */}
          {selectionMode && files.length > 0 && (
            <Box sx={{ mb: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
                flexWrap="wrap"
                gap={2}
              >
                <Box display="flex" alignItems="center" gap={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={
                          selectedFiles.size === files.length &&
                          files.length > 0
                        }
                        indeterminate={
                          selectedFiles.size > 0 &&
                          selectedFiles.size < files.length
                        }
                        onChange={selectAllFiles}
                      />
                    }
                    label={`Select All (${selectedFiles.size}/${files.length})`}
                  />
                </Box>
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<MergeIcon />}
                    onClick={handleMergeFiles}
                    disabled={selectedFiles.size < 2}
                  >
                    Merge Files ({selectedFiles.size})
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => setDeleteDialogOpen(true)}
                    disabled={selectedFiles.size === 0}
                  >
                    Delete Files ({selectedFiles.size})
                  </Button>
                </Box>
              </Box>
            </Box>
          )}

          <Grid container spacing={3}>
            {files.map(file => {
              const stageIcon = getFileStageIcon(file.path);
              const stageDescription = getFileStageDescription(file.path);
              const isSelected = selectedFiles.has(file.path);
              const isHighlighted = highlightedFile === file.path;

              return (
                <Grid item xs={12} md={6} lg={4} key={file.name}>
                  <Card
                    elevation={isHighlighted ? 6 : 2}
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      border: isSelected
                        ? '2px solid'
                        : isHighlighted
                          ? '2px solid'
                          : '1px solid',
                      borderColor: isSelected
                        ? 'primary.main'
                        : isHighlighted
                          ? 'success.main'
                          : 'divider',
                      bgcolor: isSelected
                        ? 'primary.50'
                        : isHighlighted
                          ? 'success.50'
                          : 'background.paper',
                      animation: isHighlighted ? 'pulse 2s infinite' : 'none',
                      '@keyframes pulse': {
                        '0%': { boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.4)' },
                        '70%': { boxShadow: '0 0 0 10px rgba(76, 175, 80, 0)' },
                        '100%': { boxShadow: '0 0 0 0 rgba(76, 175, 80, 0)' },
                      },
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        {selectionMode && (
                          <Checkbox
                            checked={isSelected}
                            onChange={() => toggleFileSelection(file.path)}
                            sx={{ mr: 1 }}
                          />
                        )}
                        <Typography variant="h6" sx={{ mr: 1 }}>
                          {stageIcon}
                        </Typography>
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Typography variant="h6" component="h2" noWrap>
                            {file.name}
                          </Typography>
                          {stageDescription !== 'Data Files' && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ fontSize: '0.75rem' }}
                            >
                              {stageDescription}
                            </Typography>
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Chip
                            label={file.name.split('.').pop()?.toUpperCase()}
                            size="small"
                            sx={{ fontSize: '0.7rem' }}
                          />
                          {isHighlighted && (
                            <Chip
                              label="NEW"
                              size="small"
                              color="success"
                              sx={{ fontSize: '0.6rem', fontWeight: 'bold' }}
                            />
                          )}
                        </Box>
                      </Box>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                        sx={{ display: 'flex', alignItems: 'center' }}
                      >
                        <StorageIcon sx={{ fontSize: 16, mr: 0.5 }} />
                        {formatFileSize(file.size)}
                      </Typography>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                        sx={{ display: 'flex', alignItems: 'center' }}
                      >
                        <ScheduleIcon sx={{ fontSize: 16, mr: 0.5 }} />
                        {formatDate(file.modified)}
                      </Typography>

                      {/* File Details */}
                      {file.details && (
                        <Box sx={{ mt: 1 }}>
                          {file.details.type === 'report' &&
                            file.details.recordCount !== undefined && (
                              <Typography
                                variant="body2"
                                color="primary"
                                gutterBottom
                                sx={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  fontWeight: 'medium',
                                }}
                              >
                                📝 {file.details.recordCount} header
                                {file.details.recordCount !== 1 ? 's' : ''}
                              </Typography>
                            )}
                          {file.details.type === 'tasks' &&
                            file.details.taskCount !== undefined && (
                              <Typography
                                variant="body2"
                                color="primary"
                                gutterBottom
                                sx={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  fontWeight: 'medium',
                                }}
                              >
                                📝 {file.details.taskCount} task
                                {file.details.taskCount !== 1 ? 's' : ''}
                              </Typography>
                            )}
                          {file.details.recordCount !== undefined &&
                            file.details.type !== 'report' &&
                            file.details.recordCount !==
                              file.details.taskCount && (
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                gutterBottom
                                sx={{ display: 'flex', alignItems: 'center' }}
                              >
                                📄 {file.details.recordCount} record
                                {file.details.recordCount !== 1 ? 's' : ''}
                              </Typography>
                            )}
                          {file.details.lineCount !== undefined && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              gutterBottom
                              sx={{ display: 'flex', alignItems: 'center' }}
                            >
                              📋 {file.details.lineCount} line
                              {file.details.lineCount !== 1 ? 's' : ''}
                            </Typography>
                          )}
                        </Box>
                      )}

                      {/* Loading indicator for file details */}
                      {detailsLoading &&
                        (file.name.endsWith('.json') ||
                          file.name.endsWith('.jsonl') ||
                          file.name.endsWith('.md')) &&
                        !file.details && (
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              mt: 1,
                            }}
                          >
                            <CircularProgress size={12} sx={{ mr: 1 }} />
                            <Typography variant="body2" color="text.secondary">
                              Loading details...
                            </Typography>
                          </Box>
                        )}

                      <Box display="flex" gap={1} mt={2}>
                        <Tooltip
                          title={
                            copySuccess === file.name
                              ? 'Copied!'
                              : 'Copy filename'
                          }
                        >
                          <IconButton
                            size="small"
                            onClick={() => copyFileName(file.name)}
                            color={
                              copySuccess === file.name ? 'success' : 'default'
                            }
                          >
                            <CopyIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            onClick={() => downloadFile(file)}
                            color="primary"
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                        {isViewableFile(file.name) && (
                          <Tooltip title="View Content">
                            <IconButton
                              size="small"
                              onClick={() => fetchFileContent(file)}
                              color="secondary"
                              disabled={contentLoading}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {!selectionMode && (
                          <Tooltip title="Delete File">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteSingleFile(file)}
                              color="error"
                              disabled={processing}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </>
      )}

      {/* File Content Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="xl"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            height: '90vh',
            maxHeight: '90vh',
          },
        }}
      >
        <DialogTitle>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="space-between"
          >
            <Box>
              <Typography variant="h6">{selectedFile?.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedFile?.name.endsWith('.jsonl')
                  ? 'JSONL Task File'
                  : selectedFile?.name.endsWith('.json')
                    ? 'JSON File'
                    : selectedFile?.name.endsWith('.md')
                      ? 'Markdown Report'
                      : 'Text File'}
              </Typography>
            </Box>
            <IconButton onClick={() => setViewDialogOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {contentLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            renderFileContent(fileContent || '', selectedFile?.name || '')
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {selectedFile && (
            <>
              <Button
                onClick={copyFileContent}
                startIcon={<CopyIcon />}
                color={copySuccess === 'file-content' ? 'success' : 'primary'}
                disabled={!fileContent}
              >
                {copySuccess === 'file-content' ? 'Copied!' : 'Copy Content'}
              </Button>
              <Button
                onClick={() => downloadFile(selectedFile)}
                startIcon={<DownloadIcon />}
                variant="contained"
              >
                Download
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6" color="error">
            Delete File{selectedFiles.size > 1 ? 's' : ''}
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Are you sure you want to delete {selectedFiles.size} file
            {selectedFiles.size > 1 ? 's' : ''}?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This action cannot be undone.
          </Typography>
          <Box sx={{ mt: 2 }}>
            {Array.from(selectedFiles).map(filePath => {
              const file = files.find(f => f.path === filePath);
              return file ? (
                <Typography key={filePath} variant="body2" sx={{ py: 0.5 }}>
                  • {file.name}
                </Typography>
              ) : null;
            })}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={processing}
          >
            Cancel
          </Button>
          <Button
            onClick={() => deleteFiles(Array.from(selectedFiles))}
            color="error"
            variant="contained"
            disabled={processing}
            startIcon={
              processing ? <CircularProgress size={16} /> : <DeleteIcon />
            }
          >
            {processing ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Merge Files Dialog */}
      <Dialog
        open={mergeDialogOpen}
        onClose={() => setMergeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6">Merge Files</Typography>
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Merge {selectedFiles.size} files into a single file:
          </Typography>
          <Box sx={{ mt: 2, mb: 2 }}>
            {Array.from(selectedFiles).map(filePath => {
              const file = files.find(f => f.path === filePath);
              return file ? (
                <Typography key={filePath} variant="body2" sx={{ py: 0.5 }}>
                  • {file.name}
                </Typography>
              ) : null;
            })}
          </Box>
          <TextField
            fullWidth
            label="Output Filename"
            value={mergeFileName}
            onChange={e => setMergeFileName(e.target.value)}
            placeholder="merged_file.jsonl"
            helperText="The merged file will be saved in the current directory"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setMergeDialogOpen(false)}
            disabled={processing}
          >
            Cancel
          </Button>
          <Button
            onClick={() => mergeFiles(Array.from(selectedFiles), mergeFileName)}
            color="primary"
            variant="contained"
            disabled={processing || !mergeFileName.trim()}
            startIcon={
              processing ? <CircularProgress size={16} /> : <MergeIcon />
            }
          >
            {processing ? 'Merging...' : 'Merge'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Processing Backdrop */}
      <Backdrop
        sx={{ color: '#fff', zIndex: theme => theme.zIndex.drawer + 1 }}
        open={processing}
      >
        <Box textAlign="center">
          <CircularProgress color="inherit" />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Processing files...
          </Typography>
        </Box>
      </Backdrop>

      {/* Copy Success Snackbar */}
      <Snackbar
        open={!!copySuccess}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(null)}
        message={copySuccess}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Box>
  );
};

export default DataFiles;
