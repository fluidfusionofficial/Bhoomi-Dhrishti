#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Wait for Service Health Checks
# Polls service health endpoints until all are ready
# ─────────────────────────────────────────────────────────────────────────────

MAX_WAIT=300  # 5 minutes
POLL_INTERVAL=5

# Core services to check
SERVICES=(
    "http://localhost:8001/health:parcel-identity"
    "http://localhost:8002/health:geospatial"
    "http://localhost:8003/health:revenue-records"
    "http://localhost:8004/health:registration"
    "http://localhost:8005/health:planning-zoning"
    "http://localhost:8006/health:fiscal"
    "http://localhost:8007/health:utilities"
    "http://localhost:8008/health:trust-engine"
    "http://localhost:8009/health:ml-inference"
    "http://localhost:8010/health:citizen-services"
    "http://localhost:8011/health:audit"
    "http://localhost:8012/health:notifications"
    "http://localhost:8013/health:search"
    "http://localhost:8014/health:analytics"
    "http://localhost:8015/health:interoperability"
    "http://localhost:8016/health:satellite"
)

echo "Waiting for services to become healthy..."
echo "Max wait time: ${MAX_WAIT}s"
echo ""

elapsed=0
all_healthy=false

while [ $elapsed -lt $MAX_WAIT ]; do
    healthy_count=0
    total_count=${#SERVICES[@]}

    for service_url in "${SERVICES[@]}"; do
        url="${service_url%%:*}"
        name="${service_url##*:}"

        if curl -s -f "$url" > /dev/null 2>&1; then
            ((healthy_count++))
            echo "  ✓ $name"
        else
            echo "  ⏳ $name (waiting...)"
        fi
    done

    echo "  Progress: $healthy_count/$total_count services healthy"

    if [ $healthy_count -eq $total_count ]; then
        all_healthy=true
        break
    fi

    echo ""
    sleep $POLL_INTERVAL
    ((elapsed+=POLL_INTERVAL))
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "✓ All services are healthy!"
    exit 0
else
    echo "⚠ Timeout waiting for services to become healthy"
    echo "  Some services may still be starting. Check logs with: make logs"
    exit 1
fi
