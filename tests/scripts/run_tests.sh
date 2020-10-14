#!/bin/bash
set -eu
this_dir="$(dirname $0)"

# Default argument values
COVERAGE=0

# Get arguments
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --coverage)
        COVERAGE=1
        shift # past argument
        ;;
        *)    # unknown option
        POSITIONAL+=("$1") # save it in an array for later
        shift # past argument
        ;;
    esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters


test_dir="$(readlink -f $this_dir/..)"
if [ "$#" -ge 1 ]; then
    test_dir="$(readlink -f $this_dir/../$1)"

    if [ ! -e "$test_dir" ]; then
        echo "No such file or directory: $test_dir"
        exit 1
    fi

    echo "Running only tests in $test_dir"
else
    echo "Running all tests in $test_dir"
fi

PARALLEL=""
NUM_PROC=$(nproc)
if [ $NUM_PROC -gt 1 -a "${PLUMA_ENV:-}" != "CI" ]; then
    echo "Running tests in parallel on $NUM_PROC cores"
    PARALLEL="-n $NUM_PROC"
fi

test_command="-m pytest $PARALLEL "$test_dir

echo $@
if [ $COVERAGE -eq 1 ]; then
    echo "Running coverage"
    # Don't fail coverage if some test fail
    coverage run --source=pluma $test_command || true
    coverage xml
else
    echo "Running tests"
    python3 $test_command -v
fi
