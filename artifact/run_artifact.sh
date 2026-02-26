#!/bin/bash
#
# Artifact pipeline: one script, two modes.
#
# Mode 1 (default): Find first N successful per SAM, generate SPMs, run test_llm, plot.
#   Prereqs: Buggy datasets at <artifact_dir>/python_buggy_dataset_<SAM> (included in artifact).
#
# Mode 2 (--eval-only): Use already-created firstN and spm_* variants; only run test_llm and plot.
#   Prereqs: artifact/first5_<SAM> (or firstN_<SAM>) and artifact/spm_<SAM>/{...} (and optionally spm_<SAM>_strength4 for graphs 2–3).
#
# Usage:
#   Full pipeline (find first N, generate mutants, test, plot):
#     ./run_artifact.sh <model_name> [N] [experiment_dir]
#     N = number of first successful projects per SAM (default: 5).
#     experiment_dir defaults to this artifact directory (self-contained).
#
#   Eval-only (use existing variants, run test_llm + plot):
#     ./run_artifact.sh --eval-only <model_name> [N] [artifact_dir]
#     N = number used for results labeling (default: 5).
#
# Run from the artifact directory (self-contained; all scripts and data live here).
#

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACT_DIR="$SCRIPT_DIR"
SAMS="BooleanLogic MisplacedReturn OffByOne OperatorSwap"
SPMS="commented variable dead_code variable_cumulative dead_code_cumulative"

# Parse --eval-only
EVAL_ONLY=0
if [ "$1" = "--eval-only" ]; then
  EVAL_ONLY=1
  shift
fi

MODEL_NAME="${1:?Usage: $0 [--eval-only] <model_name> [N] [experiment_dir|artifact_dir]}"
shift

# Parse optional N (default 5) and optional dir. opt1 can be N or dir; if N then opt2 can be dir.
set_n_and_dir() {
  local default_dir="$1"
  local opt1="$2"
  local opt2="$3"
  if [ -z "$opt1" ]; then
    N_FIRST=5
    PARSED_DIR="$default_dir"
  elif [ -n "$opt1" ] && [ "$opt1" -eq "$opt1" ] 2>/dev/null && [ "$opt1" -gt 0 ]; then
    N_FIRST="$opt1"
    PARSED_DIR="${opt2:-$default_dir}"
  else
    N_FIRST=5
    PARSED_DIR="${opt1:-$default_dir}"
  fi
}

if [ $EVAL_ONLY -eq 1 ]; then
  # -------------------------------------------------------------------------
  # Mode 2: Eval-only — use existing firstN and spm_*, run test_llm and plot
  # -------------------------------------------------------------------------
  set_n_and_dir "$SCRIPT_DIR" "$1" "$2"
  EVAL_ARTIFACT_DIR="$PARSED_DIR"
  cd "$EVAL_ARTIFACT_DIR"

  echo "============================================================"
  echo "Artifact (eval-only): run test_llm on existing SPM variants, then plot"
  echo "============================================================"
  echo "Model: $MODEL_NAME"
  echo "N (for results): $N_FIRST"
  echo "Artifact dir: $EVAL_ARTIFACT_DIR"
  echo ""

  for sam in $SAMS; do
    SPM_BASE="${EVAL_ARTIFACT_DIR}/spm_${sam}"
    SPM_BASE_4="${EVAL_ARTIFACT_DIR}/spm_${sam}_strength4"
    if [ ! -d "$SPM_BASE" ]; then
      echo "Skip SAM $sam: spm folder not found: $SPM_BASE"
      continue
    fi
    echo "=== SAM: $sam ==="
    for spm in $SPMS; do
      if [ -d "$SPM_BASE/$spm" ]; then
        echo "  test_llm on spm_${sam}/${spm} (strength 1)"
        python -u "$EVAL_ARTIFACT_DIR/test_llm.py" "$MODEL_NAME" "$SPM_BASE/$spm"
      else
        echo "  Skip $spm (not found)"
      fi
    done
    if [ -d "$SPM_BASE_4" ]; then
      for spm in $SPMS; do
        if [ -d "$SPM_BASE_4/$spm" ]; then
          echo "  test_llm on spm_${sam}_strength4/${spm} (strength 4)"
          python -u "$EVAL_ARTIFACT_DIR/test_llm.py" "$MODEL_NAME" "$SPM_BASE_4/$spm"
        fi
      done
    fi
    echo ""
  done

  echo "=== Generate results and 3 graphs ==="
  python "$EVAL_ARTIFACT_DIR/plot_artifact_results.py" "$EVAL_ARTIFACT_DIR" "$N_FIRST"
  echo "=== Done. See $EVAL_ARTIFACT_DIR/results_summary.txt and $EVAL_ARTIFACT_DIR/artifact_results*.png ==="
  exit 0
fi

# -------------------------------------------------------------------------
# Mode 1: Full pipeline — find first N, generate SPMs, test_llm, plot
# -------------------------------------------------------------------------
# Default experiment dir = artifact dir (self-contained; datasets live here)
set_n_and_dir "$ARTIFACT_DIR" "$1" "$2"
EXP_DIR="$PARSED_DIR"
cd "$EXP_DIR"

echo "============================================================"
echo "Artifact (full): find first $N_FIRST per SAM, generate SPMs, test_llm, plot"
echo "============================================================"
echo "Model: $MODEL_NAME"
echo "N (first successful projects per SAM): $N_FIRST"
echo "Experiment dir (buggy datasets): $EXP_DIR"
echo ""

for sam in $SAMS; do
  INPUT_DS="${EXP_DIR}/python_buggy_dataset_${sam}"
  MATCHED="${ARTIFACT_DIR}/matched_${sam}"
  FIRSTN="${ARTIFACT_DIR}/first${N_FIRST}_${sam}"
  SPM_BASE="${ARTIFACT_DIR}/spm_${sam}"

  if [ ! -d "$INPUT_DS" ]; then
    echo "Skip SAM $sam: dataset not found: $INPUT_DS"
    continue
  fi

  echo "=== SAM: $sam ==="
  echo "  Step 1: test_llm_original -> matched (stop after $N_FIRST matches)"
  python -u "$ARTIFACT_DIR/test_llm_original.py" "$MODEL_NAME" "$INPUT_DS" "$MATCHED" "$N_FIRST"

  echo "  Step 2: Select first $N_FIRST matched -> first${N_FIRST}_${sam}"
  python "$ARTIFACT_DIR/select_first_n_matched.py" "$MATCHED" "$FIRSTN" "$N_FIRST"

  NUM=$(find "$FIRSTN" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l)
  if [ "$NUM" -lt 1 ]; then
    echo "  No matched programs for $sam; skip SPM."
    continue
  fi
  echo "  Using $NUM programs for SPM."

  echo "  Step 3a: Generate all 5 SPMs (mutation strength 1) -> spm_${sam}/"
  python -u "$ARTIFACT_DIR/generate_mutants.py" "$FIRSTN" "$SPM_BASE" 1 "$MODEL_NAME"

  echo "  Step 4a: test_llm on each of 5 SPM folders (strength 1) for $sam"
  for spm in $SPMS; do
    python -u "$ARTIFACT_DIR/test_llm.py" "$MODEL_NAME" "$SPM_BASE/$spm"
  done

  SPM_BASE_4="${ARTIFACT_DIR}/spm_${sam}_strength4"
  echo "  Step 3b: Generate all 5 SPMs (mutation strength 4) -> spm_${sam}_strength4/"
  python -u "$ARTIFACT_DIR/generate_mutants.py" "$FIRSTN" "$SPM_BASE_4" 4 "$MODEL_NAME"

  echo "  Step 4b: test_llm on each of 5 SPM folders (strength 4) for $sam"
  for spm in $SPMS; do
    python -u "$ARTIFACT_DIR/test_llm.py" "$MODEL_NAME" "$SPM_BASE_4/$spm"
  done
  echo ""
done

echo "=== Generate results and 3 graphs (SPM effect, strength 1 vs 4, mutation types) ==="
python "$ARTIFACT_DIR/plot_artifact_results.py" "$ARTIFACT_DIR" "$N_FIRST"
echo "=== Done. See $ARTIFACT_DIR/results_summary.txt and $ARTIFACT_DIR/artifact_results*.png ==="
