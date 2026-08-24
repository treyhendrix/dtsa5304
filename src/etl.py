"""
ETL Script for IPEDS CS Degrees
Author: Trey Hendrix
Date Started: 2026-08-23
Date Updated: 2026-08-23
"""

# %% Modules
import sys
from pathlib import Path

import numpy as np
import scipeds
from scipeds.constants import COMPLETIONS_TABLE
from scipeds.data.completions import CompletionsQueryEngine

# %% Identify Project Directory
if "ipykernel" in sys.modules:
    PROJECT_DIR = Path.cwd().resolve()
elif "__file__" in globals():
    PROJECT_DIR = Path(__file__).parent.parent
else:
    raise FileNotFoundError("Could not find project directory.")

# %% Download Duck DB
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def _update_list_of_duckdb_files(data_dir: Path = DATA_DIR) -> list[Path]:
    fn_duckdb_files = []
    for file in data_dir.iterdir():
        if file.name.endswith(".duckdb"):
            fn_duckdb_files.append(file)
    return fn_duckdb_files


duckdb_files = _update_list_of_duckdb_files()

if len(duckdb_files) == 0:
    print("No DuckDB files found. Downloading IPEDS data...")
    scipeds.download_db(DATA_DIR, overwrite=True, verbose=False)
    print("IPEDS data sucessfully downloaded as a .duckdb file")
    duckdb_files = _update_list_of_duckdb_files()
elif len(duckdb_files) == 1:
    print("Relying on previous IPEDS download.")
else:
    raise FileExistsError(
        f"Multiple .duckdb files found in data directory: {"; ".join(str(x.name) for x in duckdb_files)}. Please clear the directory and try again."
    )
DUCK_DB_FILEPATH = duckdb_files[0]
# %% Query the DB for completion data
engine = CompletionsQueryEngine(DUCK_DB_FILEPATH)

cs_df = engine.get_df_from_query(
    f"""
    SELECT
        c.year,
        d.unitid, d.institution_name, d.state_abbreviation,
        SUM(c.n_awards) AS cs_bachelors_degrees
    FROM {COMPLETIONS_TABLE} AS c
    LEFT JOIN ipeds_directory_info AS d ON c.unitid = d.unitid
    WHERE 
        c.awlevel = 'Bachelor''s degree'
        AND c.ncses_detailed_field_group = 'Computer Science'
        AND d.control_of_institution IN ('Private not-for-profit', 'Public')
    GROUP BY c.year, d.unitid, d.institution_name, d.state_abbreviation
    ORDER BY c.year;
    """
)

bach_df = engine.get_df_from_query(
    f"""
    SELECT
        c.year,
        d.unitid,
        SUM(c.n_awards) AS bachelors_degrees
    FROM {COMPLETIONS_TABLE} AS c
    LEFT JOIN ipeds_directory_info AS d ON c.unitid = d.unitid
    WHERE 
        c.awlevel = 'Bachelor''s degree'
        AND d.control_of_institution IN ('Private not-for-profit', 'Public')
    GROUP BY c.year, d.unitid
    ORDER BY c.year;
    """
)

prop_cs_df = cs_df.merge(
    bach_df[["year", "unitid", "bachelors_degrees"]],
    how="inner",
    on=["year", "unitid"],
    validate="1:1",
)
# NAs are not expected for either column, but we will fill them with zeros just in case
prop_cs_df["cs_bachelors_degrees"] = prop_cs_df["cs_bachelors_degrees"].fillna(0)
prop_cs_df["bachelors_degrees"] = prop_cs_df["bachelors_degrees"].fillna(0)

prop_cs_df["prop_cs"] = (
    (prop_cs_df["cs_bachelors_degrees"] / prop_cs_df["bachelors_degrees"])
    .replace(
        [np.inf, -np.inf], np.nan
    )  # handle divide-by-zero errors (none are expected)
    .fillna(0)
)

# %% Summarize by state
state_all_time_df = (
    prop_cs_df.groupby("state_abbreviation")
    .agg(cs_bach=("cs_bachelors_degrees", "sum"), bach=("bachelors_degrees", "sum"))
    .reset_index()
)
state_all_time_df["prop"] = state_all_time_df["cs_bach"] / state_all_time_df["bach"]
# TODO 2026-08-23T22:45:22-0400 Move this to the qmd?
# TODO 2026-08-23T22:49:52-0400 Refactor to a main() function that returns prop_cs_df?
