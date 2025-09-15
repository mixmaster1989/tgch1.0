#!/usr/bin/env bash
set -euo pipefail

# Использование: ./scripts/trim_log.sh /path/to/logfile [max_bytes]
# По умолчанию max_bytes = 104857600 (100 MB)

LOG_FILE="${1:-}"
MAX_BYTES="${2:-104857600}"

if [[ -z "${LOG_FILE}" ]]; then
  echo "Usage: $0 /path/to/logfile [max_bytes]" >&2
  exit 1
fi

if [[ ! -f "${LOG_FILE}" ]]; then
  echo "Log file not found: ${LOG_FILE}" >&2
  exit 0
fi

CURRENT_SIZE=$(stat -c%s "${LOG_FILE}")

if (( CURRENT_SIZE <= MAX_BYTES )); then
  echo "No trim needed (${CURRENT_SIZE} <= ${MAX_BYTES})"
  exit 0
fi

# Обрезаем, оставляя последние MAX_BYTES
TMP_FILE=$(mktemp)

# tail -c выводит последние N байт
# Используем LC_ALL=C для скорости
LC_ALL=C tail -c "${MAX_BYTES}" "${LOG_FILE}" > "${TMP_FILE}" || true

# Переносим поверх исходного
cat "${TMP_FILE}" > "${LOG_FILE}"
rm -f "${TMP_FILE}"

echo "Trimmed $(basename "${LOG_FILE}") to ${MAX_BYTES} bytes" 