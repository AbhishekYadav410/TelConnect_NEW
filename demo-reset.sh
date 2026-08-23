#!/bin/bash
# Resets the platform to a clean pre-demo state.
# The database is wiped; demo accounts, knowledge base and a FRESH demo CSV
# (spike timestamped "right now") are recreated on the next backend start.
cd "$(dirname "$0")"
pkill -f "uvicorn app.main:app" 2>/dev/null
rm -f backend/data/tci.db backend/data/tci.db-wal backend/data/tci.db-shm backend/data/sample_complaints.csv
echo "Reset done. Start with ./run.sh, log in as admin and upload the demo dataset"
echo "(download link is on the Dataset upload page) - the full pipeline fires live."
