#!/bin/bash
# ETL Mapping Engine - API Usage Examples
# Demonstrates REST API interactions for data ingestion

BASE_URL="http://localhost:8005"
API_BASE="${BASE_URL}/ingest"

echo "======================================================================"
echo "Bhoomi Dhrishti - ETL Mapping Engine API Examples"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Example 1: List available source mappings
echo -e "${BLUE}Example 1: List Available Source Mappings${NC}"
echo "----------------------------------------------------------------------"
echo "Request: GET ${API_BASE}/sources"
echo ""

curl -s "${API_BASE}/sources" | jq '.'
echo ""
echo ""

# Example 2: Get mapping configuration
echo -e "${BLUE}Example 2: Get Mapping Configuration${NC}"
echo "----------------------------------------------------------------------"
echo "Request: GET ${API_BASE}/mappings/tn_rural"
echo ""

curl -s "${API_BASE}/mappings/tn_rural" | jq -r '.content' | head -n 20
echo "... (truncated)"
echo ""
echo ""

# Example 3: Upload and ingest data (Revenue RoR)
echo -e "${BLUE}Example 3: Upload and Ingest Revenue RoR Data${NC}"
echo "----------------------------------------------------------------------"
echo "Request: POST ${API_BASE}/revenue_ror?state_code=tn&context=rural"
echo ""

# Check if sample file exists
SAMPLE_FILE="../data/samples/tn_revenue_sample.csv"
if [ -f "$SAMPLE_FILE" ]; then
    echo "Uploading: $SAMPLE_FILE"

    RESPONSE=$(curl -s -X POST "${API_BASE}/revenue_ror?state_code=tn&context=rural&conflict_strategy=update" \
        -F "file=@${SAMPLE_FILE}")

    echo "$RESPONSE" | jq '.'

    # Extract job_id for next example
    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
    echo ""
    echo -e "${GREEN}✓ Job ID: ${JOB_ID}${NC}"
else
    echo -e "${YELLOW}⚠ Sample file not found: ${SAMPLE_FILE}${NC}"
    echo "Skipping upload example"
    JOB_ID="example-job-id"
fi

echo ""
echo ""

# Example 4: Check job status
if [ "$JOB_ID" != "example-job-id" ] && [ "$JOB_ID" != "null" ]; then
    echo -e "${BLUE}Example 4: Check Job Status${NC}"
    echo "----------------------------------------------------------------------"
    echo "Request: GET ${API_BASE}/status/${JOB_ID}"
    echo ""

    curl -s "${API_BASE}/status/${JOB_ID}" | jq '.'
    echo ""
    echo ""
fi

# Example 5: Upload with conflict strategy = ignore
echo -e "${BLUE}Example 5: Upload with Conflict Strategy = Ignore${NC}"
echo "----------------------------------------------------------------------"
echo "Request: POST ${API_BASE}/revenue_ror?conflict_strategy=ignore"
echo ""
echo "This will skip duplicate records instead of updating them."
echo ""

# Example 6: Ingest SRO registration data
echo -e "${BLUE}Example 6: Ingest SRO Registration Data${NC}"
echo "----------------------------------------------------------------------"
echo "Request: POST ${API_BASE}/sro_registration?state_code=tn&context=sro"
echo ""
echo "Upload SRO sale deed data with:"
echo ""
echo "curl -X POST '${API_BASE}/sro_registration?state_code=tn&context=sro' \\"
echo "  -F 'file=@sro_sample.csv'"
echo ""
echo ""

# Example 7: Update mapping configuration (admin only)
echo -e "${BLUE}Example 7: Update Mapping Configuration (Admin Only)${NC}"
echo "----------------------------------------------------------------------"
echo "Request: POST ${API_BASE}/mappings/tn_rural"
echo ""
echo "Update mapping YAML with:"
echo ""
echo "curl -X POST '${API_BASE}/mappings/tn_rural' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer \${ADMIN_TOKEN}' \\"
echo "  -d '{\"yaml_content\": \"...\"}'"
echo ""
echo ""

# Summary
echo "======================================================================"
echo -e "${GREEN}API Examples Complete${NC}"
echo "======================================================================"
echo ""
echo "Next Steps:"
echo "  1. Start the service: uvicorn app.main:app --host 0.0.0.0 --port 8005"
echo "  2. Try the examples above"
echo "  3. View API docs: ${BASE_URL}/docs"
echo "  4. Check DQ reports: data/processed/*_dq_report.json"
echo ""
echo "For Python usage, see: examples/run_etl_example.py"
echo ""
