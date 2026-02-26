# Artifact Evaluation Guide

This artifact reproduces the paper's fault-localization evaluation
under:

-   **SAMs** (Semantic-Altering Mutations)
-   **SPMs** (Semantic-Preserving Mutations)

It directly supports **RQ1--RQ3**.\
RQ4--RQ5 require running the full pipeline used in paper (see end).

------------------------------------------------------------------------

# Research Questions Supported

  ----------------------------------------------------------------------------------------
  RQ           What You Run                 What To Look At
  ------------ ---------------------------- ----------------------------------------------
  **RQ1** --   Quick evaluation             `artifact_results.png` + strength 1 section in
  Robustness                                `results_summary.txt`
  to SPMs                                   

  **RQ2** --   Quick evaluation (if         `artifact_results_strength_comparison.png` +
  Effect of    strength-4 data exists)      `artifact_results_mutation_types.png`
  mutation                                  
  type &                                    
  strength                                  

  **RQ3** --   Quick evaluation             `artifact_results_windowed.png`
  Effect of                                 
  fault                                     
  location                                  
  ----------------------------------------------------------------------------------------

------------------------------------------------------------------------

# Quick Evaluation (15--20 Minutes)

Runs evaluation on pre-generated data.

------------------------------------------------------------------------

## Requirements

-   **Docker**
    -   Check: `docker --version`
    -   **Linux (Ubuntu/Debian):** `curl -fsSL https://get.docker.com | sh` then `sudo usermod -aG docker $USER` (log out and back in). Or install [Docker Engine](https://docs.docker.com/engine/install/).
    -   **macOS / Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) — download and install from docker.com.

-   **Ollama installed on host**
    -   **Linux:** `curl -fsSL https://ollama.com/install.sh | sh` (or see [ollama.com](https://ollama.com/download)).
    -   **macOS:** Download from [ollama.com/download](https://ollama.com/download) or `brew install ollama`.
    -   **Windows:** Download installer from [ollama.com/download](https://ollama.com/download).
    -   Then start Ollama (Step 2) and pull a model: `ollama pull llama3.2:3b`.

------------------------------------------------------------------------

# Step 1 --- Build Docker Image

From repository root:

``` bash
docker build -t artifact-eval ./artifact
```

Expected output:

    Successfully built ...
    Successfully tagged artifact-eval:latest

![Successful Docker Build](images/docker_success.png)

------------------------------------------------------------------------

# Step 2 --- Start Ollama (Host Machine)

``` bash
ollama serve
```

In another terminal:

``` bash
ollama pull llama3.2:3b
```

Expected:

    Listening on 127.0.0.1:11434

![Successful ollama pull](images/pull_success.png)

------------------------------------------------------------------------

# Step 3 --- Run Quick Evaluation (Eval-Only Mode)

## Linux

``` bash
cd artifact
docker run --rm -it --network host \
  -v "$(pwd)":/artifact \
  -w /artifact \
  artifact-eval \
  ./run_artifact.sh --eval-only llama3.2:3b
```

## Mac / Windows

``` bash
cd artifact
chmod +x run_artifact.sh 
docker run --rm -it \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -v "$(pwd)":/artifact \
  -w /artifact \
  artifact-eval \
  ./run_artifact.sh --eval-only llama3.2:3b
```

Expected terminal output at the start of run:

![Successful Run Start](images/run_start.png)

    Wait for 10 to 15 minutes for run to complete. This will be at the end of a successful run.

![Successful Run End](images/run_end.png)

------------------------------------------------------------------------

# Expected Output Files

After completion, the `artifact/` directory contains:

-   `results_summary.txt`
-   `artifact_results.png`
-   `artifact_results_strength_comparison.png` 
-   `artifact_results_mutation_types.png`
-   `artifact_results_windowed.png`

![Successful File Generation](images/success_files.png)

------------------------------------------------------------------------

# Interpreting Results

## RQ1 -- Robustness to SPMs

Open:

    artifact_results.png

Example:
![Artifact Results](artifact/artifact_results.png)

------------------------------------------------------------------------

## RQ2 -- Effect of Mutation Type & Strength

Open:

    artifact_results_strength_comparison.png
    artifact_results_mutation_types.png

Example:
![Mutation Strength Analysis](artifact/artifact_results_strength_comparison.png)
![Mutation Type Analysis](artifact/artifact_results_mutation_types.png)


------------------------------------------------------------------------

## RQ3 -- Effect of Fault Location

Open:

    artifact_results_windowed.png

Example:
![Fault location Analysis](artifact/artifact_results_windowed.png)

------------------------------------------------------------------------

# Optional --- Full Pipeline

Regenerates SPMs and recomputes first N programs.

``` bash
./run_artifact.sh llama3.2:3b 5
```

Default `N = 5`.

------------------------------------------------------------------------

# Java Pipeline

Requires Java installed on host.

``` bash
cd artifact_java
chmod +x run_artifact.sh run-experiments.sh
./run_artifact.sh llama3.2:3b
```

------------------------------------------------------------------------

# Full Paper Reproduction (RQ4, RQ5)

Run:

``` bash
./run_paper_python.sh llama3.2:3b
```

(Long runtime. Will require a GPU)

------------------------------------------------------------------------

# Adding Your Own Python or Java Projects

You can run the pipeline on your own buggy programs. Prepare the data in the format below, place it where the pipeline expects it, then run the **full pipeline** (not eval-only).

------------------------------------------------------------------------

## Required data format

Each **buggy program** is one JSON file. The pipeline reads all `.json` files in each dataset folder.

**Required fields in every JSON file:**

| Field              | Type   | Description |
|--------------------|--------|-------------|
| `instruction`      | string | What the code is supposed to do (the intended behavior). Shown to the LLM as the task. |
| `buggy_code`       | string | The full source code of the program **containing the bug** (Python or Java). |
| `line_no`          | number | The **exact line number** (1-based) where the bug is located in `buggy_code`. |
| `line_no_percent`  | string | Position of the bug as a percentage of file length, for windowed analysis. Use a number with optional `%`, e.g. `"25"`, `"50%"`, `"75.5"`. Values &lt; 25 → window 0–25%, &lt; 50 → 25–50%, &lt; 75 → 50–75%, else 75–100%. |

**Example (minimal):**

``` json
{
  "instruction": "Return the sum of two integers.",
  "buggy_code": "def add(a, b):\n    return a - b\n",
  "line_no": 2,
  "line_no_percent": "100"
}
```

Filenames can be anything ending in `.json` (e.g. `project1_bug1.json`, `123_4.json`).

------------------------------------------------------------------------

## Where to add the data

The pipeline looks for **one folder per bug type (SAM)**. Each folder must contain only JSON files in the format above.

**Python:**

- **Option A — Inside the artifact:**  
  Add these folders (with your JSONs inside) under the `artifact/` directory. Then the default run uses them.
- **Option B — Custom directory:**  
  Put the folders in a separate directory (e.g. `my_python_bugs/`). You will pass this path as the **experiment_dir** when running (see below).

**Java:**


- **Option A — Inside the artifact:**  
  Add these folders under `artifact_java/`.
- **Option B — Custom directory:**  
  Put the folders elsewhere and pass that path as the experiment directory to the Java `run_artifact.sh` (third argument).

------------------------------------------------------------------------

## How to run with your data

**Python (Docker, full pipeline):**

If your data is **inside** `artifact/` (Option A), from the `artifact` directory:

``` bash
# Linux
docker run --rm -it --network host -v "$(pwd)":/artifact -w /artifact artifact-eval ./run_artifact.sh llama3.2:3b 5

# Mac/Windows
docker run --rm -it -e OLLAMA_HOST=http://host.docker.internal:11434 -v "$(pwd)":/artifact -w /artifact artifact-eval ./run_artifact.sh llama3.2:3b 5
```

If your data is in a **custom directory** (Option B), mount that directory and pass it as the third argument. Example: data in `/path/to/my_python_bugs` (containing `python_buggy_dataset_OffByOne/`, etc.):

``` bash
# Linux
docker run --rm -it --network host \
  -v "$(pwd)":/artifact \
  -v /path/to/my_python_bugs:/data \
  -w /artifact \
  artifact-eval \
  ./run_artifact.sh llama3.2:3b 5 /data

# Mac/Windows: add -e OLLAMA_HOST=http://host.docker.internal:11434, omit --network host
```

**Java (on host, full pipeline):**

From `artifact_java/`, with your dataset folders inside `artifact_java/` (Option A):

``` bash
cd artifact_java
./run_artifact.sh llama3.2:3b 5
```

With a **custom directory** (Option B), e.g. `/path/to/my_java_bugs`:

``` bash
cd artifact_java
./run_artifact.sh llama3.2:3b 5 /path/to/my_java_bugs
```

The pipeline will: (1) run the LLM on each JSON to find the bug line, (2) keep the first N where the LLM was correct, (3) generate SPM variants, (4) re-run the LLM, (5) write `results_summary.txt` and the graphs into the artifact directory (Python) or `artifact_java/` (Java).
