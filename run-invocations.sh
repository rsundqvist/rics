#!/bin/bash
set -e

echo "---------- run-invocations.sh -----------"
echo "1/7: Clean ------------------------------"
inv clean
echo "2/7: Format code ------------------------"
inv format
echo "3/7: Lint -------------------------------"
inv lint
echo "4/7: Typecheck (mypy) -------------------"
inv mypy
echo "5/7: Test -------------------------------"
inv tests
echo "6/7: Coverage report --------------------"
inv coverage -f=html
echo "7/7: Generate docs ----------------------"
inv docs
echo "---------------- Finished ---------------"
