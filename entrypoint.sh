#!/bin/sh
# Runs as root at container start (before USER is dropped) so it can fix
# ownership of a Railway Volume mounted at /data -- volumes are attached at
# runtime, after the image is built, so nothing in the Dockerfile's build-time
# `chown -R appuser:appuser /app` step can reach them. Without this, /data
# exists and is readable by appuser but not writable, which is exactly the
# "is_dir() true, os.access(W_OK) false" split db.py's persistence check
# already anticipates -- found 2026-07-09 when a fresh volume attach still
# reported persistent=false.
set -e
if [ -d /data ]; then
  chown -R appuser:appuser /data
fi
exec gosu appuser "$@"
