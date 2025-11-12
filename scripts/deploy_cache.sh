#!/bin/bash
# DASE Cache System - Deployment Script for Linux/Mac
#
# This script:
# 1. Creates cache directory structure
# 2. Runs warmup to pre-populate cache
# 3. Validates cache integrity
# 4. Shows cache statistics
#
# Usage: ./deploy_cache.sh

set -e  # Exit on error

echo "============================================================"
echo "DASE CACHE SYSTEM - DEPLOYMENT"
echo "============================================================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found in PATH"
    exit 1
fi

echo ""
echo "[1/4] Checking cache directory structure..."
if [ ! -d "cache" ]; then
    echo "Creating cache directory..."
    mkdir -p cache
fi

# Initialize cache manager (creates structure)
python3 -c "import sys; sys.path.insert(0, 'backend'); from cache import CacheManager; CacheManager(root='./cache')"
echo "[OK] Cache structure ready"

echo ""
echo "[2/4] Running cache warmup..."
python3 backend/cache/warmup.py --root ./cache

echo "[OK] Cache warmed up"

echo ""
echo "[3/4] Validating cache integrity..."
if ! python3 backend/cache/dase_cache_cli.py --root ./cache validate; then
    echo "Warning: Some cache entries may be corrupted"
    echo "Continuing anyway..."
fi

echo ""
echo "[4/4] Displaying cache statistics..."
python3 backend/cache/dase_cache_cli.py --root ./cache stats

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "Cache is ready for use."
echo ""
echo "Common commands:"
echo "  python3 backend/cache/dase_cache_cli.py ls"
echo "  python3 backend/cache/dase_cache_cli.py stats"
echo "  python3 backend/cache/warmup.py"
echo ""

exit 0
