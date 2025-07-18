import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ProgressParser:
    """Helper class for parsing progress information from CLI tool output."""
    
    def __init__(self):
        # Initialize patterns for different CLI operations
        self.patterns = self._initialize_patterns()
        self.phase_keywords = self._initialize_phase_keywords()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for parsing progress from CLI output."""
        return {
            # Task Verification patterns (from verify.py)
            'verification': [
                r'Starting verification for task (\d+)/(\d+)',
                r'Successfully verified task (\d+)/(\d+)',
                r'Task (\d+)/(\d+) failed verification',
                r'Error processing task (\d+)/(\d+)',
                r'Task verification complete\..*Successfully verified: (\d+), Failed verification: (\d+), Errors: (\d+)',
                r'Verifying (\d+) tasks?',
                r'Skipping (\d+) already verified tasks',
                r'Successfully completed task (\d+)/(\d+)',
                r'Task (\d+)/(\d+) error',
            ],
            
            # Task Generation patterns (from generate.py)
            'generation': [
                r'Starting generation for task (\d+)/(\d+)',
                r'Generated task (\d+)/(\d+)',
                r'Task generation completed in ([\d.]+) seconds',
                r'Task generation complete\. (\d+) tasks saved',
                r'Generating (\d+) tasks?',
                r'Successfully generated task (\d+)/(\d+)',
            ],
            
            # Model Evaluation patterns (from evaluate.py)
            'evaluation': [
                r'Starting evaluation for task (\d+)/(\d+)',
                r'Task evaluation completed in ([\d.]+) seconds',
                r'Successfully completed task (\d+)/(\d+)',
                r'Successfully evaluated task (\d+)/(\d+)',
                r'Tasks evaluated: (\d+)',
                r'Tasks completed successfully: (\d+)',
                r'Success rate: ([\d.]+)%',
                r'Loaded (\d+) tasks from',
                r'Evaluating (\d+) tasks?',
                r'Skipping task (\d+)/(\d+).*already tested',
            ],
            
            # LLM Judge patterns (from judge.py)
            'judging': [
                r'Starting evaluation for record (\d+)/(\d+)',
                r'Record evaluation completed in ([\d.]+) seconds',
                r'Successfully evaluated record (\d+)/(\d+)',
                r'Evaluating: (\d+)/(\d+)',
                r'Judging (\d+) records?',
            ],
            
            # Auto workflow patterns (from auto.py)
            'auto_workflow': [
                r'STEP (\d+): (.+)',
                r'✅ (.+) completed successfully',
                r'❌ (.+) failed',
                r'🚀 Running: (.+)',
                r'📊 Evaluating Model (\d+)/(\d+)',
            ],
            
            # General progress patterns
            'general': [
                r'(\d+)% complete',
                r'Progress: (\d+)%',
                r'(\d+)/(\d+) complete',
                r'Processing (\d+) of (\d+)',
                r'Completed (\d+)/(\d+)',
                r'(\d+)/(\d+) processed',
                r'(\d+)/(\d+) done',
            ]
        }
    
    def _initialize_phase_keywords(self):
        """Initialize phase completion keywords that indicate progress milestones."""
        return {
            # Task generation phases
            'starting generation': 5,
            'generation complete': 25,
            'task generation complete': 25,
            'tasks saved': 25,
            
            # Task verification phases
            'starting verification': 30,
            'verification complete': 50,
            'task verification complete': 50,
            'verified tasks saved': 50,
            
            # Model evaluation phases
            'starting evaluation': 55,
            'evaluation complete': 80,
            'model evaluation complete': 80,
            'results saved': 80,
            
            # Analysis phases
            'starting analysis': 85,
            'analysis complete': 90,
            'report generated': 90,
            
            # LLM judging phases
            'starting judging': 92,
            'judging complete': 95,
            'judge results saved': 95,
            
            # Final completion
            'workflow completed': 100,
            'auto workflow completed successfully': 100,
            'evaluation summary': 95,
        }
    
    def parse_progress_from_line(self, line: str, job_id: str, metadata: Dict[str, Any]) -> Optional[int]:
        """
        Parse progress indicators from a single line of CLI output.
        
        Args:
            line: The output line to parse
            job_id: Job identifier for tracking metadata
            metadata: Job metadata dictionary to store state
            
        Returns:
            Progress percentage (0-100) or None if no progress found
        """
        line_lower = line.lower().strip()
        
        # First check for phase completion keywords
        for keyword, progress_value in self.phase_keywords.items():
            if keyword in line_lower:
                logger.debug(f"Job {job_id}: Phase keyword '{keyword}' -> {progress_value}%")
                return progress_value
        
        # Then check pattern-based progress
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    logger.debug(f"Job {job_id}: Pattern '{pattern}' matched line '{line}' in {category}, groups: {match.groups()}")
                    progress = self._extract_progress_from_match(match, job_id, metadata, category)
                    if progress is not None:
                        logger.debug(f"Job {job_id}: Pattern match in {category} -> {progress}%")
                        return progress
        
        return None
    
    def _extract_progress_from_match(self, match, job_id: str, metadata: Dict[str, Any], category: str) -> Optional[int]:
        """Extract progress percentage from regex match groups."""
        groups = match.groups()
        
        if len(groups) == 1:
            # Single number - could be percentage, completed count, or total
            try:
                value = float(groups[0])
            except ValueError:
                # If the first group is not a number, this pattern doesn't apply
                logger.debug(f"Job {job_id}: Non-numeric match in {category}: '{groups[0]}'")
                return None
            
            # Direct percentage patterns
            if any(keyword in match.group(0).lower() for keyword in ['% complete', 'progress:', 'success rate:']):
                return min(100, max(0, int(value)))
            
            # Total count patterns (e.g., "Loaded 100 tasks from", "Verifying 50 tasks")
            if any(keyword in match.group(0).lower() for keyword in ['loaded', 'verifying', 'generating', 'evaluating', 'judging']):
                metadata['total_items'] = int(value)
                return 5  # Small progress for setup
            
            # Completion count - try to calculate percentage using stored metadata
            if 'total_items' in metadata and metadata['total_items'] > 0:
                total = metadata['total_items']
                progress = int((value / total) * 100)
                return min(100, max(0, progress))
            
            # Single task completion - set a reasonable increment
            if 'completed' in match.group(0).lower():
                return min(100, max(5, int(value * 2)))  # Rough estimate
                
        elif len(groups) == 2:
            # Current/Total pattern - this is the most common pattern
            try:
                current, total = float(groups[0]), float(groups[1])
            except ValueError:
                # If the groups are not numbers, this pattern doesn't apply
                logger.debug(f"Job {job_id}: Non-numeric match in {category}: '{groups[0]}', '{groups[1]}'")
                return None
            
            if total > 0:
                # Store total for future calculations
                metadata['total_items'] = int(total)
                
                # Calculate progress percentage
                progress = int((current / total) * 100)
                return min(100, max(0, progress))
                
        elif len(groups) == 3:
            # Summary pattern like "Successfully verified: X, Failed: Y, Errors: Z"
            try:
                successful, failed, errors = float(groups[0]), float(groups[1]), float(groups[2])
            except ValueError:
                # If the groups are not numbers, this pattern doesn't apply
                logger.debug(f"Job {job_id}: Non-numeric match in {category}: '{groups[0]}', '{groups[1]}', '{groups[2]}'")
                return None
            
            total_processed = successful + failed + errors
            
            if total_processed > 0:
                # If we have a stored total, use it; otherwise use processed count
                expected_total = metadata.get('total_items', total_processed)
                if expected_total > 0:
                    progress = int((total_processed / expected_total) * 100)
                    return min(100, max(0, progress))
        
        return None
    
    def get_operation_type(self, line: str) -> Optional[str]:
        """Determine the type of operation from the output line."""
        line_lower = line.lower()
        
        if any(keyword in line_lower for keyword in ['verification', 'verify', 'verified']):
            return 'verification'
        elif any(keyword in line_lower for keyword in ['generation', 'generate', 'generated']):
            return 'generation'
        elif any(keyword in line_lower for keyword in ['evaluation', 'evaluate', 'evaluated']):
            return 'evaluation'
        elif any(keyword in line_lower for keyword in ['judging', 'judge', 'judged']):
            return 'judging'
        elif any(keyword in line_lower for keyword in ['analysis', 'analyze', 'analyzed']):
            return 'analysis'
        elif any(keyword in line_lower for keyword in ['workflow', 'auto', 'step']):
            return 'auto_workflow'
        
        return 'general'
    
    def estimate_progress_from_operation(self, operation_type: str, line: str) -> Optional[int]:
        """Estimate progress based on operation type and current activity."""
        line_lower = line.lower()
        
        # Base progress estimates for different operation phases
        base_estimates = {
            'generation': {
                'starting': 5,
                'in_progress': 15,
                'completing': 25
            },
            'verification': {
                'starting': 30,
                'in_progress': 40,
                'completing': 50
            },
            'evaluation': {
                'starting': 55,
                'in_progress': 70,
                'completing': 80
            },
            'analysis': {
                'starting': 85,
                'in_progress': 88,
                'completing': 90
            },
            'judging': {
                'starting': 92,
                'in_progress': 94,
                'completing': 95
            }
        }
        
        if operation_type in base_estimates:
            estimates = base_estimates[operation_type]
            
            if any(keyword in line_lower for keyword in ['starting', 'begin', 'initializing']):
                return estimates['starting']
            elif any(keyword in line_lower for keyword in ['complete', 'finished', 'done', 'saved']):
                return estimates['completing']
            elif any(keyword in line_lower for keyword in ['processing', 'running', 'executing']):
                return estimates['in_progress']
        
        return None 