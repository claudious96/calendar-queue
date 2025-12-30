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

SUPPORTED_PYTHON_VERSIONS=("3.10" "3.11" "3.12" "3.13" "3.14" "3.14t")

ERROR=0

for spv in "${SUPPORTED_PYTHON_VERSIONS[@]}"
do
    # check if python version string ends with 't' (for 'threaded')
    # if yes just create a symlink to the non-threaded lockfile
    if [[ $spv == *"t" ]]; then
        base_spv=${spv%"t"}
        echo "Creating symlink for py$spv.lock to py$base_spv.lock"
        ln -sf "py$base_spv.lock" "py$spv.lock"
        continue
    fi

    echo "Updating lockfile for py$spv.lock"

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