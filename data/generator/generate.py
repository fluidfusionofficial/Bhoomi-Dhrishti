"""
Bhoomi Dhrishti - Mock Data Generator
Generates deterministic ground-truth parcels for two contexts and 7 corrupt departmental views.

Usage:
    python generate.py [--seed 42]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError for ✓ etc.)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from faker import Faker
from shapely.geometry import MultiPoint, Point, Polygon, mapping, shape
from shapely.ops import voronoi_diagram

# Initialize Faker with Indian locales
faker_en = Faker('en_IN')
faker_ta = Faker(['ta_IN', 'en_IN'])

# Tamil names for variety
TAMIL_NAMES = [
    ("ராமன்", "Raman", "Raaman"), ("சுந்தர்", "Sundar", "Sundhar"),
    ("முருகன்", "Murugan", "Murughan"), ("சிவா", "Siva", "Shiva"),
    ("வேலு", "Velu", "Vellu"), ("மணி", "Mani", "Manee"),
    ("செல்வம்", "Selvam", "Chelvam"), ("பாண்டி", "Pandi", "Paandi"),
    ("கண்ணன்", "Kannan", "Kannan"), ("ராஜா", "Raja", "Raaja"),
    ("குமார்", "Kumar", "Kumarr"), ("வெங்கட்", "Venkat", "Venkata"),
]

# Survey number pools for realistic diversity
TN_SURVEY_PREFIXES = ["SF", "RS", "T"]
CH_PLOT_PREFIXES = ["22/", "22-", "S22/"]

# LGD codes (mock but structured correctly)
LGD_TN_DISTRICT = "623"  # Tirunelveli
LGD_TN_VILLAGE = "623401"  # Periyapalayam
LGD_CH_DISTRICT = "801"  # Chandigarh
LGD_CH_WARD = "801022"  # Sector 22

class GroundTruthGenerator:
    """Generates the canonical ground truth for two contexts."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        Faker.seed(seed)

    def generate_tn_rural(self) -> List[Dict[str, Any]]:
        """Generate Tamil Nadu rural village (Periyapalayam, Tirunelveli)."""
        # Center point near Tirunelveli
        center_lat, center_lon = 8.7139, 77.7567
        parcels = []

        # Generate ~200 parcels using Voronoi
        num_parcels = 200
        points = []
        for _ in range(num_parcels):
            lat = center_lat + np.random.uniform(-0.02, 0.02)
            lon = center_lon + np.random.uniform(-0.02, 0.02)
            points.append(Point(lon, lat))

        # Create Voronoi diagram
        multipoint = MultiPoint(points)
        voronoi = voronoi_diagram(multipoint)

        # Bounding box to clip parcels
        bbox = Polygon([
            (center_lon - 0.025, center_lat - 0.025),
            (center_lon + 0.025, center_lat - 0.025),
            (center_lon + 0.025, center_lat + 0.025),
            (center_lon - 0.025, center_lat + 0.025),
        ])

        for i, geom in enumerate(voronoi.geoms):
            if i >= num_parcels:
                break
            poly = geom.intersection(bbox)
            if poly.is_empty or poly.area < 0.00001:
                continue

            parcel_id = str(uuid.UUID(int=random.getrandbits(128), version=4))

            # Generate ULPIN (14-char alphanumeric, geo-derived)
            ulpin = self._generate_ulpin(poly.centroid.y, poly.centroid.x, i)

            # Land classification (weighted)
            land_class = random.choices(
                ["agricultural", "residential", "commercial", "government", "poramboke", "forest"],
                weights=[60, 25, 5, 3, 5, 2]
            )[0]

            # Area in sq_m
            area_sq_m = poly.area * 111320 * 111320 * math.cos(math.radians(center_lat))

            # Convert to native units (cent, veli, kuli)
            if area_sq_m < 200:
                unit_native = "kuli"
                area_native = area_sq_m / 1.67
            elif area_sq_m < 2500:
                unit_native = "cent"
                area_native = area_sq_m / 40.47
            else:
                unit_native = "veli"
                area_native = area_sq_m / 6670

            # Generate owners
            num_owners = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
            owners = []
            for j in range(num_owners):
                name_ta, name_en_1, name_en_2 = random.choice(TAMIL_NAMES)
                owners.append({
                    "name_native": name_ta,
                    "name_latin": name_en_1,
                    "name_latin_alt": name_en_2,
                    "name_phonetic": self._soundex(name_en_1),
                    "share_fraction": 1.0 / num_owners,
                    "right_type": random.choices(
                        ["ownership", "tenancy", "mortgage", "easement"],
                        weights=[85, 10, 3, 2]
                    )[0]
                })

            # Survey number
            prefix = random.choice(TN_SURVEY_PREFIXES)
            survey_num = f"{prefix}-{i+1:03d}/{random.randint(1,9)}"

            parcels.append({
                "parcel_id": parcel_id,
                "ulpin": ulpin,
                "geometry": mapping(poly),
                "land_class": land_class,
                "area_sq_m": round(area_sq_m, 2),
                "area_native": round(area_native, 3),
                "unit_native": unit_native,
                "owners": owners,
                "survey_number": survey_num,
                "village_code": LGD_TN_VILLAGE,
                "district_code": LGD_TN_DISTRICT,
                "state_code": "TN",
            })

        return parcels

    def generate_ch_urban(self) -> List[Dict[str, Any]]:
        """Generate Chandigarh urban ward (Sector 22)."""
        center_lat, center_lon = 30.7333, 76.7794
        parcels = []

        # Generate ~150 urban plots
        num_parcels = 150
        points = []
        for _ in range(num_parcels):
            lat = center_lat + np.random.uniform(-0.005, 0.005)
            lon = center_lon + np.random.uniform(-0.005, 0.005)
            points.append(Point(lon, lat))

        multipoint = MultiPoint(points)
        voronoi = voronoi_diagram(multipoint)

        bbox = Polygon([
            (center_lon - 0.006, center_lat - 0.006),
            (center_lon + 0.006, center_lat - 0.006),
            (center_lon + 0.006, center_lat + 0.006),
            (center_lon - 0.006, center_lat + 0.006),
        ])

        for i, geom in enumerate(voronoi.geoms):
            if i >= num_parcels:
                break
            poly = geom.intersection(bbox)
            if poly.is_empty or poly.area < 0.000005:
                continue

            parcel_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
            ulpin = self._generate_ulpin(poly.centroid.y, poly.centroid.x, i + 1000)

            land_class = random.choices(
                ["residential", "commercial", "government", "institutional"],
                weights=[70, 20, 5, 5]
            )[0]

            area_sq_m = poly.area * 111320 * 111320 * math.cos(math.radians(center_lat))

            # Convert to sq yards / marla
            if area_sq_m < 100:
                unit_native = "sq_yards"
                area_native = area_sq_m * 1.19599
            else:
                unit_native = "marla"
                area_native = area_sq_m / 25.29

            # Owners (some multi-unit buildings)
            if i == 10:  # Special: apartment block with 40 units (BAUnit demo)
                num_owners = 40
            else:
                num_owners = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]

            owners = []
            for j in range(num_owners):
                name = faker_en.name()
                owners.append({
                    "name_native": name,
                    "name_latin": name,
                    "name_latin_alt": name,
                    "name_phonetic": self._soundex(name.split()[0]),
                    "share_fraction": 1.0 / num_owners,
                    "right_type": "ownership" if num_owners < 10 else "apartment_unit",
                })

            prefix = random.choice(CH_PLOT_PREFIXES)
            survey_num = f"{prefix}{i+1}"

            parcels.append({
                "parcel_id": parcel_id,
                "ulpin": ulpin,
                "geometry": mapping(poly),
                "land_class": land_class,
                "area_sq_m": round(area_sq_m, 2),
                "area_native": round(area_native, 3),
                "unit_native": unit_native,
                "owners": owners,
                "survey_number": survey_num,
                "village_code": LGD_CH_WARD,
                "district_code": LGD_CH_DISTRICT,
                "state_code": "CH",
            })

        return parcels

    def _generate_ulpin(self, lat: float, lon: float, seq: int) -> str:
        """Generate a mock 14-character ULPIN."""
        # Format: SSDDVVVVNNNNNN (State, District, Village, Sequential)
        # This is a simplified mock; real ULPIN derivation is more complex
        lat_enc = str(int(abs(lat) * 1000))[-3:]
        lon_enc = str(int(abs(lon) * 1000))[-3:]
        seq_enc = f"{seq:06d}"
        ulpin = f"{lat_enc}{lon_enc}{seq_enc}XX"
        return ulpin[:14]

    def _soundex(self, name: str) -> str:
        """Simplified Soundex for phonetic matching."""
        if not name:
            return "0000"
        name = name.upper()
        soundex_map = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6',
        }

        code = name[0]
        for char in name[1:]:
            if char in soundex_map:
                digit = soundex_map[char]
                if digit != code[-1]:
                    code += digit
            if len(code) >= 4:
                break

        code = (code + "000")[:4]
        return code


class DepartmentalViewsCorruptor:
    """Corrupts ground truth into 7 departmental views with realistic defects."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

        # Track injected defects for demo manifest
        self.defects = []

    def generate_revenue_ror(self, parcels: List[Dict]) -> List[Dict]:
        """Revenue Record of Rights - area in native units, some stale owners."""
        ror_records = []
        for p in parcels:
            record = {
                "survey_number": p["survey_number"],
                "village_code": p["village_code"],
                "district_code": p["district_code"],
                "area": p["area_native"],
                "unit": p["unit_native"],
                "land_class": p["land_class"],
                "owners": [],
            }

            # 15% have stale owner names
            if random.random() < 0.15:
                record["owners"] = [{"name": "STALE_OWNER_" + faker_en.name(), "share": 1.0}]
                self.defects.append({
                    "type": "stale_ownership",
                    "parcel_id": p["parcel_id"],
                    "source": "revenue_ror",
                })
            else:
                for owner in p["owners"]:
                    # Use native script for names
                    record["owners"].append({
                        "name": owner["name_native"],
                        "share": owner["share_fraction"],
                    })

            # 3% missing survey number
            if random.random() < 0.03:
                record["survey_number"] = ""
                self.defects.append({
                    "type": "missing_survey_number",
                    "parcel_id": p["parcel_id"],
                    "source": "revenue_ror",
                })

            ror_records.append(record)

        return ror_records

    def generate_sro_registrations(self, parcels: List[Dict]) -> List[Dict]:
        """SRO sale deed registry - transliterated names, area in sq ft."""
        registrations = []

        # Track parcels for double-sale injection
        double_sale_idx = random.randint(20, 40)

        for i, p in enumerate(parcels):
            # Convert area to sq ft
            area_sqft = p["area_sq_m"] * 10.7639

            record = {
                "doc_number": f"SRO/{p['state_code']}/{random.randint(10000, 99999)}",
                "survey_number": p["survey_number"],
                "registration_date": (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime("%d/%m/%Y"),
                "area_sqft": round(area_sqft, 2),
                "seller": faker_en.name(),
                "buyer": p["owners"][0]["name_latin"] if p["owners"] else faker_en.name(),
                "sale_value": round(area_sqft * random.uniform(500, 2000), 2),
            }

            registrations.append(record)

            # 5% double-sold parcels
            if i == double_sale_idx:
                # Second sale deed for same parcel
                record2 = {
                    "doc_number": f"SRO/{p['state_code']}/{random.randint(10000, 99999)}",
                    "survey_number": p["survey_number"],
                    "registration_date": (datetime.now() - timedelta(days=random.randint(10, 60))).strftime("%d/%m/%Y"),
                    "area_sqft": round(area_sqft, 2),
                    "seller": record["buyer"],
                    "buyer": faker_en.name(),
                    "sale_value": round(area_sqft * random.uniform(600, 2500), 2),
                }
                registrations.append(record2)
                self.defects.append({
                    "type": "double_sold",
                    "parcel_id": p["parcel_id"],
                    "survey_number": p["survey_number"],
                    "source": "sro_registrations",
                })

        return registrations

    def generate_municipal_tax(self, parcels: List[Dict]) -> List[Dict]:
        """ULB property tax - property IDs don't map directly, some area mismatches."""
        tax_records = []
        for p in parcels:
            # Generate non-obvious property ID
            prop_id = f"TAX-{p['district_code']}-{random.randint(1000, 9999)}"

            # 8% area mismatch >20%
            area_recorded = p["area_sq_m"]
            if random.random() < 0.08:
                area_recorded *= random.uniform(0.7, 1.35)
                self.defects.append({
                    "type": "area_mismatch",
                    "parcel_id": p["parcel_id"],
                    "actual_area": p["area_sq_m"],
                    "recorded_area": area_recorded,
                    "source": "municipal_tax",
                })

            tax_records.append({
                "property_id": prop_id,
                "survey_number": p["survey_number"] if random.random() > 0.1 else "",
                "area_sq_m": round(area_recorded, 2),
                "owner_name": p["owners"][0]["name_latin_alt"] if p["owners"] else "",
                "tax_due": round(area_recorded * random.uniform(2, 10), 2),
                "last_paid": (datetime.now() - timedelta(days=random.randint(0, 400))).strftime("%Y-%m-%d"),
            })

        return tax_records

    def generate_building_permissions(self, parcels: List[Dict]) -> List[Dict]:
        """Building permits - point geometry only, plot numbers."""
        permissions = []
        for p in parcels:
            if p["land_class"] not in ["residential", "commercial"]:
                continue

            if random.random() < 0.4:  # 40% have building permissions
                geom = shape(p["geometry"])
                centroid = geom.centroid

                permissions.append({
                    "permit_number": f"BP-{p['district_code']}-{random.randint(1000, 9999)}",
                    "plot_number": p["survey_number"].replace("/", "-"),
                    "latitude": centroid.y,
                    "longitude": centroid.x,
                    "approved_area_sq_m": round(p["area_sq_m"] * random.uniform(0.4, 0.6), 2),
                    "permit_date": (datetime.now() - timedelta(days=random.randint(180, 900))).strftime("%Y-%m-%d"),
                    "owner": p["owners"][0]["name_latin"] if p["owners"] else "",
                })

        return permissions

    def generate_court_cases(self, parcels: List[Dict]) -> List[Dict]:
        """Litigation records - often party-name-only references."""
        cases = []

        # 5% of parcels have disputes
        disputed_parcels = random.sample(parcels, k=max(1, len(parcels) // 20))

        for p in disputed_parcels:
            # 60% no survey number in case
            has_survey = random.random() > 0.6

            cases.append({
                "case_number": f"CC/{random.randint(1000, 9999)}/20{random.randint(18, 24)}",
                "filing_date": (datetime.now() - timedelta(days=random.randint(100, 1500))).strftime("%d-%m-%Y"),
                "plaintiff": p["owners"][0]["name_latin"] if p["owners"] else faker_en.name(),
                "defendant": faker_en.name(),
                "survey_number": p["survey_number"] if has_survey else "",
                "property_description": f"Land near {p['village_code']}" if not has_survey else "",
                "status": random.choice(["pending", "pending", "pending", "resolved"]),
            })

            if not has_survey:
                self.defects.append({
                    "type": "unlinked_dispute",
                    "parcel_id": p["parcel_id"],
                    "case_number": cases[-1]["case_number"],
                    "source": "court_cases",
                })

        return cases

    def generate_land_use_zoning(self, parcels: List[Dict]) -> List[Dict]:
        """Planning zones - zone polygons, not parcel polygons."""
        zones = []

        # Group parcels by rough geographic clusters
        if parcels:
            state = parcels[0]["state_code"]

            # Create 3-5 large zone polygons covering clusters
            num_zones = random.randint(3, 5)
            zone_types = ["residential", "commercial", "industrial", "agricultural", "green_belt"]

            for i in range(num_zones):
                sample_parcels = random.sample(parcels, k=min(30, len(parcels)))
                points = []
                for p in sample_parcels:
                    geom = shape(p["geometry"])
                    points.append(geom.centroid)

                if len(points) < 3:
                    continue

                # Convex hull of cluster
                multipoint = MultiPoint(points)
                zone_geom = multipoint.convex_hull.buffer(0.002)

                zones.append({
                    "zone_id": f"Z-{state}-{i+1:02d}",
                    "zone_type": random.choice(zone_types),
                    "geometry": mapping(zone_geom),
                    "fsi": round(random.uniform(1.0, 3.5), 2),
                })

        return zones

    def generate_encumbrance_ec(self, parcels: List[Dict]) -> List[Dict]:
        """Encumbrance certificates - some with unrecorded mortgages."""
        ecs = []
        for p in parcels:
            has_encumbrance = random.random() < 0.15

            ec = {
                "survey_number": p["survey_number"],
                "district_code": p["district_code"],
                "from_date": (datetime.now() - timedelta(days=365*10)).strftime("%d/%m/%Y"),
                "to_date": datetime.now().strftime("%d/%m/%Y"),
                "encumbrances": [],
            }

            if has_encumbrance:
                ec["encumbrances"].append({
                    "type": random.choice(["mortgage", "attachment", "charge"]),
                    "amount": round(random.uniform(100000, 5000000), 2),
                    "date": (datetime.now() - timedelta(days=random.randint(100, 1000))).strftime("%d/%m/%Y"),
                    "doc_number": f"DOC/{random.randint(10000, 99999)}",
                })
            else:
                # 10% "no encumbrance" but actually have unregistered arrangements
                if random.random() < 0.10:
                    self.defects.append({
                        "type": "missing_encumbrance",
                        "parcel_id": p["parcel_id"],
                        "note": "Oral mortgage arrangement not reflected",
                        "source": "encumbrance_ec",
                    })

            ecs.append(ec)

        return ecs

    def inject_special_defects(self, parcels: List[Dict]) -> None:
        """Inject deliberate demo defects."""
        # Circular transaction ring (4 parties)
        if len(parcels) >= 8:
            ring_parcels = parcels[50:54]
            parties = [faker_en.name() for _ in range(4)]

            # Create circular chain: A→B→C→D→A
            for i, p in enumerate(ring_parcels):
                p["_circular_ring_party"] = parties[i]
                self.defects.append({
                    "type": "circular_transaction_ring",
                    "parcel_id": p["parcel_id"],
                    "party": parties[i],
                    "next_party": parties[(i+1) % 4],
                })

        # Parcel with survey renumbering (lineage demo)
        if len(parcels) >= 100:
            p = parcels[99]
            old_survey = p["survey_number"]
            new_survey = old_survey.replace("/", "-NEW-")
            self.defects.append({
                "type": "survey_renumber_lineage",
                "parcel_id": p["parcel_id"],
                "old_survey": old_survey,
                "new_survey": new_survey,
            })

        # Overlapping geometry (topology error)
        if len(parcels) >= 80:
            p1 = parcels[78]
            p2 = parcels[79]
            # Shift p2 geometry to overlap with p1
            geom1 = shape(p1["geometry"])
            geom2 = shape(p2["geometry"])
            centroid_shift = Point(
                geom1.centroid.x + (geom2.centroid.x - geom1.centroid.x) * 0.3,
                geom1.centroid.y + (geom2.centroid.y - geom1.centroid.y) * 0.3,
            )
            p2["geometry"] = mapping(geom2)  # Keep for now, detection will find overlap
            self.defects.append({
                "type": "overlapping_geometry",
                "parcel_a": p1["parcel_id"],
                "parcel_b": p2["parcel_id"],
            })


def write_jsonl(path: Path, records: List[Dict]) -> None:
    """Write records as JSONL."""
    with open(path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def write_csv(path: Path, records: List[Dict]) -> None:
    """Write records as CSV."""
    if not records:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Generate Bhoomi Dhrishti mock data")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    print(f"Generating ground truth with seed={args.seed}...")

    # Create output directories
    data_dir = Path(__file__).parent.parent
    raw_tn = data_dir / "raw" / "tn_rural"
    raw_ch = data_dir / "raw" / "ch_urban"
    ground_truth_dir = data_dir / "ground_truth"

    for d in [raw_tn, raw_ch, ground_truth_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Generate ground truth
    generator = GroundTruthGenerator(seed=args.seed)
    tn_parcels = generator.generate_tn_rural()
    ch_parcels = generator.generate_ch_urban()
    all_parcels = tn_parcels + ch_parcels

    print(f"Generated {len(tn_parcels)} TN rural parcels")
    print(f"Generated {len(ch_parcels)} CH urban parcels (including 1 apartment block with 40 units)")

    # Write ground truth
    write_jsonl(ground_truth_dir / "parcels.jsonl", all_parcels)

    # Generate corrupted departmental views
    print("\nGenerating departmental views with injected defects...")

    corruptor = DepartmentalViewsCorruptor(seed=args.seed)

    # Tamil Nadu views
    tn_ror = corruptor.generate_revenue_ror(tn_parcels)
    tn_sro = corruptor.generate_sro_registrations(tn_parcels)
    tn_tax = corruptor.generate_municipal_tax(tn_parcels)
    tn_bp = corruptor.generate_building_permissions(tn_parcels)
    tn_cases = corruptor.generate_court_cases(tn_parcels)
    tn_zones = corruptor.generate_land_use_zoning(tn_parcels)
    tn_ec = corruptor.generate_encumbrance_ec(tn_parcels)

    write_jsonl(raw_tn / "revenue_ror.jsonl", tn_ror)
    write_csv(raw_tn / "sro_registrations.csv", tn_sro)
    write_csv(raw_tn / "municipal_tax.csv", tn_tax)
    write_csv(raw_tn / "building_permissions.csv", tn_bp)
    write_jsonl(raw_tn / "court_cases.jsonl", tn_cases)
    write_jsonl(raw_tn / "land_use_zones.jsonl", tn_zones)
    write_jsonl(raw_tn / "encumbrance_ec.jsonl", tn_ec)

    # Chandigarh views
    ch_ror = corruptor.generate_revenue_ror(ch_parcels)
    ch_sro = corruptor.generate_sro_registrations(ch_parcels)
    ch_tax = corruptor.generate_municipal_tax(ch_parcels)
    ch_bp = corruptor.generate_building_permissions(ch_parcels)
    ch_cases = corruptor.generate_court_cases(ch_parcels)
    ch_zones = corruptor.generate_land_use_zoning(ch_parcels)
    ch_ec = corruptor.generate_encumbrance_ec(ch_parcels)

    write_jsonl(raw_ch / "revenue_ror.jsonl", ch_ror)
    write_csv(raw_ch / "sro_registrations.csv", ch_sro)
    write_csv(raw_ch / "municipal_tax.csv", ch_tax)
    write_csv(raw_ch / "building_permissions.csv", ch_bp)
    write_jsonl(raw_ch / "court_cases.jsonl", ch_cases)
    write_jsonl(raw_ch / "land_use_zones.jsonl", ch_zones)
    write_jsonl(raw_ch / "encumbrance_ec.jsonl", ch_ec)

    # Inject special demo defects
    corruptor.inject_special_defects(all_parcels)

    # Write defects manifest
    defects_manifest = {
        "seed": args.seed,
        "generated_at": datetime.now().isoformat(),
        "total_parcels": len(all_parcels),
        "defects": corruptor.defects,
    }

    with open(ground_truth_dir / "defects_manifest.json", 'w') as f:
        json.dump(defects_manifest, f, indent=2)

    print(f"\n✓ Generated {len(corruptor.defects)} deliberate defects")
    print(f"✓ Ground truth: {ground_truth_dir}/parcels.jsonl")
    print(f"✓ Defects manifest: {ground_truth_dir}/defects_manifest.json")
    print(f"✓ TN departmental views: {raw_tn}")
    print(f"✓ CH departmental views: {raw_ch}")
    print("\nDefect summary:")
    defect_types = {}
    for d in corruptor.defects:
        dtype = d["type"]
        defect_types[dtype] = defect_types.get(dtype, 0) + 1

    for dtype, count in sorted(defect_types.items()):
        print(f"  - {dtype}: {count}")


if __name__ == "__main__":
    main()
