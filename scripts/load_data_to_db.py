"""
Load generated parcel data from JSONL files into PostgreSQL.
Run with: python3.12 scripts/load_data_to_db.py
"""
import json
import sys
import uuid
from pathlib import Path
from datetime import date, datetime

# Ensure UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "--quiet"])
    import psycopg2
    import psycopg2.extras

BASE_DIR = Path(__file__).parent.parent

# --- DB config (always connect via localhost since this runs on host) ---
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "bhoomi"
DB_USER = "bhoomi"
DB_PASS = "change_me_strong_password_here"

# Read password from .env
env_file = BASE_DIR / ".env"
for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("POSTGRES_PASSWORD="):
        DB_PASS = line.split("=", 1)[1].strip().split("#")[0].strip()
    if line.startswith("POSTGRES_PORT="):
        try:
            DB_PORT = int(line.split("=", 1)[1].strip().split("#")[0].strip())
        except ValueError:
            pass

print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
conn.autocommit = False
cur = conn.cursor()
psycopg2.extras.register_uuid()

# State code mapping (from generator state_code to LGD lgd_code)
STATE_MAP = {"TN": "33", "CH": "04"}

# Get valid district codes from reference table
cur.execute("SELECT lgd_code FROM reference.lgd_hierarchy WHERE entity_type='DISTRICT'")
VALID_DISTRICTS = {r[0] for r in cur.fetchall()}

# Get valid village codes
cur.execute("SELECT lgd_code FROM reference.lgd_hierarchy WHERE entity_type='VILLAGE'")
VALID_VILLAGES = {r[0] for r in cur.fetchall()}

def next_bdpr(state_lgd: str) -> str:
    """Generate a unique BDPR code."""
    return f"{state_lgd}{str(uuid.uuid4().int)[:14]}"

# Load parcels from ground_truth
parcels_file = BASE_DIR / "data" / "ground_truth" / "parcels.jsonl"
if not parcels_file.exists():
    print(f"ERROR: {parcels_file} not found. Run the data generator first.")
    sys.exit(1)

parcels = [json.loads(l) for l in parcels_file.read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"Loading {len(parcels)} parcels into DB...")

inserted_parcels = 0
inserted_ror = 0
skipped = 0

for p in parcels:
    try:
        raw_state = p.get("state_code", "TN")
        state_lgd = STATE_MAP.get(raw_state, "33")
        
        raw_district = str(p.get("district_code", ""))
        district_lgd = raw_district if raw_district in VALID_DISTRICTS else None
        
        raw_village = str(p.get("village_code", ""))
        village_lgd = raw_village if raw_village in VALID_VILLAGES else None
        
        is_urban = raw_state == "CH"

        parcel_uuid = str(uuid.uuid4())
        bdpr = next_bdpr(state_lgd)

        # Only pass ULPIN if it matches the DB regex (14 alphanumeric chars, no XX)
        import re
        raw_ulpin = p.get("ulpin", "")
        if re.match(r'^[0-9]{2}[0-9]{2}[0-9]{4}[A-Z0-9]{8}$', raw_ulpin or ""):
            ulpin = raw_ulpin
        else:
            # Generate valid synthetic ULPIN: SS DD VVVV XXXXXXXX
            s = state_lgd.zfill(2)[:2]
            d = (district_lgd or "00").zfill(2)[:2]
            v = (village_lgd or "0000").zfill(4)[:4]
            suffix = format(uuid.uuid4().int % (36**8), '08X')[:8]
            ulpin = f"{s}{d}{v}{suffix}"

        cur.execute("""
            INSERT INTO identity.parcels (
                id, bdpr, ulpin, state_code, district_code,
                village_code, is_urban, system_of_record_flag
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'DERIVED'
            )
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (
            parcel_uuid,
            bdpr,
            ulpin,
            state_lgd,
            district_lgd or state_lgd,
            village_lgd,
            is_urban,
        ))
        
        row = cur.fetchone()
        if not row:
            skipped += 1
            continue
        
        db_id = row[0]
        inserted_parcels += 1

        # Insert parcel geometry into geo schema (using savepoint so failure doesn't rollback parcel)
        if p.get("geometry"):
            geom_json = json.dumps(p["geometry"])
            try:
                cur.execute("SAVEPOINT geom_sp")
                cur.execute("""
                    INSERT INTO geo.parcel_geometries (
                        parcel_id, survey_number, geometry_type,
                        geometry, area_sq_m, srid, accuracy_class,
                        source_department, source_system, as_of_date
                    ) VALUES (
                        %s, %s, 'CADASTRAL',
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                        %s, 4326, 'C',
                        'REVENUE_DEPT', 'SYNTHETIC_GENERATOR', %s
                    )
                    ON CONFLICT DO NOTHING
                """, (
                    db_id,
                    p.get("survey_number"),
                    geom_json,
                    p.get("area_sq_m"),
                    date.today(),
                ))
                cur.execute("RELEASE SAVEPOINT geom_sp")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT geom_sp")

        # Insert RoR (owners)
        for owner in (p.get("owners") or []):
            try:
                cur.execute("SAVEPOINT ror_sp")
                cur.execute("""
                    INSERT INTO revenue.records_of_rights (
                        parcel_id, survey_number,
                        area_sq_m, area_native, area_unit_native,
                        land_classification,
                        source_department, source_system, source_as_of_date,
                        data_freshness_status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        'REVENUE_DEPT', 'SYNTHETIC_GENERATOR', %s,
                        'CACHED'
                    )
                """, (
                    db_id,
                    p.get("survey_number"),
                    p.get("area_sq_m"),
                    p.get("area_native"),
                    p.get("unit_native", "sq_m"),
                    p.get("land_class", "unknown"),
                    date.today(),
                ))
                cur.execute("RELEASE SAVEPOINT ror_sp")
                inserted_ror += 1
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT ror_sp")

        conn.commit()

    except Exception as e:
        skipped += 1
        conn.rollback()
        if skipped <= 5:
            print(f"  Skip parcel {p.get('ulpin')}: {e}")

print(f"\n[OK] Inserted {inserted_parcels} parcels, {inserted_ror} RoR records, skipped {skipped}")

cur.execute("SELECT COUNT(*) FROM identity.parcels")
print(f"[OK] identity.parcels: {cur.fetchone()[0]} rows")
cur.execute("SELECT COUNT(*) FROM revenue.records_of_rights")
print(f"[OK] revenue.records_of_rights: {cur.fetchone()[0]} rows")
try:
    cur.execute("SELECT COUNT(*) FROM geo.parcel_geometries")
    print(f"[OK] geo.parcel_geometries: {cur.fetchone()[0]} rows")
except Exception:
    pass

cur.close()
conn.close()
print("\nDone! Parcel data loaded into PostgreSQL.")
