#!/usr/bin/env bash

LOG_PREFIX="[>>>]"

function check_deps {
    local log_missing=false
    if [ "$1" == "--log" ] ; then
        log_missing=true
        shift
    fi

    exit_code=0
    while [ $# -gt 0 ] ; do
        if ! command -v "$1" &> /dev/null ; then
            exit_code=1
            if [ "$log_missing" == true ] ; then
                log "Dependency '$1' is missing"
            fi
        fi
        shift
    done
    return $exit_code
}

function log {
    echo "${LOG_PREFIX} $@"
}

function log_indent {
    sed "s/^/    /g"
}

function log_box_indent {
    log '  ╭──────'
    sed "s/^/${LOG_PREFIX}   │ /g"
    log '  ╰──────'
}

function indent {
    sed "s/^/    /g"
}

function box_indent {
    echo '  ╭──────'
    sed "s/^/  │ /g"
    echo '  ╰──────'
}

function run_boxed {
    log "Running command '$@'"
    "$@" | log_box_indent
}

function run_with_summary {
    exit_code=0
    results=()
    while [ "$#" -gt 0 ] ; do
        "$1"
        if [ $? -ne 0 ] ; then
            exit_code=$?
            results+=("   FAIL: $1")
        else
            results+=("SUCCESS: $1")
        fi
        shift
    done

    for result in "${results[@]}" ; do
        log "RESULT: ${result}"
    done
}
