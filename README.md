# dtsa5304
CU Boulder MSDS Fundamentals of Data Visualization (DTSA 5304) Final Project

## Assignment Information and Repository Structure

This repository contains my final assignment for DTSA 5304 as well as the code to reproduce all analyses.

* `rise_of_cs.qmd` is the project's main file. It contains the code for all visualizations, background information about the dataset and project, and narrative about design decisions.  
* `rise_of_cs.html` the rendered version of `rise_of_cs.qmd`, which will be submitted. It can be downloaded and viewed in a web browser (GitHub will only display the raw HTML source code).
* `src` contains Python scripts for extracting, transforming, and loading the 
Integrated Postsecondary Education Data System (IPEDS) data. These scripts are called by `rise_of_cs.qmd`.
* `instructions` contains project instructions are requirements (for my convenience and reference).


## Reproducibility and Environment Setup

This project uses `uv`...
The main project of this repository is the `

1. Clone the repository, optionally specifying a specific location to clone to, replacing `<target-folder-name>` with a directory such as `~/Downloads/treys_dtsa5304`:

```bash
git clone https://github.com/treyhendrix/dtsa5304.git <target-folder-name>
```

2. Install the `uv` and `quarto` tools if you do not already have them installed

* [uv official installation guide](https://docs.astral.sh/uv/getting-started/installation/)
* Once you have `uv` install, you can install Quarto (if you do not already have it) using: 

```bash
uv tool install quarto-cli
```

3. Navigate to the cloned directory and create a virtual environment by running:

```bash
uv sync
```

4. Render `rise_of_cs.qmd` and reproduce the analysis by running the command below: 

```bash
uv run quarto render rise_of_cs.qmd
```
