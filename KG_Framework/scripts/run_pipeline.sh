#!/usr/bin/env bash

set -euo pipefail

python -m kg_framework.cli "${1:-run-all}"
