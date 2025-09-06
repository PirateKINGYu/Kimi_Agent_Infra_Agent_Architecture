#!/usr/bin/env bash
set -e
python -m src.b2_runner --cases cases/cases.jsonl --policy cases/policies/v1.yaml --out-base runs
python -m src.b2_eval --runs runs --out runs/summary_v1.csv --cases cases/cases.jsonl