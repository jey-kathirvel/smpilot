#!/usr/bin/env bash
set -u

base_url="${1:-https://smpilot.ads-ai.in}"
base_url="${base_url%/}"
failures=0

check_route() {
  path="$1"
  status="$(curl --silent --show-error --location --output /dev/null --write-out '%{http_code}' --max-time 20 "${base_url}${path}" || true)"
  case "$status" in
    2??|3??) printf 'PASS %-20s HTTP %s\n' "$path" "$status" ;;
    *) printf 'FAIL %-20s HTTP %s\n' "$path" "${status:-000}"; failures=$((failures + 1)) ;;
  esac
}

printf 'SMPilot production smoke check: %s\n' "$base_url"
for route in / /login /signup /health /manifest.json /service-worker.js; do
  check_route "$route"
done

health_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 20 "${base_url}/health" || true)"
printf 'Application health: HTTP %s\n' "${health_status:-000}"

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files smpilot.service --no-legend 2>/dev/null | grep -q '^smpilot.service'; then
  service_status="$(systemctl is-active smpilot.service 2>/dev/null || true)"
  printf 'Service status: %s\n' "$service_status"
  [ "$service_status" = "active" ] || failures=$((failures + 1))
else
  printf 'Service status: not available in this environment\n'
fi

if command -v git >/dev/null 2>&1 && git -C /opt/smpilot rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Deployed Git commit: %s\n' "$(git -C /opt/smpilot rev-parse HEAD)"
else
  printf 'Deployed Git commit: not available in this environment\n'
fi

if [ "$failures" -ne 0 ]; then
  printf 'Smoke check failed: %s check(s) failed.\n' "$failures"
  exit 1
fi
printf 'Smoke check passed.\n'
