# ETL Mapping Engine - Quick Reference

## REST API Endpoints

### Data Ingestion

```bash
# Upload and ingest data
POST /ingest/{source_type}
  ?state_code=tn
  &context=rural
  &conflict_strategy=update

# Supported source_types: revenue_ror, sro_registration
# Supported file types: .csv, .json, .jsonl
# conflict_strategy: update (upsert) | ignore (skip duplicates)
```

**Example:**
```bash
curl -X POST "http://localhost:8005/ingest/revenue_ror?state_code=tn&context=rural" \
  -F "file=@data.csv"
```

### Job Management

```bash
# Check ingestion job status
GET /ingest/status/{job_id}
```

### Source Configuration

```bash
# List all configured source mappings
GET /ingest/sources

# Get specific mapping configuration
GET /ingest/mappings/{state_code}_{context}

# Update mapping configuration (admin only)
POST /ingest/mappings/{state_code}_{context}
Body: {"yaml_content": "..."}
```

## Transformation Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `normalize_survey_number` | Strip leading zeros, normalize separators | `"0123/4A"` → `"123/4A"` |
| `normalize_date` | Convert to ISO 8601 | `"15/08/2020"` → `"2020-08-15"` |
| `convert_area` | District-aware unit conversion | `5.5 cent` → `222.59 sq_m` |
| `transliterate_to_latin` | Script transliteration | `"முருகன்"` → `"Murugan"` |
| `generate_phonetic_key` | Soundex-like key for names | `"Ramesh Kumar"` → `"R652"` |
| `validate_geometry` | WKT/GeoJSON validation | Validates & returns WKT |
| `parse_address` | Extract components | Returns `{district, village, pincode}` |

## Mapping YAML Template

```yaml
source_type: revenue_ror
source_system: STATE_SYSTEM_NAME
source_department: Department Name

field_mapping:
  canonical_field:
    source_field: "Source_Column"
    transform: transform_function_name
    type: str|float|int|bool
    script: tamil|devanagari  # For transliteration

conversions:
  area_units:
    cent: 40.47
    acre: 4046.86

data_quality:
  required_fields: [survey_number, district_code]
  unique_fields: [survey_number]
```

## Python Usage

### Mapper

```python
from app.engine import SourceMapper

mapper = SourceMapper("mappings/tn_rural/mapping.yaml")
canonical = mapper.apply_mapping(
    source_record,
    context={"district_lgd_code": "33001"}
)
```

### Validator

```python
from app.engine import DataQualityValidator

validator = DataQualityValidator("revenue_ror")
report = validator.validate_records(canonical_records)

print(f"Quality Score: {report.quality_score}%")
print(f"Valid: {report.valid_rows}/{report.total_rows}")
```

### Loader

```python
from app.engine import DataLoader
from app.db import AsyncSessionLocal

async with AsyncSessionLocal() as session:
    loader = DataLoader(session)
    rows = await loader.load_ror_records(
        canonical_records,
        conflict_strategy="update"
    )
```

### Transforms

```python
from app.engine import transforms

# Area conversion
area_sq_m = transforms.convert_area(5.5, "cent", "sq_m")

# Date normalization
iso_date = transforms.normalize_date("15/08/2020")

# Survey number normalization
normalized = transforms.normalize_survey_number("0123/4A")
```

## DQ Report Structure

```json
{
  "source_type": "revenue_ror",
  "total_rows": 200,
  "valid_rows": 185,
  "quality_score": 92.5,
  "field_statistics": {
    "field_name": {
      "null_count": 6,
      "null_rate": 0.03,
      "min": 0.5,
      "max": 45.2,
      "mean": 5.3
    }
  },
  "issues": [
    {
      "row": 15,
      "field": "survey_number",
      "issue": "null_value"
    }
  ]
}
```

## Common Workflows

### 1. Ingest New State Data

```bash
# 1. Create mapping directory
mkdir -p data/mappings/kl_rural

# 2. Create mapping.yaml
# (copy and modify from tn_rural/mapping.yaml)

# 3. Upload data
curl -X POST "http://localhost:8005/ingest/revenue_ror?state_code=kl&context=rural" \
  -F "file=@kerala_data.csv"

# 4. Check DQ report
cat data/processed/*_dq_report.json
```

### 2. Test Mapping Locally

```bash
# Run standalone example
python examples/run_etl_example.py

# Run tests
pytest tests/test_etl_engine.py -v
```

### 3. Update Existing Mapping

```bash
# 1. Get current mapping
curl "http://localhost:8005/ingest/mappings/tn_rural" > current.yaml

# 2. Edit YAML file
vim current.yaml

# 3. Upload updated mapping
curl -X POST "http://localhost:8005/ingest/mappings/tn_rural" \
  -H "Content-Type: application/json" \
  -d "{\"yaml_content\": \"$(cat current.yaml)\"}"
```

## File Locations

```
services/interoperability/
├── data/
│   ├── mappings/        # YAML configurations
│   │   ├── tn_rural/
│   │   └── tn_sro/
│   ├── processed/       # DQ reports (JSON)
│   └── samples/         # Sample CSV files
├── app/
│   ├── engine/          # Core ETL modules
│   │   ├── mapper.py
│   │   ├── transforms.py
│   │   ├── validator.py
│   │   └── loader.py
│   └── routers/
│       └── ingest.py    # REST API
└── examples/            # Usage examples
```

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/bhoomi
LOG_LEVEL=INFO
SERVICE_NAME=interoperability
```

## Database Tables

- `identity.parcels` - Land parcel master
- `revenue.ror_records` - Record of Rights
- `registration.sale_deeds` - SRO registrations

## Error Handling

| Error | HTTP Code | Meaning |
|-------|-----------|---------|
| `Mapping not found` | 404 | No mapping config for state/context |
| `Unsupported file type` | 400 | Not CSV/JSON/JSONL |
| `Failed to parse` | 400 | Invalid file format |
| `Schema validation failed` | 200 (tracked in DQ report) | Data doesn't match schema |

## Performance Tips

- Batch size: 1000 records per DB transaction
- Use `conflict_strategy=ignore` for faster inserts (no updates)
- Large files: Consider splitting into chunks
- Async I/O: All DB operations use asyncpg

## Support Commands

```bash
# View logs
docker logs -f bhoomi-interoperability

# Check service health
curl http://localhost:8005/health

# View API docs
open http://localhost:8005/docs

# Run tests
pytest tests/ -v

# Format code
black app/ tests/
```

## Key Dependencies

- `fastapi` - REST API framework
- `pandas` - Data manipulation
- `pydantic` - Schema validation
- `great-expectations` - Data quality
- `sqlalchemy` - Database ORM
- `shapely` - Geometry validation
- `unidecode` - Transliteration

## Next Steps

1. ✅ Test with sample data
2. ✅ Review DQ reports
3. ⏳ Add state-specific mappings
4. ⏳ Configure authentication
5. ⏳ Set up monitoring
6. ⏳ Deploy to production

---

**Documentation**: See `ETL_ENGINE_README.md` for detailed guide

**Examples**: See `examples/` directory for working code samples

**Support**: bhoomi-dhrishti-support@example.com
