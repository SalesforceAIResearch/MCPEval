import os
import subprocess
import threading
import uuid
import re
from datetime import datetime
from utils.progress_parser import ProgressParser


class JobManager:
    def __init__(self, config):
        self.config = config
        self.job_progress = {}
        self.job_logs = {}
        self.job_metadata = {}
        self.running_processes = {}  # Track running subprocesses
        self.progress_parser = ProgressParser()  # Initialize progress parser

    def _parse_progress_from_output(self, line, job_id):
        """Parse progress indicators from CLI output using ProgressParser helper"""
        # Ensure job metadata exists
        if job_id not in self.job_metadata:
            self.job_metadata[job_id] = {}
            
        # Use the ProgressParser helper to parse the line
        progress = self.progress_parser.parse_progress_from_line(line, job_id, self.job_metadata[job_id])
        
        if progress is not None:
            return progress
            
        # Fallback: Try to estimate progress based on operation type
        operation_type = self.progress_parser.get_operation_type(line)
        if operation_type:
            estimated_progress = self.progress_parser.estimate_progress_from_operation(operation_type, line)
            if estimated_progress is not None:
                return estimated_progress
        
        return None

    def run_cli_command_with_progress(self, command, job_id=None, capture_output=True):
        """Run a CLI command with real-time progress tracking"""
        try:
            if job_id:
                # Initialize job tracking
                if job_id not in self.job_progress:
                    self.job_progress[job_id] = {'status': 'running', 'progress': 0}
                if job_id not in self.job_logs:
                    self.job_logs[job_id] = []

            # Get workspace directory from config
            workspace_root = self.config.get('workspace', {}).get('root', '../workspace')
            root_dir = workspace_root

            # Set up environment variables
            env = os.environ.copy()
            env_config = self.config.get('environment', {})
            for key, value in env_config.items():
                env[key] = value

            # Start the process with streaming output
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                cwd=root_dir,
                env=env,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            if job_id:
                self.running_processes[job_id] = process
                self.job_logs[job_id].append(f"Process started with PID: {process.pid}")
            
            # Stream output in real-time
            stdout_lines = []
            stderr_lines = []
            
            def read_stdout():
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        stdout_lines.append(line)
                        if job_id:
                            self.job_logs[job_id].append(line)
                            
                            # Parse progress from output
                            progress = self._parse_progress_from_output(line, job_id)
                            if progress is not None:
                                self.job_progress[job_id]['progress'] = progress
                                print(f"Job {job_id}: Progress updated to {progress}% from line: {line}")
                
                process.stdout.close()
            
            def read_stderr():
                for line in iter(process.stderr.readline, ''):
                    line = line.strip()
                    if line:
                        stderr_lines.append(line)
                        if job_id:
                            self.job_logs[job_id].append(f"Error: {line}")
                
                process.stderr.close()
            
            # Start reader threads
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            
            stdout_thread.start()
            stderr_thread.start()
            
            try:
                # Wait for process completion with timeout
                returncode = process.wait(timeout=30*60)
                
                # Wait for output threads to finish
                stdout_thread.join(timeout=5)
                stderr_thread.join(timeout=5)
                
                if job_id and job_id in self.running_processes:
                    del self.running_processes[job_id]
                
                if job_id:
                    if returncode == 0:
                        self.job_progress[job_id] = {'status': 'completed', 'progress': 100}
                        self.job_logs[job_id].append(f"Command completed successfully")
                    else:
                        self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                        self.job_logs[job_id].append(f"Command failed with exit code {returncode}")
                
                return {
                    'success': returncode == 0,
                    'output': '\n'.join(stdout_lines),
                    'error': '\n'.join(stderr_lines),
                    'returncode': returncode
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)
                
                if job_id and job_id in self.running_processes:
                    del self.running_processes[job_id]
                if job_id:
                    self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                    self.job_logs[job_id].append("Command timed out after 30 minutes")
                
                return {
                    'success': False,
                    'error': 'Command timed out after 30 minutes',
                    'returncode': -1
                }
        
        except Exception as e:
            if job_id:
                self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                self.job_logs[job_id].append(f"Error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def run_cli_command(self, command, job_id=None, capture_output=True):
        """Run a CLI command and optionally track progress"""
        # Use the new progress-aware version for better tracking
        return self.run_cli_command_with_progress(command, job_id, capture_output)

    def create_job(self, job_type, title, endpoint):
        """Create a new job and return job ID"""
        job_id = str(uuid.uuid4())
        self.job_metadata[job_id] = {
            "type": job_type,
            "title": title,
            "endpoint": endpoint
        }
        return job_id

    def run_job_async(self, job_id, command):
        """Run a job asynchronously in a background thread"""
        # Initialize job tracking before starting the thread
        self.job_progress[job_id] = {'status': 'running', 'progress': 0}
        self.job_logs[job_id] = []
        
        def run_task():
            try:
                # Store the command for debugging
                if job_id in self.job_metadata:
                    self.job_metadata[job_id]['command'] = command
                self.job_logs[job_id].append(f"Executing command: {command}")
                
                result = self.run_cli_command(command, job_id)
                self.job_progress[job_id].update(result)
            except Exception as e:
                self.job_progress[job_id]['status'] = 'failed'
                self.job_logs[job_id].append(f"Job execution error: {str(e)}")
        
        threading.Thread(target=run_task, daemon=True).start()
        return {'job_id': job_id, 'status': 'started'}

    def kill_job(self, job_id):
        """Kill a running job"""
        if job_id in self.running_processes:
            try:
                process = self.running_processes[job_id]
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate gracefully
            except Exception as e:
                self.job_logs[job_id].append(f"Error killing process: {str(e)}")
            finally:
                if job_id in self.running_processes:
                    del self.running_processes[job_id]
                self.job_progress[job_id]['status'] = 'cancelled'
                self.job_logs[job_id].append("Job was cancelled by user")
                return True
        
        # If no process found, just mark as cancelled
        if job_id in self.job_progress:
            self.job_progress[job_id]['status'] = 'cancelled'
            self.job_logs[job_id].append("Job was cancelled by user")
            return True
        
        return False

    def get_job_status(self, job_id):
        """Get job status and progress"""
        if job_id not in self.job_progress:
            return None
        
        response = {
            'job_id': job_id,
            'progress': self.job_progress[job_id],
            'logs': self.job_logs.get(job_id, [])
        }
        
        # Add workspace information for auto jobs
        if job_id in self.job_metadata:
            metadata = self.job_metadata[job_id]
            if metadata.get('endpoint') == 'auto':
                response['workspace'] = metadata.get('workspace')
                response['servers'] = metadata.get('servers')
        
        return response

    def get_recent_activities(self):
        """Get recent job activities"""
        activities = []
        
        # Convert job_progress to activity format
        for job_id, job_data in self.job_progress.items():
            # Get metadata if available, otherwise use defaults
            metadata = self.job_metadata.get(job_id, {})
            activity_type = metadata.get("type", "Unknown Task")
            title = metadata.get("title", f"Job {job_id[:8]}")
            
            # Calculate relative timestamp
            timestamp = "Just now"  # Default since we don't store creation time
            
            activity = {
                'id': job_id,
                'type': activity_type,
                'title': title,
                'status': job_data.get('status', 'unknown'),
                'progress': job_data.get('progress', 0),
                'timestamp': timestamp
            }
            
            # Add model information if available
            models = metadata.get('models', [])
            if models:
                activity['models'] = models
                activity['num_models'] = len(models)
            
            activities.append(activity)
        
        # Sort by most recent first (for now, just reverse order)
        activities.reverse()
        
        # Limit to last 10 activities
        activities = activities[:10]
        
        return activities 