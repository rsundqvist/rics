#!/bin/bash

echo "---------- run-invocations.sh -----------"
echo "1/7: Clean ------------------------------"
inv clean
echo "2/7: Format code ------------------------"
inv format
echo "3/7: Test -------------------------------"
inv tests
echo "4/7: Lint -------------------------------"
inv lint
echo "5/7: Typecheck (mypy) -------------------"
inv mypy
echo "6/7: Coverage report (open browser) -----"
inv coverage -f=html -o
echo "7/7: Generate docs (open browser) -------"
inv docs -o
echo "---------------- Finished ---------------"
