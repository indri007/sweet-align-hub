#!/bin/bash
set -e

echo "============================================================"
echo "  JobMatch AI — container startup"
echo "============================================================"

# data_preparation.py is idempotent: it checks existing row/doc counts
# and skips insertion if the database/vector store is already populated.
# So it's safe to always run it here, whether the backend is local
# (SQLite + ChromaDB) or cloud (Aiven MySQL + Qdrant).
echo "[entrypoint] Running data preparation (safe to skip if already populated)..."
if ! python data_preparation.py; then
    echo "[entrypoint] WARNING: data preparation failed or was skipped."
    echo "[entrypoint] The app will still start, but job matching may not work"
    echo "[entrypoint] until the database/vector store is populated."
fi

echo "[entrypoint] Starting Streamlit..."
exec streamlit run app.py \
    --server.port="${STREAMLIT_SERVER_PORT:-8501}" \
    --server.address="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
