import subprocess
import threading
import uuid
from datetime import datetime


class JobManager:
    def __init__(self, config):
        self.config = config
        self.job_progress = {}
        self.job_logs = {}
        self.job_metadata = {}

    def run_cli_command(self, command, job_id=None, capture_output=True):
        """Run a CLI command and optionally track progress"""
        try:
            if job_id:
                self.job_progress[job_id] = {'status': 'running', 'progress': 0}
                self.job_logs[job_id] = []

            # Get root directory from config
            root_dir = self.config.get('paths', {}).get('root_directory', '..')

            # Run the command
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=root_dir)
                output = result.stdout
                error = result.stderr
                
                if job_id:
                    if result.returncode == 0:
                        self.job_progress[job_id] = {'status': 'completed', 'progress': 100}
                        self.job_logs[job_id].append(f"Command completed successfully: {output}")
                    else:
                        self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                        self.job_logs[job_id].append(f"Command failed: {error}")
                
                return {
                    'success': result.returncode == 0,
                    'output': output,
                    'error': error,
                    'returncode': result.returncode
                }
            else:
                # For long-running commands, run in background but wait for completion
                result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=root_dir)
                output = result.stdout
                error = result.stderr
                
                if job_id:
                    if result.returncode == 0:
                        self.job_progress[job_id] = {'status': 'completed', 'progress': 100}
                        self.job_logs[job_id].append("Command completed successfully")
                        if output:
                            self.job_logs[job_id].append(f"Output: {output}")
                    else:
                        self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                        self.job_logs[job_id].append(f"Command failed with exit code {result.returncode}")
                        if error:
                            self.job_logs[job_id].append(f"Error: {error}")
                
                return {
                    'success': result.returncode == 0,
                    'output': output,
                    'error': error,
                    'returncode': result.returncode
                }
        
        except Exception as e:
            if job_id:
                self.job_progress[job_id] = {'status': 'failed', 'progress': 100}
                self.job_logs[job_id].append(f"Error: {str(e)}")
            return {'success': False, 'error': str(e)}

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
        def run_task():
            result = self.run_cli_command(command, job_id)
            self.job_progress[job_id].update(result)
        
        threading.Thread(target=run_task).start()
        return {'job_id': job_id, 'status': 'started'}

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
            
            activities.append(activity)
        
        # Sort by most recent first (for now, just reverse order)
        activities.reverse()
        
        # Limit to last 10 activities
        activities = activities[:10]
        
        return activities 