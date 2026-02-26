#!/bin/bash
#
# Reproduce full paper results for Python (all matched programs, mutation strengths 1,2,4,6,8).
# Run from the artifact directory. Usage: ./run_paper_python.sh <model_name>
# Requires: python_buggy_dataset_<SAM> and scripts in this directory.
#
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
  echo "Usage: $0 <model_name>"
  exit 1
fi
MODEL_NAME="$1"

echo "Running full paper pipeline (Python) with model: $MODEL_NAME"

python test_llm_original.py "$MODEL_NAME" "$SCRIPT_DIR/python_buggy_dataset_BooleanLogic" "$SCRIPT_DIR/python_buggy_dataset_boolean_logic_matched_$MODEL_NAME"
python test_llm_original.py "$MODEL_NAME" "$SCRIPT_DIR/python_buggy_dataset_MisplacedReturn" "$SCRIPT_DIR/python_buggy_dataset_misplaced_return_matched_$MODEL_NAME"
python test_llm_original.py "$MODEL_NAME" "$SCRIPT_DIR/python_buggy_dataset_OffByOne" "$SCRIPT_DIR/python_buggy_dataset_off_by_one_matched_$MODEL_NAME"
python test_llm_original.py "$MODEL_NAME" "$SCRIPT_DIR/python_buggy_dataset_OperatorSwap" "$SCRIPT_DIR/python_buggy_dataset_operator_swap_matched_$MODEL_NAME"

for STR in 1 2 4 6 8; do
  python generate_mutants.py "$SCRIPT_DIR/python_buggy_dataset_misplaced_return_matched_$MODEL_NAME" "$SCRIPT_DIR/$MODEL_NAME-mutated_python_MisplacedReturn_$STR" "$STR" "$MODEL_NAME"
  python generate_mutants.py "$SCRIPT_DIR/python_buggy_dataset_operator_swap_matched_$MODEL_NAME" "$SCRIPT_DIR/$MODEL_NAME-mutated_python_OperatorSwap_$STR" "$STR" "$MODEL_NAME"
  python generate_mutants.py "$SCRIPT_DIR/python_buggy_dataset_off_by_one_matched_$MODEL_NAME" "$SCRIPT_DIR/$MODEL_NAME-mutated_python_OffByOne_$STR" "$STR" "$MODEL_NAME"
  python generate_mutants.py "$SCRIPT_DIR/python_buggy_dataset_boolean_logic_matched_$MODEL_NAME" "$SCRIPT_DIR/$MODEL_NAME-mutated_python_BooleanLogic_$STR" "$STR" "$MODEL_NAME"
done

SAMS="OperatorSwap BooleanLogic MisplacedReturn OffByOne"
SPMS="commented variable dead_code variable_cumulative dead_code_cumulative"
for STR in 1 2 4 6 8; do
  for sam in $SAMS; do
    BASE="$SCRIPT_DIR/$MODEL_NAME-mutated_python_${sam}_$STR"
    for spm in $SPMS; do
      python test_llm.py "$MODEL_NAME" "$BASE/$spm"
    done
  done
done

echo "Done. Full paper pipeline (Python) completed. Results are in the mutated folders and test_llm outputs (success.txt/fail.txt per SPM folder)."
