#!/usr/bin/env bash
set -e
python -m src.b1_cli --task "Compute (23*19)+sqrt(144) and save to calc.txt" --policy cases/policies/v1.yaml