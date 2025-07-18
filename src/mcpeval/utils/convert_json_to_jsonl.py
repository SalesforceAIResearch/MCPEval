#!/usr/bin/env python3
"""
Convert JSON file to JSONL (JSON Lines) format.
This script reads a JSON file containing an array of objects and converts it to JSONL format,
where each object is written as a separate line.

Enhanced version also supports separating trajectory and completion scores from judge results files.
"""

import json
import argparse
import os
import re
from pathlib import Path


def convert_json_to_jsonl(input_file, output_file=None):
    """
    Convert a JSON file containing an array to JSONL format.

    Args:
        input_file (str): Path to the input JSON file
        output_file (str, optional): Path to the output JSONL file.
                                   If None, uses input filename with .jsonl extension
    """
    input_path = Path(input_file)

    # Generate output filename if not provided
    if output_file is None:
        output_file = input_path.with_suffix(".jsonl")

    try:
        # Read the JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure data is a list
        if not isinstance(data, list):
            raise ValueError("Input JSON file must contain an array/list of objects")

        # Write to JSONL format
        with open(output_file, "w", encoding="utf-8") as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")

        print(f"Successfully converted {input_file} to {output_file}")
        print(f"Converted {len(data)} objects to JSONL format")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_file}': {e}")
    except Exception as e:
        print(f"Error: {e}")


def extract_eval_model_from_filename(filename):
    """
    Extract the evaluation model name from the filename.
    Expected format: gpt-4o_{eval_model}_task_evaluation_judge_results.json

    Args:
        filename (str): Input filename

    Returns:
        str: Evaluation model name (e.g., 'gpt-4o-mini', 'gpt-4.1-nano')
    """
    # Match pattern: gpt-4o_{eval_model}_task_evaluation_judge_results.json
    pattern = r"gpt-4o_(.+?)_task_evaluation_judge_results\.json$"
    match = re.search(pattern, filename)

    if match:
        return match.group(1)
    else:
        raise ValueError(f"Filename '{filename}' does not match expected pattern")


def separate_judge_results(input_file, output_dir=None):
    """
    Separate trajectory and completion data from judge results JSON files
    and save as separate JSONL files.

    Args:
        input_file (str): Path to the input judge results JSON file
        output_dir (str, optional): Output directory. If None, uses same directory as input file
    """
    input_path = Path(input_file)

    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract eval model from filename
        eval_model = extract_eval_model_from_filename(input_path.name)
        judge_model = "gpt-4o"  # Assuming gpt-4o is always the judge model

        # Read the JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure data is a list
        if not isinstance(data, list):
            raise ValueError("Input JSON file must contain an array/list of objects")

        # Define field mappings
        trajectory_fields = [
            "task_id",
            "task_name",
            "original_success",
            "trajectory_score",
            "trajectory_scores",
            "trajectory_comments",
            "used_ground_truth_trajectory",
            "used_ground_truth_response",
        ]

        completion_fields = [
            "task_id",
            "task_name",
            "original_success",
            "completion_score",
            "completion_scores",
            "completion_comments",
            "used_ground_truth_trajectory",
            "used_ground_truth_response",
        ]

        # Extract data for each type
        trajectory_data = []
        completion_data = []

        for item in data:
            # Extract trajectory data
            trajectory_item = {
                field: item.get(field) for field in trajectory_fields if field in item
            }
            trajectory_data.append(trajectory_item)

            # Extract completion data
            completion_item = {
                field: item.get(field) for field in completion_fields if field in item
            }
            completion_data.append(completion_item)

        # Generate output filenames
        base_name = f"{eval_model}_task_evaluation_with_{judge_model}"
        trajectory_file = output_dir / f"{base_name}_trajectory.jsonl"
        completion_file = output_dir / f"{base_name}_completion.jsonl"
        judge_results_file = output_dir / f"{base_name}_judge_results.jsonl"

        # Write trajectory data
        with open(trajectory_file, "w", encoding="utf-8") as f:
            for item in trajectory_data:
                json.dump(item, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")

        # Write completion data
        with open(completion_file, "w", encoding="utf-8") as f:
            for item in completion_data:
                json.dump(item, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")

        # Write full judge results data
        with open(judge_results_file, "w", encoding="utf-8") as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")

        print(f"Successfully separated data from {input_file}")
        print(f"Created {len(trajectory_data)} trajectory records in {trajectory_file}")
        print(f"Created {len(completion_data)} completion records in {completion_file}")
        print(f"Created {len(data)} judge results records in {judge_results_file}")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_file}': {e}")
    except Exception as e:
        print(f"Error: {e}")


def process_multiple_judge_files(input_files, output_dir=None):
    """
    Process multiple judge results files.

    Args:
        input_files (list): List of input file paths
        output_dir (str, optional): Output directory
    """
    for input_file in input_files:
        print(f"\nProcessing {input_file}...")
        separate_judge_results(input_file, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON file to JSONL format or separate judge results"
    )
    parser.add_argument("input_file", nargs="?", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSONL file path (optional)")
    parser.add_argument(
        "--separate-judge",
        action="store_true",
        help="Separate trajectory and completion data from judge results files",
    )
    parser.add_argument(
        "--batch-judge",
        nargs="+",
        metavar="FILE",
        help="Process multiple judge results files",
    )
    parser.add_argument("--output-dir", help="Output directory (for batch processing)")

    args = parser.parse_args()

    if args.batch_judge:
        # Process multiple judge results files
        process_multiple_judge_files(args.batch_judge, args.output_dir)
    elif args.separate_judge:
        # Separate single judge results file
        if not args.input_file:
            print("Error: input_file is required when using --separate-judge")
            return
        separate_judge_results(args.input_file, args.output_dir)
    else:
        # Regular JSON to JSONL conversion
        if not args.input_file:
            print("Error: input_file is required")
            return
        convert_json_to_jsonl(args.input_file, args.output)


if __name__ == "__main__":
    main()
