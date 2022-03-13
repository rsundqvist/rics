#!/bin/bash

echo "---------- run-invocations.sh -----------"
echo "1/7: Clean ------------------------------"
poetry run inv clean
echo "2/7: Format code ------------------------"
poetry run inv format
echo "3/7: Test -------------------------------"
poetry run inv tests
echo "4/7: Lint -------------------------------"
poetry run inv lint
echo "5/7: Typecheck (mypy) -------------------"
poetry run inv mypy
echo "6/7: Coverage report (open browser) -----"
poetry run inv coverage -f=html -o
echo "7/7: Generate docs (open browser) -------"
poetry run inv docs -o
echo "---------------- Finished ---------------"
