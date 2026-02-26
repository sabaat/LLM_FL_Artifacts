#!/usr/bin/env python3
"""
Select the first N matched programs (by filename order) from a matched folder
produced by test_llm_original.py. Used by the artifact to fix the seed to 10 programs.
"""
import os
import sys
import shutil


def main():
    if len(sys.argv) < 4:
        print("Usage: python select_first_n_matched.py <matched_folder> <output_folder> <n>")
        sys.exit(1)

    matched_folder = sys.argv[1]
    output_folder = sys.argv[2]
    n = int(sys.argv[3])

    if not os.path.isdir(matched_folder):
        print(f"Error: matched folder not found: {matched_folder}")
        sys.exit(1)

    json_files = sorted([f for f in os.listdir(matched_folder) if f.lower().endswith(".json")])
    selected = json_files[:n]

    if len(selected) < n:
        print(f"Warning: only {len(selected)} JSON files in matched folder; requested {n}.")

    os.makedirs(output_folder, exist_ok=True)
    for f in selected:
        src = os.path.join(matched_folder, f)
        dst = os.path.join(output_folder, f)
        shutil.copy2(src, dst)

    print(f"Copied first {len(selected)} matched programs to {output_folder}")


if __name__ == "__main__":
    main()
