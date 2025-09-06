# EURES-Job-Filter

Job Filter for finding visa sponsorship / relocation assistance jobs

## Usage

This repository contains a Python script that queries the [EURES](https://europa.eu/eures/) job search API for software developer roles in Germany, Finland, France and the Netherlands. It retrieves results page by page and saves a CSV file of listings that mention either **"relocation assistance"** or **"visa sponsorship"** in their descriptions. Results from each page are written to disk immediately so a partial CSV remains even if the run stops early.

### Run

```bash
python job_filter.py
```

The script writes `filtered_jobs.csv` in the current directory, appending matches after each page fetch. Pass `--max-pages N` to limit the number of pages fetched during a run.

During execution, progress messages indicate which page and job IDs are being processed and whether each POST request succeeds.
