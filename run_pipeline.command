#!/bin/bash
# CED 301 — Playlist Transcription Runner
# Double-click this file in Finder to start the pipeline.
# It will process all 35 videos from the YouTube playlist,
# skipping any that are already done.

# Keep terminal open on error
set -e
trap 'echo ""; echo "❌  Pipeline failed. Check output above."; read -p "Press Enter to close..."' ERR

TOOLBOX="$(cd "$(dirname "$0")" && pwd)"
cd "$TOOLBOX"

echo "============================================================"
echo "  CED 301 — Transcrição Automática de Playlist"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""
echo "  Diretório: $TOOLBOX"
echo ""

# Activate venv
source "$TOOLBOX/.venv/bin/activate"
echo "  Python: $(python --version)"
echo ""

# Run the playlist runner
python src/playlist_runner.py "$@"

echo ""
echo "============================================================"
echo "  Pipeline concluído. Abra o Cowork para escrever os capítulos."
echo "============================================================"
echo ""
read -p "Pressione Enter para fechar..."
