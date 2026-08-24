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
    duck_db_files = _update_list_of_duckdb_files()
elif len(duckdb_files) == 1:
    print("Relying on previous IPEDS download.")
else:
    raise FileExistsError(
        f"Multiple .duckdb files found in data directory: {"; ".join(str(x.name) for x in duckdb_files)}. Please clear the directory and try again."
    )
DUCK_DB_FILEPATH = duck_db_files[0]
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

# TODO 2026-08-23T20:31:08-0400 Need to make this calculation safe to divide-by-zero errors
prop_cs_df["prop_cs"] = (
    prop_cs_df["cs_bachelors_degrees"] / prop_cs_df["bachelors_degrees"]
)


# Summarize by state


# %% Check what CIP codes map to ncses_detailed_field_group
# TODO 2026-08-23T20:33:57-0400 Working on this

cip_df = engine.get_df_from_query(
    f"""
    SELECT DISTINCT 
        cipcode::TEXT AS cipcode, 
        ncses_detailed_field_group::TEXT AS ncses_detailed_field_group
    FROM {COMPLETIONS_TABLE};
    """
)
cs_cip_df = cip_df.loc[cip_df["ncses_detailed_field_group"] == "Computer Science"]
# CIP families
# Mostly 11 = Computer and information Science and Support Services
# But a few 07 = Does not exist in current taxonomy... weird
# A few 30 = Multi/Interdisciplinary (e.g., data science)
# A few 52 = Business (e.g., "Business Systems Networking and Telecommunications")
