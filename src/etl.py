"""
ETL Script for IPEDS CS Degrees
Author: Trey Hendrix
Date Started: 2026-08-23
Date Updated: 2026-08-23
"""

# %% Modules
import sys
from pathlib import Path

import scipeds

# %% Identify Directory
if "ipykernel" in sys.modules:
    print("Interactive session")
    PROJECT_DIR = Path.cwd().resolve()
elif "__file__" in globals():
    PROJECT_DIR = Path(__file__).parent.parent
    print("Terminal session")
else:
    raise FileNotFoundError("Could not find project directory.")


# %% Download DB
scipeds.download_db  # the=
