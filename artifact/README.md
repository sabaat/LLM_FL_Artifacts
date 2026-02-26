# Artifact: Fault Localization Under SAM and SPM

This artifact mirrors the original paper pipeline structure and provides results that speak to **RQ1–RQ3** of the paper (see `ARTIFACT_EVALUATION.md` in the parent directory for the mapping: RQ1 = robustness to SPMs, RQ2 = SPM types/strengths, RQ3 = fault location; RQ4/RQ5 require the full paper pipeline).

- **4 SAMs** (Semantic-Altering Mutations / bug types): **BooleanLogic**, **MisplacedReturn**, **OffByOne**, **OperatorSwap** (as in `final_script_python.sh`).
- For each SAM: run **test_llm_original** on that buggy dataset → programs where the LLM **successfully localized the fault**.
- Take the **first N** of those (per SAM; N defaults to 10, configurable).
- Apply **all 5 SPMs** to each SAM’s N programs: **commented**, **variable**, **dead_code**, **variable_cumulative**, **dead_code_cumulative** (as in `generate_mutants.py`).
- Run **test_llm** on each SPM folder for each SAM.
- **Results**: for each SAM, how many of the N were **still localized** after each SPM (table + graph).

Designed to run on a single machine (e.g. MacBook) with a small Ollama model.

## Requirements

- **Docker** — to build and run the artifact (see **`ARTIFACT_EVALUATION.md`** in the parent directory for step-by-step commands).
- **Ollama** — installed and running on the **host**; pull a model, e.g. `ollama pull llama3.2:3b`. The container connects to Ollama on the host; no Python or pip installation on your machine.

## Self-contained artifact

This folder is **self-contained** for submission: all scripts and the four buggy datasets are included. No need for the parent repository directory.

**Included:**
- Scripts: `run_artifact.sh`, `test_llm_original.py`, `test_llm.py`, `generate_mutants.py`, `select_first_n_matched.py`, `plot_artifact_results.py`
- Datasets: `python_buggy_dataset_BooleanLogic`, `python_buggy_dataset_MisplacedReturn`, `python_buggy_dataset_OffByOne`, `python_buggy_dataset_OperatorSwap` (each with JSON files: `instruction`, `buggy_code`, `line_no`, `line_no_percent`)

## How to run (Docker)

All run instructions are in **`ARTIFACT_EVALUATION.md`** (parent directory). Summary:

1. **Build:** From repo root: `docker build -t artifact-eval ./artifact`
2. **Ollama on host:** Start Ollama and pull a model (e.g. `ollama pull llama3.2:3b`).
3. **Quick eval (eval-only):** From this directory:  
   `docker run --rm -it --network host -v "$(pwd)":/artifact -w /artifact artifact-eval ./run_artifact.sh --eval-only llama3.2:3b`  
   (On Mac/Windows use `-e OLLAMA_HOST=http://host.docker.internal:11434` and omit `--network host`.)
4. **Full pipeline:** Same `docker run` but `./run_artifact.sh llama3.2:3b 5` (no `--eval-only`).

For eval-only, this directory should already contain pre-generated `spm_<SAM>/` folders (e.g. from a provided artifact or a previous full run).

## Outputs

- **`results_summary.txt`** – For each SAM: for each of the 5 SPMs, “X / N” still localized (N = the first-N value you chose, or fewer if fewer matched).
- **`artifact_results.png`** – Grouped bar chart: one group per SAM, 5 bars per group (one per SPM), showing how many of N were still localized after that SPM.

## SAMs and SPMs (summary)

- **4 SAMs** (bug types): BooleanLogic, MisplacedReturn, OffByOne, OperatorSwap. Your original script uses these four; if you prefer to use only three, edit `SAMS` in `run_artifact.sh` and the `SAMS` list in `plot_artifact_results.py`.
- **5 SPMs**: commented, variable, dead_code, variable_cumulative, dead_code_cumulative (semantic-preserving mutations from `generate_mutants.py`).

## Notes

- The pipeline uses **Ollama** only (no API keys). Ollama runs on the host; the container connects to it.
- If a SAM has fewer than N matched programs, the summary and plot use the actual count for that SAM.
- Default N = 5. Results are written into the mounted directory (`results_summary.txt`, `artifact_results*.png`).
