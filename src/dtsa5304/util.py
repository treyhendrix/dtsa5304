"""
Helper Functions for IPEDS CS Degree Analysis
Author: Trey Hendrix
Date Started: 2026-08-25
Date Updated: 2026-08-25
"""

# %% Modules
import sys
from pathlib import Path


# %% Find project directory
def find_project_dir() -> Path:
    """Find the project directory accounting for interactive (e.g., REPL notebooks) and terminal-based execution."""

    # Identify environment type
    if "ipykernel" in sys.modules:  # Interactive/REPL session
        env_type = "interactive"
        candidate_paths = [Path.cwd().resolve()] + [*Path.cwd().resolve().parents]
    elif "__file__" in globals():  # File is being run in the terminal/as an executable
        env_type = "terminal"
        script_path = Path(__file__).parent
        candidate_paths = [script_path.resolve()] + [*script_path.resolve().parents]
    else:
        raise FileNotFoundError(
            "Could not find project directory. Failed to identify the environment in which the script is running."
        )

    # Travel up in the directory until we find our repo's toml file or run out of options
    for path in candidate_paths:
        if "pyproject.toml" in [file.name for file in path.iterdir()]:
            PROJECT_DIR = path
            break
        if not path.name:
            if env_type == "interactive":
                raise FileNotFoundError(
                    f"Could not find project directory working upwards from an interactive session starting at Path.cwd() = {Path.cwd()!s}"
                )
            elif env_type == "terminal":
                raise FileNotFoundError(
                    f"Could not find project directory working upwards from a terminal-based session starting at __file__ = {Path.cwd()!s}"
                )
            else:
                raise FileNotFoundError(
                    "Could not find project directory. An unknown error occurred."
                )

    return PROJECT_DIR


# %% Default script behavior
if __name__ == "__main__":
    print(f"Project dir found at {find_project_dir()!s}")
