#!/usr/bin/env python3
"""
Auto Workflow CLI Tool

This module provides functionality for automatically running the complete evaluation cycle:
1. Task generation
2. Task verification
3. Model evaluation
4. Analysis (no report generation)
5. Optional LLM judging
6. Optional judge rubric analysis
7. Final comprehensive report generation

The auto feature creates a dedicated working directory and orchestrates all steps.
Each run is identified by a unique task ID for easy tracking and organization.
"""
import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
import time
import uuid
from datetime import datetime

from mcpeval.utils.cli import Colors, colored_print, setup_colored_logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoWorkflowOrchestrator:
    """Orchestrates the complete evaluation workflow."""

    def __init__(self, args):
        self.args = args
        self.working_dir = Path(args.working_dir)

        # Generate unique task ID for this run
        self.task_id = self._generate_task_id()

        # Store servers as they are - will be passed directly to commands
        self.servers = args.servers

        self.task_model = args.task_model
        self.model_configs = self._load_model_configs(args.eval_model_configs)
        self.num_tasks = args.num_tasks
        self.max_turns = args.max_turns
        self.enable_llm_judge = args.enable_llm_judge
        self.llm_judge_model = args.llm_judge_model

        # Optional prompt files
        self.task_generation_prompt = args.task_generation_prompt
        self.task_verification_prompt = args.task_verification_prompt
        self.evaluation_prompt = args.evaluation_prompt

        # Setup working directory structure
        self._setup_working_directory()

    def _generate_task_id(self) -> str:
        """Generate a unique task ID for this run."""
        # Use timestamp + short UUID for uniqueness and readability
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        task_id = f"{timestamp}_{short_uuid}"
        return task_id

    def _get_output_filename(self, base_name: str, extension: str = ".json") -> str:
        """Generate output filename with task ID."""
        return f"{self.task_id}_{base_name}{extension}"

    def _load_model_configs(self, config_paths: List[str]) -> List[Dict[str, Any]]:
        """Load model configuration files."""
        configs = []
        for config_path in config_paths:
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                config["_config_path"] = config_path
                config["_name"] = self._extract_model_name(config_path)
                configs.append(config)
                colored_print(f"✓ Loaded model config: {config['_name']}", Colors.GREEN)
            except Exception as e:
                colored_print(
                    f"❌ Error loading model config {config_path}: {e}", Colors.RED
                )
                sys.exit(1)
        return configs

    def _extract_model_name(self, config_path: str) -> str:
        """Extract model name from config file path."""
        # e.g., "eval_models/gpt-4o.json" -> "gpt4o"
        basename = Path(config_path).stem
        return basename.replace("-", "").replace(".", "")

    def _sanitize_model_name(self, model_name: str) -> str:
        """Sanitize model name for use in file paths."""
        return model_name.replace("/", "_").replace(":", "_").replace(" ", "_")

    def _setup_working_directory(self):
        """Create and setup the working directory structure."""
        try:
            # Create main working directory
            self.working_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            self.data_dir = self.working_dir / "data"
            self.results_dir = self.working_dir / "results"
            self.report_dir = self.working_dir / "report"
            self.logs_dir = self.working_dir / "logs"

            for dir_path in [
                self.data_dir,
                self.results_dir,
                self.report_dir,
                self.logs_dir,
            ]:
                dir_path.mkdir(exist_ok=True)

            colored_print(
                f"✓ Working directory setup complete: {self.working_dir}", Colors.GREEN
            )
            colored_print(f"📋 Task ID: {self.task_id}", Colors.BRIGHT_CYAN, bold=True)

        except Exception as e:
            colored_print(f"❌ Error setting up working directory: {e}", Colors.RED)
            sys.exit(1)

    def _check_prompts(self):
        """Check for provided prompt files and report status."""
        prompt_status = []

        if self.task_generation_prompt:
            if Path(self.task_generation_prompt).exists():
                prompt_status.append(
                    f"✓ Task generation prompt: {self.task_generation_prompt}"
                )
            else:
                colored_print(
                    f"⚠️ Task generation prompt file not found: {self.task_generation_prompt}",
                    Colors.YELLOW,
                )
                prompt_status.append("⚠ Task generation prompt: not found")
        else:
            prompt_status.append("- Task generation prompt: using default behavior")

        if self.task_verification_prompt:
            if Path(self.task_verification_prompt).exists():
                prompt_status.append(
                    f"✓ Task verification prompt: {self.task_verification_prompt}"
                )
            else:
                colored_print(
                    f"⚠️ Task verification prompt file not found: {self.task_verification_prompt}",
                    Colors.YELLOW,
                )
                prompt_status.append("⚠ Task verification prompt: not found")
        else:
            prompt_status.append("- Task verification prompt: using default behavior")

        if self.evaluation_prompt:
            if Path(self.evaluation_prompt).exists():
                prompt_status.append(f"✓ Evaluation prompt: {self.evaluation_prompt}")
            else:
                colored_print(
                    f"⚠️ Evaluation prompt file not found: {self.evaluation_prompt}",
                    Colors.YELLOW,
                )
                prompt_status.append("⚠ Evaluation prompt: not found")
        else:
            prompt_status.append("- Evaluation prompt: using default behavior")

        if prompt_status:
            colored_print("📝 Prompt Configuration:", Colors.BRIGHT_CYAN, bold=True)
            for status in prompt_status:
                if status.startswith("✓"):
                    colored_print(f"  {status}", Colors.GREEN)
                elif status.startswith("⚠"):
                    colored_print(f"  {status}", Colors.YELLOW)
                else:
                    colored_print(f"  {status}", Colors.DIM)

    def _run_command(
        self, cmd: List[str], step_name: str, log_file: Optional[str] = None
    ) -> bool:
        """Run a command and handle logging."""
        colored_print(f"🚀 Running: {step_name}", Colors.BRIGHT_CYAN, bold=True)
        colored_print(f"Command: {' '.join(cmd)}", Colors.DIM)

        # Setup logging
        log_path = None
        if log_file:
            log_path = self.logs_dir / log_file

        try:
            start_time = time.time()

            # Run the command
            if log_path:
                with open(log_path, "w") as f:
                    result = subprocess.run(
                        cmd, check=True, stdout=f, stderr=subprocess.STDOUT, text=True
                    )
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            elapsed = time.time() - start_time
            colored_print(
                f"✅ {step_name} completed successfully in {elapsed:.2f}s",
                Colors.BRIGHT_GREEN,
                bold=True,
            )

            if result.stdout and not log_path:
                logger.info(f"Output: {result.stdout[:200]}...")

            return True

        except subprocess.CalledProcessError as e:
            colored_print(
                f"❌ {step_name} failed with return code {e.returncode}",
                Colors.BRIGHT_RED,
                bold=True,
            )
            if e.stdout:
                colored_print(f"STDOUT: {e.stdout}", Colors.RED)
            if e.stderr:
                colored_print(f"STDERR: {e.stderr}", Colors.RED)
            return False
        except Exception as e:
            colored_print(
                f"❌ {step_name} failed with error: {e}", Colors.BRIGHT_RED, bold=True
            )
            return False

    def step_1_generate_tasks(self) -> str:
        """Step 1: Generate tasks using frontier model."""
        colored_print("\n" + "=" * 60, Colors.BRIGHT_YELLOW)
        colored_print("STEP 1: TASK GENERATION", Colors.BRIGHT_YELLOW, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_YELLOW)

        output_file = self.data_dir / self._get_output_filename(
            "evaluation_tasks", ".jsonl"
        )

        cmd = ["mcp-eval", "generate-tasks", "--servers"]

        # Add all servers
        cmd.extend(self.servers)

        # Add other arguments
        cmd.extend(
            [
                "--model",
                self.task_model,
                "--num-tasks",
                str(self.num_tasks),
                "--output",
                str(output_file),
            ]
        )

        # Add prompt file if provided
        if self.task_generation_prompt:
            cmd.extend(["--prompt-file", self.task_generation_prompt])

        success = self._run_command(
            cmd,
            "Task Generation",
            self._get_output_filename("01_task_generation", ".log"),
        )

        if not success:
            colored_print(
                "❌ Task generation failed. Stopping workflow.",
                Colors.BRIGHT_RED,
                bold=True,
            )
            sys.exit(1)

        return str(output_file)

    def step_2_verify_tasks(self, tasks_file: str) -> str:
        """Step 2: Verify generated tasks."""
        colored_print("\n" + "=" * 60, Colors.BRIGHT_BLUE)
        colored_print("STEP 2: TASK VERIFICATION", Colors.BRIGHT_BLUE, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_BLUE)

        output_file = self.data_dir / self._get_output_filename(
            "evaluation_tasks_verified", ".jsonl"
        )

        cmd = ["mcp-eval", "verify-tasks", "--servers"]

        # Add all servers
        cmd.extend(self.servers)

        # Add other arguments
        cmd.extend(
            [
                "--tasks-file",
                tasks_file,
                "--model",
                self.task_model,
                "--output",
                str(output_file),
            ]
        )

        # Add prompt file if provided
        if self.task_verification_prompt:
            cmd.extend(["--prompt-file", self.task_verification_prompt])

        success = self._run_command(
            cmd,
            "Task Verification",
            self._get_output_filename("02_task_verification", ".log"),
        )

        if not success:
            colored_print(
                "❌ Task verification failed. Stopping workflow.",
                Colors.BRIGHT_RED,
                bold=True,
            )
            sys.exit(1)

        return str(output_file)

    def step_3_evaluate_models(self, verified_tasks_file: str) -> List[str]:
        """Step 3: Evaluate all models."""
        colored_print("\n" + "=" * 60, Colors.BRIGHT_GREEN)
        colored_print("STEP 3: MODEL EVALUATION", Colors.BRIGHT_GREEN, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_GREEN)

        evaluation_results = []

        for i, model_config in enumerate(self.model_configs, 1):
            model_name = model_config["_name"]
            config_path = model_config["_config_path"]

            colored_print(
                f"\n📊 Evaluating Model {i}/{len(self.model_configs)}: {model_name}",
                Colors.BRIGHT_WHITE,
                bold=True,
            )

            # Create evaluation output file
            eval_output = self.results_dir / self._get_output_filename(
                f"{model_name}_evaluation"
            )

            cmd = ["mcp-eval", "evaluate", "--servers"]

            # Add all servers
            cmd.extend(self.servers)

            # Add other arguments
            cmd.extend(
                [
                    "--model-config",
                    config_path,
                    "--tasks-file",
                    verified_tasks_file,
                    "--output",
                    str(eval_output),
                    "--max-turns",
                    str(self.max_turns),
                ]
            )

            # Add evaluation prompt if provided
            if self.evaluation_prompt:
                cmd.extend(["--prompt-file", self.evaluation_prompt])

            step_name = f"Model Evaluation - {model_name}"
            log_file = self._get_output_filename(f"03_evaluation_{model_name}", ".log")

            success = self._run_command(cmd, step_name, log_file)

            if success:
                evaluation_results.append(str(eval_output))
                colored_print(f"✅ {model_name} evaluation completed", Colors.GREEN)
            else:
                colored_print(f"❌ {model_name} evaluation failed", Colors.RED)

        if not evaluation_results:
            colored_print(
                "❌ All model evaluations failed. Stopping workflow.",
                Colors.BRIGHT_RED,
                bold=True,
            )
            sys.exit(1)

        return evaluation_results

    def step_4_analyze_results(
        self, evaluation_files: List[str], verified_tasks_file: str
    ) -> List[str]:
        """Step 4: Analyze evaluation results (no report generation)."""
        colored_print("\n" + "=" * 60, Colors.BRIGHT_CYAN)
        colored_print("STEP 4: ANALYSIS", Colors.BRIGHT_CYAN, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_CYAN)

        analysis_results = []

        for eval_file in evaluation_files:
            eval_path = Path(eval_file)
            # Extract model name from filename with task ID prefix
            # Format: {task_id}_{model_name}_evaluation.json
            filename_without_ext = eval_path.stem
            model_name = filename_without_ext.replace(f"{self.task_id}_", "").replace(
                "_evaluation", ""
            )

            colored_print(
                f"\n🔍 Analyzing results for: {model_name}",
                Colors.BRIGHT_WHITE,
                bold=True,
            )

            # Create analysis output file
            analysis_output = self.results_dir / self._get_output_filename(
                f"{model_name}_summary_analysis"
            )

            cmd = [
                "mcp-eval",
                "analyze",
                "--predictions",
                eval_file,
                "--ground-truth",
                verified_tasks_file,
                "--analysis-output",
                str(analysis_output),
            ]

            step_name = f"Analysis - {model_name}"
            log_file = self._get_output_filename(f"04_analysis_{model_name}", ".log")

            success = self._run_command(cmd, step_name, log_file)

            if success:
                analysis_results.append(str(analysis_output))
                colored_print(f"✅ {model_name} analysis completed", Colors.GREEN)
            else:
                colored_print(f"❌ {model_name} analysis failed", Colors.RED)

        return analysis_results

    def step_5_llm_judge(
        self, evaluation_files: List[str], verified_tasks_file: str
    ) -> List[Dict[str, str]]:
        """Step 5: Optional LLM judging."""
        if not self.enable_llm_judge:
            colored_print("\n⏭️  Skipping LLM judging (disabled)", Colors.YELLOW)
            return []

        colored_print("\n" + "=" * 60, Colors.BRIGHT_MAGENTA)
        colored_print("STEP 5: LLM JUDGING", Colors.BRIGHT_MAGENTA, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_MAGENTA)

        judge_results = []

        for eval_file in evaluation_files:
            eval_path = Path(eval_file)
            # Extract model name from filename with task ID prefix
            # Format: {task_id}_{model_name}_evaluation.json
            filename_without_ext = eval_path.stem
            model_name = filename_without_ext.replace(f"{self.task_id}_", "").replace(
                "_evaluation", ""
            )

            colored_print(
                f"\n🧠 LLM judging for: {model_name}", Colors.BRIGHT_WHITE, bold=True
            )

            cmd = [
                "mcp-eval",
                "judge",
                "--input-file",
                eval_file,
                "--output-dir",
                str(self.results_dir),
                "--ground-truth",
                verified_tasks_file,
                "--model",
                self.llm_judge_model,
            ]

            step_name = f"LLM Judging - {model_name}"
            log_file = self._get_output_filename(f"05_llm_judge_{model_name}", ".log")

            success = self._run_command(cmd, step_name, log_file)

            if success:
                # Store the expected output file paths (based on judge command naming pattern)
                clean_judge_model = self._sanitize_model_name(self.llm_judge_model)
                judge_result = {
                    "model_name": model_name,
                    "trajectory_file": str(
                        self.results_dir
                        / self._get_output_filename(
                            f"{model_name}_evaluation_with_{clean_judge_model}_trajectory",
                            ".jsonl",
                        )
                    ),
                    "completion_file": str(
                        self.results_dir
                        / self._get_output_filename(
                            f"{model_name}_evaluation_with_{clean_judge_model}_completion",
                            ".jsonl",
                        )
                    ),
                }
                judge_results.append(judge_result)
                colored_print(f"✅ {model_name} LLM judging completed", Colors.GREEN)
            else:
                colored_print(f"❌ {model_name} LLM judging failed", Colors.RED)

        return judge_results

    def step_6_judge_rubric(self, judge_results: List[Dict[str, str]]) -> List[str]:
        """Step 6: Optional judge rubric analysis."""
        if not self.enable_llm_judge or not judge_results:
            colored_print(
                "\n⏭️  Skipping judge rubric analysis (LLM judging disabled or no results)",
                Colors.YELLOW,
            )
            return []

        colored_print("\n" + "=" * 60, Colors.BRIGHT_WHITE)
        colored_print("STEP 6: JUDGE RUBRIC ANALYSIS", Colors.BRIGHT_WHITE, bold=True)
        colored_print("=" * 60, Colors.BRIGHT_WHITE)

        rubric_analysis_results = []

        for judge_result in judge_results:
            model_name = judge_result["model_name"]
            trajectory_file = judge_result["trajectory_file"]
            completion_file = judge_result["completion_file"]

            colored_print(
                f"\n📋 Judge rubric analysis for: {model_name}",
                Colors.BRIGHT_WHITE,
                bold=True,
            )

            cmd = [
                "mcp-eval",
                "judge-rubric",
                "--trajectory-file",
                trajectory_file,
                "--completion-file",
                completion_file,
                "--output-dir",
                str(self.report_dir),
            ]

            step_name = f"Judge Rubric Analysis - {model_name}"
            log_file = self._get_output_filename(
                f"06_judge_rubric_{model_name}", ".log"
            )

            success = self._run_command(cmd, step_name, log_file)

            if success:
                # The judge-rubric command generates analysis files in the report directory
                clean_judge_model = self._sanitize_model_name(self.llm_judge_model)
                rubric_analysis_file = self.report_dir / self._get_output_filename(
                    f"{model_name}_evaluation_with_{clean_judge_model}_trajectory_llm_judger_analysis"
                )
                if rubric_analysis_file.exists():
                    rubric_analysis_results.append(str(rubric_analysis_file))
                colored_print(
                    f"✅ {model_name} judge rubric analysis completed", Colors.GREEN
                )
            else:
                colored_print(
                    f"❌ {model_name} judge rubric analysis failed", Colors.RED
                )

        return rubric_analysis_results

    def step_7_generate_final_report(
        self, analysis_files: List[str], rubric_analysis_files: List[str]
    ):
        """Step 7: Generate final comprehensive report."""
        colored_print("\n" + "=" * 60, Colors.BRIGHT_YELLOW)
        colored_print(
            "STEP 7: COMPREHENSIVE REPORT GENERATION", Colors.BRIGHT_YELLOW, bold=True
        )
        colored_print("=" * 60, Colors.BRIGHT_YELLOW)

        # Generate comprehensive report for each model
        for i, analysis_file in enumerate(analysis_files):
            analysis_path = Path(analysis_file)
            # Extract model name from filename with task ID prefix
            # Format: {task_id}_{model_name}_summary_analysis.json
            filename_without_ext = analysis_path.stem
            # Remove task ID prefix and summary_analysis suffix
            model_name = filename_without_ext.replace(f"{self.task_id}_", "").replace(
                "_summary_analysis", ""
            )

            colored_print(
                f"\n📄 Generating comprehensive report for: {model_name}",
                Colors.BRIGHT_WHITE,
                bold=True,
            )

            # Find corresponding rubric analysis file if available
            rubric_file = None
            if rubric_analysis_files:
                for rubric_path in rubric_analysis_files:
                    if model_name in rubric_path:
                        rubric_file = rubric_path
                        break

            # Create report generation command
            cmd = [
                "mcp-eval",
                "report-gen",
                "--tool-analysis-file",
                analysis_file,
                "--model-name",
                model_name,
                "--output-file",
                str(
                    self.report_dir
                    / self._get_output_filename(
                        f"{model_name}_comprehensive_report", ".md"
                    )
                ),
            ]

            # Add LLM judge file if available
            if rubric_file:
                cmd.extend(["--llm-judge-file", rubric_file])

            step_name = f"Comprehensive Report - {model_name}"
            log_file = self._get_output_filename(
                f"07_comprehensive_report_{model_name}", ".log"
            )

            success = self._run_command(cmd, step_name, log_file)

            if success:
                colored_print(
                    f"✅ {model_name} comprehensive report generated", Colors.GREEN
                )
            else:
                colored_print(
                    f"❌ {model_name} comprehensive report failed", Colors.RED
                )

    def _create_workflow_summary(
        self,
        evaluation_files: List[str],
        analysis_files: List[str],
        judge_results: List[Dict[str, str]],
        rubric_analysis_files: List[str],
    ):
        """Create a summary file of the workflow run."""
        try:
            summary_file = self.working_dir / self._get_output_filename(
                "workflow_summary", ".json"
            )

            summary_data = {
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat(),
                "workflow_config": {
                    "servers": self.servers,
                    "task_model": self.task_model,
                    "num_tasks": self.num_tasks,
                    "max_turns": self.max_turns,
                    "enable_llm_judge": self.enable_llm_judge,
                    "llm_judge_model": (
                        self.llm_judge_model if self.enable_llm_judge else None
                    ),
                    "models_evaluated": [
                        config["_name"] for config in self.model_configs
                    ],
                },
                "output_files": {
                    "evaluation_files": evaluation_files,
                    "analysis_files": analysis_files,
                    "judge_results": judge_results,
                    "rubric_analysis_files": rubric_analysis_files,
                },
                "directory_structure": {
                    "data_dir": str(self.data_dir),
                    "results_dir": str(self.results_dir),
                    "report_dir": str(self.report_dir),
                    "logs_dir": str(self.logs_dir),
                },
            }

            with open(summary_file, "w") as f:
                json.dump(summary_data, f, indent=2)

            colored_print(
                f"📋 Workflow summary saved: {summary_file}", Colors.BRIGHT_CYAN
            )

        except Exception as e:
            colored_print(
                f"⚠️  Warning: Could not create workflow summary: {e}", Colors.YELLOW
            )

    def run_workflow(self):
        """Run the complete workflow."""
        colored_print(
            "🎯 Starting Auto Evaluation Workflow", Colors.BRIGHT_CYAN, bold=True
        )
        colored_print(f"Task ID: {self.task_id}", Colors.BRIGHT_CYAN, bold=True)
        colored_print(f"Working Directory: {self.working_dir}", Colors.CYAN)
        if len(self.servers) == 1:
            colored_print(f"Server: {self.servers[0]}", Colors.CYAN)
        else:
            colored_print(f"Servers: {len(self.servers)} server(s)", Colors.CYAN)
            for i, server in enumerate(self.servers, 1):
                colored_print(f"  {i}. {server}", Colors.CYAN)
        colored_print(f"Task Model: {self.task_model}", Colors.CYAN)
        colored_print(f"Models to Evaluate: {len(self.model_configs)}", Colors.CYAN)
        colored_print(f"Number of Tasks: {self.num_tasks}", Colors.CYAN)
        colored_print(
            f"LLM Judging: {'Enabled' if self.enable_llm_judge else 'Disabled'}",
            Colors.CYAN,
        )

        try:
            # Step 0: Check prompts
            self._check_prompts()

            # Step 1: Generate tasks
            tasks_file = self.step_1_generate_tasks()

            # Step 2: Verify tasks
            verified_tasks_file = self.step_2_verify_tasks(tasks_file)

            # Step 3: Evaluate models
            evaluation_files = self.step_3_evaluate_models(verified_tasks_file)

            # Step 4: Analyze results (no report generation)
            analysis_files = self.step_4_analyze_results(
                evaluation_files, verified_tasks_file
            )

            # Step 5: Optional LLM judging
            judge_results = self.step_5_llm_judge(evaluation_files, verified_tasks_file)

            # Step 6: Optional judge rubric analysis
            rubric_analysis_files = self.step_6_judge_rubric(judge_results)

            # Step 7: Generate final comprehensive report
            self.step_7_generate_final_report(analysis_files, rubric_analysis_files)

            # Create workflow summary file
            self._create_workflow_summary(
                evaluation_files, analysis_files, judge_results, rubric_analysis_files
            )

            # Final success message
            colored_print("\n" + "=" * 60, Colors.BRIGHT_GREEN)
            colored_print(
                "🎉 AUTO WORKFLOW COMPLETED SUCCESSFULLY! 🎉",
                Colors.BRIGHT_GREEN,
                bold=True,
            )
            colored_print("=" * 60, Colors.BRIGHT_GREEN)
            colored_print(f"Task ID: {self.task_id}", Colors.BRIGHT_GREEN, bold=True)
            colored_print(f"Results available in: {self.working_dir}", Colors.GREEN)
            colored_print("📊 Evaluation files: results/", Colors.GREEN)
            colored_print("📝 Analysis files: results/", Colors.GREEN)
            colored_print("📄 Final reports: report/", Colors.GREEN)
            colored_print("📋 Logs: logs/", Colors.GREEN)
            colored_print(
                f"📋 Workflow summary: {self.task_id}_workflow_summary.json",
                Colors.GREEN,
            )
            colored_print(
                f"💡 All output files are prefixed with: {self.task_id}_",
                Colors.BRIGHT_CYAN,
            )

        except KeyboardInterrupt:
            colored_print(
                "\n⚠️  Workflow interrupted by user", Colors.BRIGHT_YELLOW, bold=True
            )
            sys.exit(1)
        except Exception as e:
            colored_print(
                f"\n❌ Workflow failed with error: {e}", Colors.BRIGHT_RED, bold=True
            )
            logger.exception("Detailed error information:")
            sys.exit(1)


def main(args):
    """Main entry point for the auto workflow."""
    # Set API key in environment if provided directly
    if hasattr(args, "api_key") and args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    # Create and run the workflow orchestrator
    orchestrator = AutoWorkflowOrchestrator(args)
    orchestrator.run_workflow()


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main auto --help")
    import sys

    sys.exit(1)
