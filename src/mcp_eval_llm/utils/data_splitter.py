"""
Data Splitting Utilities

This module provides utilities for splitting JSONL files into train/valid/test sets.
"""
import json
import random
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

from .cli import Colors, colored_print


def validate_ratios(train_ratio: float, valid_ratio: float, test_ratio: float) -> None:
    """Validate that the train, valid, and test ratios sum to 1.0.
    
    Args:
        train_ratio: Ratio for training set
        valid_ratio: Ratio for validation set  
        test_ratio: Ratio for test set
        
    Raises:
        ValueError: If ratios don't sum to 1.0
    """
    total_ratio = train_ratio + valid_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError(f"Train, valid, and test ratios must sum to 1.0, got {total_ratio}")


def load_jsonl_tasks(file_path: str) -> List[Dict[str, Any]]:
    """Load tasks from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of task dictionaries
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        Exception: If there's an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse and validate JSON lines
        tasks = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                try:
                    task = json.loads(line)
                    tasks.append(task)
                except json.JSONDecodeError as e:
                    colored_print(f"⚠️  Warning: Skipping invalid JSON at line {i+1}: {e}", Colors.YELLOW)
        
        colored_print(f"✓ Loaded {len(tasks)} tasks from {file_path}", Colors.GREEN)
        return tasks
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading input file: {e}")


def split_tasks(tasks: List[Dict[str, Any]], train_ratio: float, valid_ratio: float, test_ratio: float, seed: int = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split tasks into train, validation, and test sets.
    
    Args:
        tasks: List of task dictionaries
        train_ratio: Ratio for training set
        valid_ratio: Ratio for validation set
        test_ratio: Ratio for test set  
        seed: Random seed for reproducible splits
        
    Returns:
        Tuple of (train_tasks, valid_tasks, test_tasks)
    """
    # Set random seed for reproducibility
    if seed is not None:
        random.seed(seed)
        colored_print(f"✓ Random seed set to {seed}", Colors.GREEN)
    
    # Randomly shuffle tasks
    shuffled_tasks = tasks.copy()
    random.shuffle(shuffled_tasks)
    colored_print(f"✓ Randomly shuffled tasks", Colors.GREEN)
    
    # Calculate split indices
    total_tasks = len(shuffled_tasks)
    train_count = int(total_tasks * train_ratio)
    valid_count = int(total_tasks * valid_ratio)
    test_count = total_tasks - train_count - valid_count  # Remaining tasks go to test
    
    # Split tasks
    train_tasks = shuffled_tasks[:train_count]
    valid_tasks = shuffled_tasks[train_count:train_count + valid_count]
    test_tasks = shuffled_tasks[train_count + valid_count:]
    
    colored_print(f"✓ Split into {len(train_tasks)} train, {len(valid_tasks)} valid, {len(test_tasks)} test tasks", Colors.GREEN)
    
    return train_tasks, valid_tasks, test_tasks


def write_jsonl(tasks: List[Dict[str, Any]], filepath: str) -> None:
    """Write tasks to a JSONL file.
    
    Args:
        tasks: List of task dictionaries
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')


def generate_output_paths(input_file: str, output_dir: str = None) -> Tuple[str, str, str]:
    """Generate output file paths for train, valid, and test sets.
    
    Args:
        input_file: Input file path
        output_dir: Output directory (optional)
        
    Returns:
        Tuple of (train_path, valid_path, test_path)
    """
    input_name = Path(input_file).stem
    
    if output_dir:
        train_path = os.path.join(output_dir, f"{input_name}_train.jsonl")
        valid_path = os.path.join(output_dir, f"{input_name}_valid.jsonl")
        test_path = os.path.join(output_dir, f"{input_name}_test.jsonl")
    else:
        train_path = f"{input_name}_train.jsonl"
        valid_path = f"{input_name}_valid.jsonl"
        test_path = f"{input_name}_test.jsonl"
    
    return train_path, valid_path, test_path


def create_split_summary(input_file: str, total_tasks: int, train_ratio: float, valid_ratio: float, test_ratio: float, 
                        train_count: int, valid_count: int, test_count: int, seed: int,
                        train_path: str, valid_path: str, test_path: str, output_dir: str = None) -> str:
    """Create and save a summary of the data split.
    
    Args:
        input_file: Input file path
        total_tasks: Total number of tasks
        train_ratio: Training set ratio
        valid_ratio: Validation set ratio
        test_ratio: Test set ratio
        train_count: Number of training tasks
        valid_count: Number of validation tasks
        test_count: Number of test tasks
        seed: Random seed used
        train_path: Training set file path
        valid_path: Validation set file path
        test_path: Test set file path
        output_dir: Output directory (optional)
        
    Returns:
        Path to the summary file
    """
    summary = {
        'input_file': input_file,
        'total_tasks': total_tasks,
        'train_ratio': train_ratio,
        'valid_ratio': valid_ratio,
        'test_ratio': test_ratio,
        'train_count': train_count,
        'valid_count': valid_count,
        'test_count': test_count,
        'seed': seed,
        'output_files': {
            'train': train_path,
            'valid': valid_path,
            'test': test_path
        }
    }
    
    input_name = Path(input_file).stem
    summary_path = f"{input_name}_split_summary.json"
    if output_dir:
        summary_path = os.path.join(output_dir, summary_path)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary_path


def split_jsonl_file(input_file: str, output_dir: str = None, train_ratio: float = 0.7, 
                    valid_ratio: float = 0.15, test_ratio: float = 0.15, seed: int = 42) -> Dict[str, str]:
    """Split a JSONL file into train, validation, and test sets.
    
    Args:
        input_file: Path to the input JSONL file
        output_dir: Output directory for split files (default: current directory)
        train_ratio: Ratio of data for training set (default: 0.7)
        valid_ratio: Ratio of data for validation set (default: 0.15)
        test_ratio: Ratio of data for test set (default: 0.15)
        seed: Random seed for reproducible splits (default: 42)
        
    Returns:
        Dictionary with paths to output files and summary
        
    Raises:
        ValueError: If ratios don't sum to 1.0
        FileNotFoundError: If input file doesn't exist
    """
    # Validate ratios
    validate_ratios(train_ratio, valid_ratio, test_ratio)
    
    # Load tasks from JSONL file
    tasks = load_jsonl_tasks(input_file)
    
    # Split tasks
    train_tasks, valid_tasks, test_tasks = split_tasks(tasks, train_ratio, valid_ratio, test_ratio, seed)
    
    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        colored_print(f"✓ Created output directory: {output_dir}", Colors.GREEN)
    
    # Generate output file paths
    train_path, valid_path, test_path = generate_output_paths(input_file, output_dir)
    
    # Write split files
    write_jsonl(train_tasks, train_path)
    write_jsonl(valid_tasks, valid_path)
    write_jsonl(test_tasks, test_path)
    
    # Print summary
    colored_print(f"✓ Data splitting completed successfully!", Colors.BRIGHT_GREEN, bold=True)
    colored_print(f"  📁 Train: {train_path} ({len(train_tasks)} tasks)", Colors.GREEN)
    colored_print(f"  📁 Valid: {valid_path} ({len(valid_tasks)} tasks)", Colors.GREEN)
    colored_print(f"  📁 Test: {test_path} ({len(test_tasks)} tasks)", Colors.GREEN)
    
    # Generate split summary
    summary_path = create_split_summary(
        input_file, len(tasks), train_ratio, valid_ratio, test_ratio,
        len(train_tasks), len(valid_tasks), len(test_tasks), seed,
        train_path, valid_path, test_path, output_dir
    )
    
    colored_print(f"  📊 Summary: {summary_path}", Colors.CYAN)
    
    return {
        'train': train_path,
        'valid': valid_path,
        'test': test_path,
        'summary': summary_path
    } 