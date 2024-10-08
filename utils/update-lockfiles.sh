#!/usr/bin/env bash

echo "Checking pdm is installed"

_=$(which pdm)

if [[ $? -ne 0 ]]; then
    echo "pdm not found. Please install it to update the lockfiles."
    echo "See: https://pdm-project.org/en/latest/"
    exit 1
else
    PDM_VERSION=$(pdm --version)
    echo "Found $PDM_VERSION"
fi

SUPPORTED_PYTHON_VERSIONS=("3.10" "3.11" "3.12" "3.13")

ERROR=0

for spv in "${SUPPORTED_PYTHON_VERSIONS[@]}"
do
    pdm lock --python="==$spv.*" --lockfile=py$spv.lock

    if [[ $? -ne 0 ]]; then
        ERROR=$(($ERROR + num2))
    fi
done

if [[ $ERROR -eq 0 ]]; then
    echo "Lockfiles successfully updated."
else
    echo "An error occurred while updating lockfiles."
fi