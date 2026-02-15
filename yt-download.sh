#!/bin/bash
# Удобный запускалка для YouTube Downloader

cd "$(dirname "$0")"
python3 youtube_downloader.py "$@"
