#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if git is installed
if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed. Please install it and try again."
    exit 1
fi

# Get the absolute path to the scenario directory.
WORK_DIR=$(realpath "$(dirname "$0")")

# Clone or update the termux-web-scraper repository.
if [ -d "$WORK_DIR/termux-web-scraper" ]; then
  echo "Updating termux-web-scraper..."
  git -C "$WORK_DIR/termux-web-scraper" pull --rebase
else
  echo "Cloning termux-web-scraper..."
  # TODO: specify a version of termux-web-scraper
  git clone https://github.com/kpliuta/termux-web-scraper.git "$WORK_DIR/termux-web-scraper"
fi

# TODO: change a timeout to once in 10 min
# Execute the scraper script in a loop with a 10 seconds timeout.
"$WORK_DIR/termux-web-scraper/scripts/run.sh" \
    --work-dir "$WORK_DIR" \
    --scenario-file src/main.py \
    --upgrade \
    --loop \
    --loop-timeout 10 \
    --loop-error-ignore \
    --output-dir /sdcard/sinotrack-alert-monitor:/mnt/scraper/out
