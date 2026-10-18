#!/bin/sh
# Startet ein Plugin-Skript mit dem ersten funktionierenden Python 3.
# Nötig für Windows: dort ist "python3" oft nur ein Store-Verweis, der nichts ausführt.
# Ohne Python passiert nichts (exit 0), damit Hooks nie die Arbeit blockieren.
script="$(dirname "$0")/$1"
shift
for py in python3 python; do
  if "$py" -c "import sys; sys.exit(sys.version_info < (3, 8))" >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done
if py -3 -c "" >/dev/null 2>&1; then
  exec py -3 "$script" "$@"
fi
exit 0
