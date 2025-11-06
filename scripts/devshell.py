#!/usr/bin/env python3
"""Interactive development shell for saju-engine.

This script provides an IPython-based development shell with:
- All services preloaded and available
- Common utilities imported
- Container instances ready
- Policy files accessible
- Sample data for testing

Usage:
    python scripts/devshell.py                    # Start interactive shell
    python scripts/devshell.py --service analysis # Preload specific service
    python scripts/devshell.py --script myscript.py # Run script with context

Features:
    - Auto-import common modules
    - Preload engine instances
    - Access to containers and policies
    - Sample saju data for testing
    - Tab completion and syntax highlighting
    - Command history

Example Session:
    $ python scripts/devshell.py
    🚀 Saju Development Shell v1.0.0

    Available objects:
      - analysis_engine: AnalysisEngine instance
      - container: Default DI container
      - policies: Policy loader utilities

    In [1]: result = analysis_engine.analyze(request)
    In [2]: print(result.strength.level)
    Out[2]: '신강'
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
# Add analysis-service FIRST to avoid conflicts with other services
sys.path.insert(0, str(REPO_ROOT / "services" / "analysis-service"))
sys.path.insert(0, str(REPO_ROOT))

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print welcome banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║         🚀 Saju Development Shell v1.0.0                ║
╚══════════════════════════════════════════════════════════╝{Colors.END}

{Colors.GREEN}Environment loaded:{Colors.END}
  📁 Repo root: {REPO_ROOT}
  🐍 Python: {sys.version.split()[0]}
  📦 Services: analysis, astro, pillars, tz-time

{Colors.YELLOW}Quick start:{Colors.END}
  • analysis_engine - AnalysisEngine instance
  • container - DI container
  • sample_data - Test data loader
  • help_devshell() - Show available commands

{Colors.BLUE}Type 'help_devshell()' for more information{Colors.END}
"""
    print(banner)


def load_analysis_service() -> dict[str, Any]:
    """Load analysis service components."""
    print(f"{Colors.CYAN}Loading analysis-service...{Colors.END}")

    try:
        from app.core import AnalysisEngine
        from app.models import AnalysisRequest, PillarInput
        from app.api.dependencies_new import container

        # Create engine instance
        engine = AnalysisEngine()

        return {
            "AnalysisEngine": AnalysisEngine,
            "AnalysisRequest": AnalysisRequest,
            "PillarInput": PillarInput,
            "analysis_engine": engine,
            "container": container,
        }
    except Exception as e:
        print(f"{Colors.RED}⚠️  Failed to load analysis-service: {e}{Colors.END}")
        return {}


def load_common_utilities() -> dict[str, Any]:
    """Load common utilities and helpers."""
    print(f"{Colors.CYAN}Loading common utilities...{Colors.END}")

    try:
        from saju_common import (
            Container,
            ValidationError,
            NotFoundError,
            create_service_app,
        )
        from saju_common.policy_loader import resolve_policy_path

        return {
            "Container": Container,
            "ValidationError": ValidationError,
            "NotFoundError": NotFoundError,
            "create_service_app": create_service_app,
            "resolve_policy_path": resolve_policy_path,
        }
    except Exception as e:
        print(f"{Colors.RED}⚠️  Failed to load common utilities: {e}{Colors.END}")
        return {}


def load_sample_data() -> dict[str, Any]:
    """Load sample saju data for testing."""
    print(f"{Colors.CYAN}Loading sample data...{Colors.END}")

    # Sample birth data
    sample_pillars = {
        "year": {"pillar": "庚辰"},
        "month": {"pillar": "乙酉"},
        "day": {"pillar": "乙亥"},
        "hour": {"pillar": "辛巳"},
    }

    # Sample analysis request
    from datetime import datetime
    try:
        from app.models import AnalysisRequest, PillarInput

        sample_request = AnalysisRequest(
            pillars={
                key: PillarInput(pillar=val["pillar"])
                for key, val in sample_pillars.items()
            },
            options={
                "birth_dt": "2000-09-14T10:00:00+09:00",
                "timezone": "Asia/Seoul",
            }
        )

        return {
            "sample_pillars": sample_pillars,
            "sample_request": sample_request,
        }
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not create sample request: {e}{Colors.END}")
        return {
            "sample_pillars": sample_pillars,
        }


def help_devshell():
    """Show help information."""
    help_text = f"""
{Colors.BOLD}Saju Development Shell - Help{Colors.END}

{Colors.GREEN}Available Objects:{Colors.END}
  {Colors.BOLD}Engines:{Colors.END}
    • analysis_engine     - AnalysisEngine instance (preloaded)
    • AnalysisEngine      - Class for creating new instances

  {Colors.BOLD}Models:{Colors.END}
    • AnalysisRequest     - Request model class
    • PillarInput         - Pillar input model

  {Colors.BOLD}Container:{Colors.END}
    • container           - Default DI container
    • Container           - Container class

  {Colors.BOLD}Sample Data:{Colors.END}
    • sample_pillars      - Example four pillars
    • sample_request      - Pre-built AnalysisRequest

  {Colors.BOLD}Utilities:{Colors.END}
    • resolve_policy_path - Find policy files
    • create_service_app  - Create FastAPI app
    • ValidationError     - Exception class
    • NotFoundError       - Exception class

{Colors.GREEN}Quick Examples:{Colors.END}
  {Colors.CYAN}# Analyze sample data{Colors.END}
  result = analysis_engine.analyze(sample_request)
  print(result.strength.level)  # '신강'

  {Colors.CYAN}# Create custom request{Colors.END}
  request = AnalysisRequest(
      pillars={{
          "year": PillarInput(pillar="庚辰"),
          "month": PillarInput(pillar="乙酉"),
          "day": PillarInput(pillar="乙亥"),
          "hour": PillarInput(pillar="辛巳"),
      }},
      options={{"birth_dt": "2000-09-14T10:00:00+09:00"}}
  )
  result = analysis_engine.analyze(request)

  {Colors.CYAN}# Test container overrides{Colors.END}
  from unittest.mock import Mock
  mock_engine = Mock()
  with container.override("get_analysis_engine", mock_engine):
      engine = container.get("get_analysis_engine")
      assert engine is mock_engine

  {Colors.CYAN}# Find policy files{Colors.END}
  policy_path = resolve_policy_path("strength_policy_v2.json")
  print(policy_path)

{Colors.GREEN}IPython Commands:{Colors.END}
  • ?obj        - Show object info
  • obj?        - Show object info (alternate)
  • obj??       - Show source code
  • %whos       - List all variables
  • %history    - Show command history
  • %paste      - Paste code block
  • %debug      - Enter debugger on error

{Colors.BLUE}For more help: https://ipython.readthedocs.io{Colors.END}
"""
    print(help_text)


def start_shell(namespace: dict[str, Any], banner: bool = True):
    """Start interactive shell with namespace."""
    try:
        from IPython import embed
        from IPython.terminal.prompts import Prompts, Token

        # Custom prompt
        class SajuPrompt(Prompts):
            def in_prompt_tokens(self):
                return [
                    (Token.Prompt, '사주'),
                    (Token.Prompt, ' ['),
                    (Token.PromptNum, str(self.shell.execution_count)),
                    (Token.Prompt, ']: '),
                ]

        if banner:
            print_banner()

        # Configure IPython
        from traitlets.config import Config
        config = Config()
        config.TerminalInteractiveShell.prompts_class = SajuPrompt
        config.TerminalInteractiveShell.highlighting_style = 'monokai'
        config.TerminalInteractiveShell.confirm_exit = False

        embed(user_ns=namespace, config=config)

    except ImportError:
        # Fallback to standard Python REPL
        print(f"{Colors.YELLOW}⚠️  IPython not available, using standard Python REPL{Colors.END}")
        if banner:
            print_banner()

        import code
        code.interact(local=namespace, banner="")


def run_script(script_path: Path, namespace: dict[str, Any]):
    """Run a Python script with the devshell namespace."""
    if not script_path.exists():
        print(f"{Colors.RED}❌ Script not found: {script_path}{Colors.END}")
        return 1

    print(f"{Colors.CYAN}Running script: {script_path}{Colors.END}\n")

    # Read and execute script
    try:
        with open(script_path) as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, namespace)
        print(f"\n{Colors.GREEN}✅ Script completed successfully{Colors.END}")
        return 0
    except Exception as e:
        print(f"\n{Colors.RED}❌ Script failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive development shell for saju-engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--service",
        choices=["analysis", "astro", "pillars", "tz-time"],
        help="Preload specific service (default: analysis)",
        default="analysis",
    )
    parser.add_argument(
        "--script",
        type=Path,
        help="Run a Python script with devshell context",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress welcome banner",
    )

    args = parser.parse_args()

    # Build namespace
    namespace = {
        "help_devshell": help_devshell,
        "REPO_ROOT": REPO_ROOT,
    }

    # Load services based on selection
    if args.service == "analysis":
        namespace.update(load_analysis_service())
        namespace.update(load_sample_data())

    # Load common utilities
    namespace.update(load_common_utilities())

    # Run script or start shell
    if args.script:
        return run_script(args.script, namespace)
    else:
        start_shell(namespace, banner=not args.no_banner)
        return 0


if __name__ == "__main__":
    sys.exit(main())
