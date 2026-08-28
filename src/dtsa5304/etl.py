"""
ETL Script for IPEDS CS Degrees
Author: Trey Hendrix
Date Started: 2026-08-23
Date Updated: 2026-08-27
"""

# %% Modules
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipeds
from scipeds.constants import COMPLETIONS_TABLE
from scipeds.data.completions import CompletionsQueryEngine

# %% Local Modules
from dtsa5304.util import find_project_dir


# %% IPEDS ETL Function
def get_ipeds_data() -> pd.DataFrame:
    """Download IPEDS duckDB file (if necessary) and wrangle data into rows representing counts of CS Bachelor's degrees and all Bachelor's degrees for all public and non-profit institutions for all years."""

    # Identify Project Directory
    PROJECT_DIR = find_project_dir()

    # Logging (for printing to console)
    class ISO8601Formatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created).astimezone()
            return dt.isoformat(timespec="milliseconds")

    console_handler = logging.StreamHandler(sys.stdout)
    formatter = ISO8601Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[console_handler])
    logger = logging.getLogger("etl")
    logger.info("Starting IPEDS ETL")

    # Download Duck DB
    DATA_DIR = PROJECT_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)
    logger.info(f"Checking for existing IPEDS data at {DATA_DIR!s}.")

    def _update_list_of_duckdb_files(data_dir: Path = DATA_DIR) -> list[Path]:
        fn_duckdb_files = []
        for file in data_dir.iterdir():
            if file.name.endswith(".duckdb"):
                fn_duckdb_files.append(file)
        return fn_duckdb_files

    duckdb_files = _update_list_of_duckdb_files()

    if len(duckdb_files) == 0:
        logger.info("No DuckDB files found. Downloading IPEDS data...")
        scipeds.download_db(DATA_DIR, overwrite=True, verbose=False)
        logger.info("IPEDS data sucessfully downloaded as a .duckdb file")
        duckdb_files = _update_list_of_duckdb_files()
        # TODO 2026-08-26T07:00:01-0400 Add a check here for if no files are found after the download (edge case)
    elif len(duckdb_files) == 1:
        logger.info("Previous IPEDS download found. Skipping fresh data download.")
    else:
        raise FileExistsError(
            f"Multiple .duckdb files found in data directory: {"; ".join(str(x.name) for x in duckdb_files)}. Please clear the directory and try again."
        )
    DUCK_DB_FILEPATH = duckdb_files[0]
    logger.info(f"Duck DB file '{DUCK_DB_FILEPATH!s}' ready for use.")
    # Query the DB for completion data
    engine = CompletionsQueryEngine(DUCK_DB_FILEPATH)

    def _query_bachelors_degrees(
        engine: CompletionsQueryEngine,
        extra_filter: str = "",
        degree_col_alias: str = "bachelors_degrees",
    ) -> pd.DataFrame:
        return engine.get_df_from_query(
            f"""
            SELECT
                c.year,
                d.unitid, d.institution_name, d.state_abbreviation,
                SUM(c.n_awards) AS {degree_col_alias}
            FROM {COMPLETIONS_TABLE} AS c
            LEFT JOIN ipeds_directory_info AS d ON c.unitid = d.unitid
            WHERE 
                c.awlevel = 'Bachelor''s degree'
                AND d.control_of_institution IN ('Private not-for-profit', 'Public')
                {extra_filter}
            GROUP BY c.year, d.unitid, d.institution_name, d.state_abbreviation
            ORDER BY c.year;
            """
        )

    logger.info("Querying CS bachelor's degrees from DuckDB.")
    cs_df = _query_bachelors_degrees(
        engine,
        extra_filter="AND c.ncses_detailed_field_group = 'Computer Science'",
        degree_col_alias="cs_bachelors_degrees",
    )
    logger.info("Querying all bachelor's degrees from DuckDB.")
    bach_df = _query_bachelors_degrees(engine)

    prop_cs_df = cs_df.merge(
        bach_df[["year", "unitid", "bachelors_degrees"]],
        how="inner",
        on=["year", "unitid"],
        validate="1:1",
    )
    # Check for NA values in degree counts (not expected) to prevent divide-by-zero issues
    n_cs_na = prop_cs_df["cs_bachelors_degrees"].isna().sum()
    n_bach_na = prop_cs_df["bachelors_degrees"].isna().sum()
    if n_cs_na == 0 and n_bach_na == 0:
        logger.info("No NA degree counts detected.")
    else:
        logger.info(
            f"NA degree counts detected: {n_cs_na} CS count NAs and {n_bach_na} bachelor's degree NAs"
        )
        logger.info(
            "Dropping any NA bachelor's degree count records and filling any missing CS degree counts with zeros."
        )
        prop_cs_df = prop_cs_df.loc[~prop_cs_df["bachelors_degrees"].isna()]
        prop_cs_df["cs_bachelors_degrees"] = prop_cs_df["cs_bachelors_degrees"].fillna(
            0
        )

    # This calculation should be safe from divide-by-zero errors
    prop_cs_df["prop_cs"] = (
        prop_cs_df["cs_bachelors_degrees"] / prop_cs_df["bachelors_degrees"]
    )
    logger.info(
        "Returning proportion of CS bachelor's degrees by year for all public and non-profit institutions."
    )
    return prop_cs_df


# %% Rainbow spaghetti fake data
def get_rainbow_spaghetti_data(random_seed: int = 42):
    """Generate fake 'spaghetti' data for a demonstration plot."""
    np.random.seed(random_seed)
    pastas = [
        "Spaghetti",
        "Penne",
        "Rigatoni",
        "Fettuccine",
        "Farfalle",
        "Ravioli",
        "Linguine",
        "Ziti",
        "Angel Hair",
        "Lasagne",
    ]
    pastas = sorted(pastas)
    years = np.arange(1984, 2025)
    pasta_df = pd.DataFrame(years, columns=["year"])
    for pasta in pastas:
        start_prop = np.random.uniform(0.1, 0.3)
        slope = np.random.uniform(0.005, 0.015)
        trend = start_prop + slope * (years - 1984)
        noise = np.random.normal(0, 0.04, size=len(years))
        pasta_df[pasta] = np.clip(trend + noise, 0, 1)
    return pd.melt(pasta_df, id_vars="year", var_name="pasta", value_name="prop")


# %% Default script behavior
if __name__ == "__main__":
    get_ipeds_data()
