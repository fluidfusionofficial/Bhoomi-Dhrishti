"""
Bhoomi Dhrishti - Realistic Synthetic Data Generator
Generates 2000+ TN rural and 1000+ CH urban parcels with 7 departmental views.
Calibrated against: Agricultural Census (86.21% small/marginal), NFHS-5 (14% female
ownership), DILRMP dashboard (TN/CH 100% ULPIN), TN Bhoomi Pahani format, CH Estate Office.

Usage:
    python generate.py [--seed 42] [--tn-count 2000] [--ch-count 1000]
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

import numpy as np
from faker import Faker
from shapely.geometry import MultiPoint, Point, Polygon, box, mapping, shape
from shapely.affinity import translate

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

faker_en = Faker("en_IN")

# ═══════════════════════════════════════════════════════════════════════════════
# NAME POOLS — Tamil Nadu (Tirunelveli) & Chandigarh
# Each entry: (native_script, latin, alt_latin)
# ═══════════════════════════════════════════════════════════════════════════════

TN_MALE_NAMES = [
    ("ராமன்", "Raman", "Raaman"), ("சுந்தர்", "Sundar", "Sundhar"),
    ("முருகன்", "Murugan", "Murughan"), ("சிவா", "Siva", "Shiva"),
    ("வேலு", "Velu", "Vellu"), ("மணி", "Mani", "Manee"),
    ("செல்வம்", "Selvam", "Chelvam"), ("பாண்டி", "Pandi", "Paandi"),
    ("கண்ணன்", "Kannan", "Kannen"), ("ராஜா", "Raja", "Raajaa"),
    ("குமார்", "Kumar", "Kumaar"), ("வெங்கட்", "Venkat", "Venkata"),
    ("அருண்", "Arun", "Aroon"), ("கார்த்திக்", "Karthik", "Karthick"),
    ("சரவணன்", "Saravanan", "Saravannan"), ("பழனி", "Pazhani", "Palani"),
    ("ராஜேந்திரன்", "Rajendran", "Rajendiran"), ("சுரேஷ்", "Suresh", "Surase"),
    ("தினேஷ்", "Dinesh", "Dhinesh"), ("மகேஷ்", "Mahesh", "Maheash"),
    ("பாலா", "Bala", "Baala"), ("கோபி", "Gopi", "Gopee"),
    ("ஜெயராம்", "Jeyaram", "Jayaram"), ("சண்முகம்", "Shanmugam", "Sanmugam"),
    ("நாகராஜன்", "Nagarajan", "Nagrajan"), ("வேலுச்சாமி", "Veluchami", "Velusamy"),
    ("தங்கராஜ்", "Thangaraj", "Thankaraj"), ("பெரியசாமி", "Periyasamy", "Periyaswamy"),
    ("மாரிமுத்து", "Marimuthu", "Marimutthu"), ("முத்துக்குமார்", "Muthukumar", "Muthukumaar"),
    ("அய்யனார்", "Ayyanar", "Aiyanar"), ("கருப்பசாமி", "Karuppasamy", "Karuppaswamy"),
    ("சின்னசாமி", "Chinnasamy", "Chinnaswamy"), ("ஆறுமுகம்", "Arumugam", "Aarumugam"),
    ("வடிவேல்", "Vadivel", "Vadivellu"), ("சுப்பிரமணி", "Subramani", "Subramanee"),
    ("தமிழ்செல்வன்", "Tamilselvan", "Tamizhelvan"), ("இளங்கோவன்", "Ilangovan", "Elangovan"),
    ("பாலசுப்ரமணியன்", "Balasubramanian", "Balasubramaniam"),
    ("ராமசாமி", "Ramasamy", "Ramaswamy"), ("அன்பழகன்", "Anbazhagan", "Anbalagan"),
    ("கலையரசன்", "Kalaiarasan", "Kalairasan"),
]

TN_FEMALE_NAMES = [
    ("லக்ஷ்மி", "Lakshmi", "Laxmi"), ("சரஸ்வதி", "Saraswathi", "Sarasvati"),
    ("பார்வதி", "Parvathi", "Parvati"), ("மீனாட்சி", "Meenakshi", "Meenachi"),
    ("காமாட்சி", "Kamakshi", "Kamachi"), ("செல்வி", "Selvi", "Chelvi"),
    ("மாலதி", "Malathi", "Malati"), ("சுமதி", "Sumathi", "Sumati"),
    ("தமிழ்ச்செல்வி", "Tamilselvi", "Tamizhelvi"), ("ராஜேஸ்வரி", "Rajeswari", "Rajeswary"),
    ("கலைவாணி", "Kalaivani", "Kalaivaani"), ("மகாலட்சுமி", "Mahalakshmi", "Mahalaxmi"),
    ("வள்ளி", "Valli", "Vaalli"), ("நாகம்மாள்", "Nagammal", "Naagammal"),
    ("பொன்னம்மாள்", "Ponnammal", "Ponnamaal"), ("கனகம்மாள்", "Kanakammal", "Kanagammal"),
    ("முத்தம்மாள்", "Muthammal", "Mutthammal"), ("சீதா", "Seetha", "Sita"),
    ("அன்னம்மா", "Annamma", "Annamaa"), ("ஜெயலட்சுமி", "Jayalakshmi", "Jayalaxmi"),
    ("சந்திரா", "Chandra", "Chandraa"), ("சுசிலா", "Sushila", "Susila"),
    ("கமலா", "Kamala", "Kamalaa"), ("பத்மா", "Padma", "Pathmaa"),
    ("ஆண்டாள்", "Andal", "Aandaal"), ("மணிமேகலை", "Manimegalai", "Manimagalai"),
    ("வசந்தா", "Vasantha", "Vasanta"),
]

CH_MALE_NAMES = [
    ("ਰਾਜ", "Raj", "Raaj"), ("ਅਮਨ", "Aman", "Amaan"),
    ("ਗੁਰਪ੍ਰੀਤ", "Gurpreet", "Gurprith"), ("ਹਰਜੀਤ", "Harjeet", "Harjit"),
    ("ਮਨਦੀਪ", "Mandeep", "Mandip"), ("ਜਸਵਿੰਦਰ", "Jaswinder", "Jasvinder"),
    ("ਸੁਖਵਿੰਦਰ", "Sukhwinder", "Sukhvinder"), ("राजेश", "Rajesh", "Raajesh"),
    ("ਅਮਰੀਕ", "Amrik", "Amreek"), ("ਬਲਵੀਰ", "Balveer", "Balweer"),
    ("ਦਲਜੀਤ", "Daljeet", "Daljit"), ("ਕੁਲਦੀਪ", "Kuldeep", "Kuldip"),
    ("ਮਨਜੀਤ", "Manjeet", "Manjit"), ("ਪਰਮਜੀਤ", "Paramjeet", "Parmjit"),
    ("ਰਵਿੰਦਰ", "Ravinder", "Rawinder"), ("ਸਤਿੰਦਰ", "Satinder", "Satindar"),
    ("विक्रम", "Vikram", "Vickram"), ("अशोक", "Ashok", "Ashoke"),
    ("ਦਵਿੰਦਰ", "Davinder", "Dawinder"), ("ਗੁਰਮੀਤ", "Gurmeet", "Gurmit"),
    ("ਹਰਪ੍ਰੀਤ", "Harpreet", "Harprith"), ("जगदीश", "Jagdish", "Jagdeesh"),
    ("करन", "Karan", "Karun"), ("ਲਖਵੀਰ", "Lakhveer", "Lakhweer"),
    ("ਨਰਿੰਦਰ", "Narinder", "Narindar"), ("ਪ੍ਰਕਾਸ਼", "Prakash", "Parkash"),
    ("ਰਣਜੀਤ", "Ranjeet", "Ranjit"), ("ਸੰਦੀਪ", "Sandeep", "Sandip"),
    ("ਤਰਨਜੀਤ", "Taranjeet", "Taranjit"), ("अर्जुन", "Arjun", "Arjoon"),
    ("ਸੁਰਿੰਦਰ", "Surinder", "Surindar"), ("मोहन", "Mohan", "Mohun"),
    ("ਬਲਜੀਤ", "Baljeet", "Baljit"), ("सुरेश", "Suresh", "Sureesh"),
    ("ਜਗਤਾਰ", "Jagtar", "Jagtaar"),
]

CH_FEMALE_NAMES = [
    ("ਪ੍ਰੀਤ", "Preet", "Preeti"), ("ਅਮਨਦੀਪ", "Amandeep", "Amandip"),
    ("ਜਸਲੀਨ", "Jasleen", "Jaslin"), ("ਕਮਲਜੀਤ", "Kamaljeet", "Kamaljit"),
    ("ਮਨਪ੍ਰੀਤ", "Manpreet", "Manprith"), ("ਨਵਜੋਤ", "Navjot", "Navjoth"),
    ("ਰਵਨੀਤ", "Ravneet", "Ravnit"), ("ਸਿਮਰਨ", "Simran", "Simren"),
    ("ਅਮਰਜੀਤ", "Amarjeet", "Amarjit"), ("ਬਲਵਿੰਦਰ", "Balwinder", "Balvindar"),
    ("ਗੁਰਦੀਪ", "Gurdeep", "Gurdip"), ("ਹਰਸਿਮਰਨ", "Harsimran", "Harsimren"),
    ("किरन", "Kiran", "Kiren"), ("रानी", "Rani", "Ranee"),
    ("ਸੁਖਪ੍ਰੀਤ", "Sukhpreet", "Sukhprith"), ("ਜਸਮੀਨ", "Jasmeen", "Jasmine"),
    ("ਸੁਰਜੀਤ", "Surjeet", "Surjit"), ("ਰਜਿੰਦਰ", "Rajinder", "Rajindar"),
    ("नीलम", "Neelam", "Nilam"), ("पूजा", "Pooja", "Puja"),
    ("अनीता", "Anita", "Aneeta"), ("ਹਰਲੀਨ", "Harleen", "Harlin"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

LGD_TN = {"state": "33", "district": "623", "subdistrict": "6230", "village": "623401"}
LGD_CH = {"state": "04", "district": "401", "ward": "401022"}

TN_LAND_WEIGHTS = [
    ("agricultural", 0.65), ("residential", 0.15), ("commercial", 0.03),
    ("government", 0.05), ("poramboke", 0.07), ("forest", 0.05),
]
CH_LAND_WEIGHTS = [
    ("residential", 0.65), ("commercial", 0.20),
    ("government", 0.10), ("industrial", 0.05),
]

TN_RIGHT_WEIGHTS = [("ownership", 0.85), ("tenancy", 0.08), ("mortgage", 0.04), ("easement", 0.03)]
CH_RIGHT_WEIGHTS = [("ownership", 0.40), ("lease", 0.55), ("government", 0.05)]

TN_MARKET_INR_PER_SQM = {
    "agricultural": (50, 250), "residential": (5000, 21000),
    "commercial": (21000, 86000), "government": (0, 0),
    "poramboke": (0, 0), "forest": (0, 0),
}
CH_MARKET_INR_PER_SQM = {
    "residential": (60000, 240000), "commercial": (240000, 1200000),
    "government": (100000, 500000), "industrial": (80000, 300000),
}

TN_TAX_ANNUAL_PER_SQM = {
    "agricultural": (0.05, 0.5), "residential": (1, 8),
    "commercial": (4, 20), "government": (0, 0),
    "poramboke": (0, 0), "forest": (0, 0),
}
CH_TAX_ANNUAL_PER_SQM = {
    "residential": (20, 150), "commercial": (100, 1000),
    "government": (0, 0), "industrial": (50, 500),
}

TN_SURVEY_PREFIXES = ["SF", "RS", "T"]
CH_BLOCKS = list("ABCDEFGHJKLMNPQRSTUVW")

COURT_TYPES = [("title_dispute", 0.40), ("boundary_dispute", 0.25),
               ("partition_suit", 0.20), ("eviction", 0.15)]
COURT_STATUS = [("pending", 0.75), ("resolved", 0.10), ("dismissed", 0.10), ("settled", 0.05)]

ZONE_TYPES = ["residential", "commercial", "agricultural", "green_belt", "industrial"]
ZONE_FSI = {"residential": (1.5, 2.5), "commercial": (2.0, 3.5),
            "agricultural": (0.5, 1.0), "green_belt": (0.0, 0.0), "industrial": (1.0, 2.0)}

ENCUMBRANCE_TYPES = [("mortgage", 0.60), ("attachment", 0.25), ("charge", 0.15)]

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def soundex(name: str) -> str:
    if not name:
        return "0000"
    name = name.upper()
    smap = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3", "L": "4", "M": "5", "N": "5", "R": "6",
    }
    code = name[0]
    for ch in name[1:]:
        if ch in smap:
            d = smap[ch]
            if d != code[-1]:
                code += d
        if len(code) >= 4:
            break
    return (code + "000")[:4]


def weighted_choice(items_weights):
    items, weights = zip(*items_weights)
    return random.choices(items, weights=weights, k=1)[0]


def make_ulpin(state_code: str, district_code: str, village_code: str, seq: int) -> str:
    sc = state_code.zfill(2)[:2]
    dc = district_code.zfill(2)[-2:]
    vc = village_code.zfill(4)[-4:]
    sq = f"{seq:06d}"
    return f"{sc}{dc}{vc}{sq}"


def random_date(start_days_ago: int, end_days_ago: int) -> datetime:
    days = random.randint(min(start_days_ago, end_days_ago), max(start_days_ago, end_days_ago))
    return datetime.now() - timedelta(days=days)


def write_jsonl(path: Path, records: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def write_csv(path: Path, records: List[Dict]) -> None:
    if not records:
        return
    all_keys = []
    for r in records:
        for k in r.keys():
            if k not in all_keys:
                all_keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            flat = {}
            for k, v in r.items():
                flat[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            writer.writerow(flat)


# ═══════════════════════════════════════════════════════════════════════════════
# GEOMETRY GENERATOR — Non-uniform grid with jitter
# ═══════════════════════════════════════════════════════════════════════════════

class GridGeometryGenerator:
    def __init__(self, rng: np.random.RandomState):
        self.rng = rng

    def generate(self, center_lon: float, center_lat: float,
                 spread_lon: float, spread_lat: float,
                 n_cols: int, n_rows: int, sigma: float = 0.5,
                 jitter_frac: float = 0.08) -> List[Polygon]:
        min_lon = center_lon - spread_lon
        max_lon = center_lon + spread_lon
        min_lat = center_lat - spread_lat
        max_lat = center_lat + spread_lat

        col_w = self.rng.lognormal(0, sigma, n_cols)
        col_w = col_w / col_w.sum() * (max_lon - min_lon)
        row_h = self.rng.lognormal(0, sigma, n_rows)
        row_h = row_h / row_h.sum() * (max_lat - min_lat)

        col_x = np.concatenate([[min_lon], np.cumsum(col_w) + min_lon])
        row_y = np.concatenate([[min_lat], np.cumsum(row_h) + min_lat])

        interior_x = col_x[1:-1].copy()
        interior_y = row_y[1:-1].copy()

        jx = np.zeros((n_cols + 1, n_rows + 1, 2))
        for ci in range(n_cols + 1):
            for ri in range(n_rows + 1):
                jx[ci, ri, 0] = col_x[ci]
                jx[ci, ri, 1] = row_y[ri]

        for ci in range(1, n_cols):
            for ri in range(1, n_rows):
                dx = col_w[ci] * jitter_frac * self.rng.uniform(-1, 1)
                dy = row_h[ri] * jitter_frac * self.rng.uniform(-1, 1)
                jx[ci, ri, 0] += dx
                jx[ci, ri, 1] += dy

        parcels = []
        for ci in range(n_cols):
            for ri in range(n_rows):
                coords = [
                    (jx[ci, ri, 0], jx[ci, ri, 1]),
                    (jx[ci + 1, ri, 0], jx[ci + 1, ri, 1]),
                    (jx[ci + 1, ri + 1, 0], jx[ci + 1, ri + 1, 1]),
                    (jx[ci, ri + 1, 0], jx[ci, ri + 1, 1]),
                ]
                try:
                    poly = Polygon(coords)
                    if poly.is_valid and poly.area > 1e-10:
                        parcels.append(poly)
                except Exception:
                    pass

        return parcels


# ═══════════════════════════════════════════════════════════════════════════════
# GROUND TRUTH GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class GroundTruthGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        Faker.seed(seed)
        self.rng = np.random.RandomState(seed)
        self.geo = GridGeometryGenerator(self.rng)
        self.gender_stats = {"male": 0, "female": 0}

    def _pick_owner(self, male_names, female_names, is_tn: bool) -> Dict:
        total = self.gender_stats["male"] + self.gender_stats["female"]
        female_target = 0.14
        if total > 0 and self.gender_stats["female"] / total < female_target:
            p_female = min(0.25, female_target * 1.5)
        else:
            p_female = female_target
        is_female = random.random() < p_female
        if is_female:
            self.gender_stats["female"] += 1
            pool = female_names
        else:
            self.gender_stats["male"] += 1
            pool = male_names
        entry = random.choice(pool)
        return {
            "name_native": entry[0],
            "name_latin": entry[1],
            "name_latin_alt": entry[2],
            "name_phonetic": soundex(entry[1]),
            "gender": "F" if is_female else "M",
        }

    def _area_to_native(self, area_sq_m: float, is_tn: bool) -> Tuple[float, str]:
        if is_tn:
            if area_sq_m >= 10000:
                return round(area_sq_m / 10000, 4), "hectare"
            elif area_sq_m >= 40:
                return round(area_sq_m / 40.47, 3), "cent"
            else:
                return round(area_sq_m / 1.67, 2), "kuli"
        else:
            if area_sq_m >= 25:
                return round(area_sq_m / 25.29, 3), "marla"
            else:
                return round(area_sq_m / 0.8361, 2), "sq_yard"

    def _gen_survey(self, idx: int, is_tn: bool) -> str:
        if is_tn:
            prefix = random.choice(TN_SURVEY_PREFIXES)
            main_num = random.randint(1, 999)
            sub = random.randint(1, 9)
            suffix = random.choice(["", "", "", "A", "B", "C", "D"])
            if prefix == "T":
                return f"T-{main_num}/{sub}{suffix}".rstrip()
            return f"{prefix}/{main_num}/{sub}{suffix}".rstrip()
        else:
            block = random.choice(CH_BLOCKS)
            num = idx + 1
            fmt = random.choice([
                f"Sec-22/{block}-{num}",
                f"22/{block}-{num}",
                f"S22/{block}-{num}",
            ])
            return fmt

    def _compute_area_sq_m(self, poly: Polygon, center_lat: float) -> float:
        cos_lat = math.cos(math.radians(center_lat))
        m_per_deg_lat = 111320.0
        m_per_deg_lon = 111320.0 * cos_lat
        coords = list(poly.exterior.coords)
        xs = [c[0] * m_per_deg_lon for c in coords]
        ys = [c[1] * m_per_deg_lat for c in coords]
        n = len(coords)
        area = 0.0
        for i in range(n - 1):
            area += xs[i] * ys[i + 1] - xs[i + 1] * ys[i]
        return abs(area) / 2.0

    def _compute_spread(self, target_count, target_mean_area, center_lat):
        cos_lat = math.cos(math.radians(center_lat))
        m_per_deg_lon = 111320.0 * cos_lat
        m_per_deg_lat = 111320.0
        total_m2 = target_count * target_mean_area
        side_m = math.sqrt(total_m2)
        spread_lon = side_m / (2 * m_per_deg_lon)
        spread_lat = side_m / (2 * m_per_deg_lat)
        return spread_lon, spread_lat

    def generate_tn_rural(self, target_count: int = 2000) -> List[Dict]:
        center_lat, center_lon = 8.7139, 77.7567
        n_cols = int(math.ceil(math.sqrt(target_count * 1.05)))
        n_rows = int(math.ceil(target_count * 1.05 / n_cols))
        spread_lon, spread_lat = self._compute_spread(target_count, 8500, center_lat)

        polys = self.geo.generate(center_lon, center_lat, spread_lon, spread_lat,
                                  n_cols, n_rows, sigma=0.80, jitter_frac=0.10)
        polys = polys[:target_count + 200]

        parcels = []
        classes = [c for c, _ in TN_LAND_WEIGHTS]
        weights = [w for _, w in TN_LAND_WEIGHTS]

        for i, poly in enumerate(polys):
            if len(parcels) >= target_count:
                break
            area_sq_m = self._compute_area_sq_m(poly, center_lat)
            if area_sq_m < 100:
                continue

            parcel_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
            ulpin = make_ulpin(LGD_TN["state"], LGD_TN["district"], LGD_TN["village"], i)
            land_class = random.choices(classes, weights=weights, k=1)[0]
            area_native, unit_native = self._area_to_native(area_sq_m, is_tn=True)

            num_owners = random.choices([1, 2, 3], weights=[0.65, 0.25, 0.10], k=1)[0]
            owners = []
            for _ in range(num_owners):
                o = self._pick_owner(TN_MALE_NAMES, TN_FEMALE_NAMES, is_tn=True)
                o["share_fraction"] = round(1.0 / num_owners, 6)
                o["right_type"] = weighted_choice(TN_RIGHT_WEIGHTS)
                owners.append(o)

            base_date = random_date(365 * 5, 30)

            parcels.append({
                "parcel_id": parcel_id,
                "ulpin": ulpin,
                "geometry": mapping(poly),
                "land_class": land_class,
                "area_sq_m": round(area_sq_m, 2),
                "area_native": area_native,
                "unit_native": unit_native,
                "owners": owners,
                "survey_number": self._gen_survey(i, is_tn=True),
                "village_code": LGD_TN["village"],
                "district_code": LGD_TN["district"],
                "state_code": "TN",
                "base_transaction_date": base_date.strftime("%Y-%m-%d"),
            })

        return parcels

    def generate_ch_urban(self, target_count: int = 1000) -> List[Dict]:
        center_lat, center_lon = 30.7333, 76.7794
        n_cols = int(math.ceil(math.sqrt(target_count * 1.05)))
        n_rows = int(math.ceil(target_count * 1.05 / n_cols))
        spread_lon, spread_lat = self._compute_spread(target_count, 312, center_lat)

        polys = self.geo.generate(center_lon, center_lat, spread_lon, spread_lat,
                                  n_cols, n_rows, sigma=0.79, jitter_frac=0.03)
        polys = polys[:target_count + 100]

        parcels = []
        classes = [c for c, _ in CH_LAND_WEIGHTS]
        weights = [w for _, w in CH_LAND_WEIGHTS]

        for i, poly in enumerate(polys):
            if len(parcels) >= target_count:
                break
            area_sq_m = self._compute_area_sq_m(poly, center_lat)
            if area_sq_m < 10:
                continue

            parcel_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
            ulpin = make_ulpin(LGD_CH["state"], LGD_CH["district"], LGD_CH["ward"], i + 10000)
            land_class = random.choices(classes, weights=weights, k=1)[0]
            area_native, unit_native = self._area_to_native(area_sq_m, is_tn=False)

            if i == 10:
                num_owners = 40
            else:
                num_owners = random.choices([1, 2, 3, 4], weights=[0.55, 0.30, 0.10, 0.05], k=1)[0]

            owners = []
            for _ in range(num_owners):
                o = self._pick_owner(CH_MALE_NAMES, CH_FEMALE_NAMES, is_tn=False)
                o["share_fraction"] = round(1.0 / num_owners, 6)
                o["right_type"] = weighted_choice(CH_RIGHT_WEIGHTS) if num_owners < 10 else "apartment_unit"
                owners.append(o)

            base_date = random_date(365 * 5, 30)

            parcels.append({
                "parcel_id": parcel_id,
                "ulpin": ulpin,
                "geometry": mapping(poly),
                "land_class": land_class,
                "area_sq_m": round(area_sq_m, 2),
                "area_native": area_native,
                "unit_native": unit_native,
                "owners": owners,
                "survey_number": self._gen_survey(i, is_tn=False),
                "village_code": LGD_CH["ward"],
                "district_code": LGD_CH["district"],
                "state_code": "CH",
                "base_transaction_date": base_date.strftime("%Y-%m-%d"),
            })

        return parcels


# ═══════════════════════════════════════════════════════════════════════════════
# DEPARTMENTAL VIEW GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

class DepartmentalViewGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed + 1000)
        np.random.seed(seed + 1000)
        self.defects: List[Dict] = []

    def _log_defect(self, dtype: str, parcel_id: str, source: str, **extra):
        d = {"type": dtype, "parcel_id": parcel_id, "source": source}
        d.update(extra)
        self.defects.append(d)

    # ─── Revenue Record of Rights ─────────────────────────────────────────────

    def generate_revenue_ror(self, parcels: List[Dict]) -> List[Dict]:
        records = []
        for p in parcels:
            record = {
                "survey_number": p["survey_number"],
                "patta_no": f"PT/{p['district_code']}/{random.randint(10000, 99999)}",
                "village_code": p["village_code"],
                "district_code": p["district_code"],
                "area": p["area_native"],
                "unit": p["unit_native"],
                "land_class": p["land_class"],
                "owners": [],
                "record_date": p["base_transaction_date"],
            }

            if random.random() < 0.15:
                stale = faker_en.name()
                record["owners"] = [{"name": stale, "share": 1.0}]
                self._log_defect("stale_ownership", p["parcel_id"], "revenue_ror")
            elif random.random() < 0.08:
                heir_prefix = random.choice(["Legal Heirs of ", "(Late) "])
                record["owners"] = [{"name": heir_prefix + p["owners"][0]["name_native"], "share": 1.0}]
                self._log_defect("deceased_owner_not_mutated", p["parcel_id"], "revenue_ror")
            else:
                for owner in p["owners"]:
                    record["owners"].append({
                        "name": owner["name_native"],
                        "share": owner["share_fraction"],
                    })

            if random.random() < 0.03:
                record["survey_number"] = ""
                self._log_defect("missing_survey_number", p["parcel_id"], "revenue_ror")

            if random.random() < 0.05:
                alt_classes = {"agricultural": "residential", "residential": "commercial",
                               "poramboke": "residential", "forest": "agricultural"}
                if p["land_class"] in alt_classes:
                    self._log_defect("land_class_outdated", p["parcel_id"], "revenue_ror",
                                     actual=alt_classes[p["land_class"]], recorded=p["land_class"])

            records.append(record)
        return records

    # ─── SRO Registrations ────────────────────────────────────────────────────

    def generate_sro_registrations(self, parcels: List[Dict]) -> List[Dict]:
        registrations = []
        is_tn = parcels[0]["state_code"] == "TN" if parcels else True
        market = TN_MARKET_INR_PER_SQM if is_tn else CH_MARKET_INR_PER_SQM

        double_sale_indices = set(random.sample(range(len(parcels)),
                                                k=max(1, int(len(parcels) * 0.025))))

        for i, p in enumerate(parcels):
            area_sqft = p["area_sq_m"] * 10.7639
            base = datetime.strptime(p["base_transaction_date"], "%Y-%m-%d")
            reg_date = base + timedelta(days=random.randint(0, 30))

            price_range = market.get(p["land_class"], (100, 1000))
            price_per_sqm = random.uniform(price_range[0], price_range[1]) if price_range[1] > 0 else 0
            sale_value = round(p["area_sq_m"] * price_per_sqm, 2)

            if random.random() < 0.12:
                sale_value = round(sale_value * random.uniform(1.5, 3.0), 2)
                self._log_defect("inflated_sale_value", p["parcel_id"], "sro_registrations",
                                 multiplier="1.5-3x")

            buyer_name = p["owners"][0]["name_latin"] if p["owners"] else faker_en.name()
            if random.random() < 0.20:
                buyer_name = p["owners"][0]["name_latin_alt"] if p["owners"] else buyer_name

            if random.random() < 0.05:
                seller = faker_en.name()
                self._log_defect("seller_not_current_owner", p["parcel_id"], "sro_registrations")
            else:
                seller = faker_en.name()

            record = {
                "doc_number": f"SRO/{p['state_code']}/{random.randint(10000, 99999)}",
                "survey_number": p["survey_number"],
                "registration_date": reg_date.strftime("%d/%m/%Y"),
                "area_sqft": round(area_sqft, 2),
                "seller": seller,
                "buyer": buyer_name,
                "sale_value": sale_value,
            }
            registrations.append(record)

            if i in double_sale_indices:
                second_date = reg_date + timedelta(days=random.randint(10, 60))
                registrations.append({
                    "doc_number": f"SRO/{p['state_code']}/{random.randint(10000, 99999)}",
                    "survey_number": p["survey_number"],
                    "registration_date": second_date.strftime("%d/%m/%Y"),
                    "area_sqft": round(area_sqft, 2),
                    "seller": buyer_name,
                    "buyer": faker_en.name(),
                    "sale_value": round(sale_value * random.uniform(1.1, 1.5), 2),
                })
                self._log_defect("double_sold", p["parcel_id"], "sro_registrations",
                                 survey_number=p["survey_number"])

        return registrations

    # ─── Municipal / ULB Property Tax ─────────────────────────────────────────

    def generate_municipal_tax(self, parcels: List[Dict]) -> List[Dict]:
        records = []
        is_tn = parcels[0]["state_code"] == "TN" if parcels else True
        tax_rates = TN_TAX_ANNUAL_PER_SQM if is_tn else CH_TAX_ANNUAL_PER_SQM

        for p in parcels:
            prop_id = f"TAX-{p['district_code']}-{random.randint(1000, 9999)}"
            area_recorded = p["area_sq_m"]

            if random.random() < 0.08:
                factor = random.choice([random.uniform(0.70, 0.85), random.uniform(1.15, 1.35)])
                area_recorded = area_recorded * factor
                self._log_defect("area_mismatch", p["parcel_id"], "municipal_tax",
                                 actual_area=p["area_sq_m"], recorded_area=round(area_recorded, 2))

            rate_range = tax_rates.get(p["land_class"], (0.1, 1))
            tax_per_sqm = random.uniform(rate_range[0], rate_range[1])
            tax_due = round(area_recorded * tax_per_sqm, 2)

            survey = p["survey_number"] if random.random() > 0.10 else ""
            if not survey:
                self._log_defect("missing_survey_in_tax", p["parcel_id"], "municipal_tax")

            owner_name = p["owners"][0]["name_latin_alt"] if p["owners"] else ""
            last_paid = random_date(400, 0).strftime("%Y-%m-%d")

            records.append({
                "property_id": prop_id,
                "survey_number": survey,
                "area_sq_m": round(area_recorded, 2),
                "owner_name": owner_name,
                "tax_due": tax_due,
                "last_paid": last_paid,
                "assessment_year": datetime.now().year,
            })

        if random.random() < 0.5:
            for _ in range(max(1, int(len(parcels) * 0.02))):
                records.append({
                    "property_id": f"TAX-{parcels[0]['district_code']}-{random.randint(1000, 9999)}",
                    "survey_number": "",
                    "area_sq_m": round(random.uniform(50, 500), 2),
                    "owner_name": faker_en.name(),
                    "tax_due": round(random.uniform(500, 10000), 2),
                    "last_paid": random_date(300, 0).strftime("%Y-%m-%d"),
                    "assessment_year": datetime.now().year,
                })
                self._log_defect("ghost_property", "NONE", "municipal_tax")

        return records

    # ─── Building Permissions ─────────────────────────────────────────────────

    def generate_building_permissions(self, parcels: List[Dict]) -> List[Dict]:
        records = []
        eligible = [p for p in parcels if p["land_class"] in ("residential", "commercial")]
        for p in eligible:
            if random.random() >= 0.40:
                continue
            geom = shape(p["geometry"])
            centroid = geom.centroid
            approved_frac = random.uniform(0.40, 0.60)
            approved_area = round(p["area_sq_m"] * approved_frac, 2)
            permit_date = random_date(900, 90)

            status = "approved"
            if random.random() < 0.05:
                status = random.choice(["rejected_but_built", "unauthorized"])
                self._log_defect("unauthorized_construction", p["parcel_id"], "building_permissions")
            elif random.random() < 0.10:
                if (datetime.now() - permit_date).days > 365 * 3:
                    status = "expired"
                    self._log_defect("expired_permit", p["parcel_id"], "building_permissions")

            records.append({
                "permit_number": f"BP-{p['district_code']}-{random.randint(1000, 9999)}",
                "plot_number": p["survey_number"].replace("/", "-"),
                "latitude": round(centroid.y, 7),
                "longitude": round(centroid.x, 7),
                "approved_area_sq_m": approved_area,
                "permit_date": permit_date.strftime("%Y-%m-%d"),
                "owner": p["owners"][0]["name_latin"] if p["owners"] else "",
                "status": status,
            })
        return records

    # ─── Court Cases ──────────────────────────────────────────────────────────

    def generate_court_cases(self, parcels: List[Dict]) -> List[Dict]:
        cases = []
        disputed = random.sample(parcels, k=max(1, int(len(parcels) * 0.05)))

        for p in disputed:
            has_survey = random.random() > 0.60
            case_type = weighted_choice(COURT_TYPES)
            status = weighted_choice(COURT_STATUS)
            filing_date = random_date(1500, 30)

            plaintiff = p["owners"][0]["name_latin"] if p["owners"] else faker_en.name()
            if random.random() < 0.30:
                initial = plaintiff.split()[0][0] + "." if " " in plaintiff else plaintiff[:3]
                plaintiff = initial + " " + plaintiff.split()[-1] if " " in plaintiff else plaintiff

            case = {
                "case_number": f"CC/{random.randint(1000, 9999)}/20{random.randint(18, 26)}",
                "filing_date": filing_date.strftime("%d-%m-%Y"),
                "plaintiff": plaintiff,
                "defendant": faker_en.name(),
                "survey_number": p["survey_number"] if has_survey else "",
                "property_description": f"Land near {p['village_code']}" if not has_survey else "",
                "case_type": case_type,
                "status": status,
            }

            if random.random() < 0.15:
                extra_surveys = random.sample(
                    [pp["survey_number"] for pp in parcels if pp["parcel_id"] != p["parcel_id"]],
                    k=min(3, len(parcels) - 1)
                )
                case["related_survey_numbers"] = ",".join(extra_surveys)

            cases.append(case)

            if not has_survey:
                self._log_defect("unlinked_dispute", p["parcel_id"], "court_cases",
                                 case_number=case["case_number"])

        return cases

    # ─── Land Use Zoning ──────────────────────────────────────────────────────

    def generate_land_use_zoning(self, parcels: List[Dict]) -> List[Dict]:
        if not parcels:
            return []
        state = parcels[0]["state_code"]
        zones = []
        num_zones = random.randint(4, 6)

        for i in range(num_zones):
            sample = random.sample(parcels, k=min(40, len(parcels)))
            points = [shape(p["geometry"]).centroid for p in sample]
            if len(points) < 3:
                continue
            hull = MultiPoint(points).convex_hull
            if hull.geom_type == "Point" or hull.area < 1e-10:
                continue
            zone_geom = hull.buffer(0.001)
            zone_type = random.choice(ZONE_TYPES)
            fsi_range = ZONE_FSI.get(zone_type, (1.0, 2.0))

            zones.append({
                "zone_id": f"Z-{state}-{i + 1:02d}",
                "zone_type": zone_type,
                "geometry": mapping(zone_geom),
                "fsi": round(random.uniform(fsi_range[0], fsi_range[1]), 2),
                "master_plan_year": random.choice([2006, 2011, 2016, 2021]),
            })

        conflict_count = 0
        for p in parcels:
            p_centroid = shape(p["geometry"]).centroid
            for z in zones:
                z_geom = shape(z["geometry"])
                if z_geom.contains(p_centroid):
                    if p["land_class"] != z["zone_type"] and random.random() < 0.10:
                        self._log_defect("zone_use_conflict", p["parcel_id"], "land_use_zoning",
                                         parcel_class=p["land_class"], zone_type=z["zone_type"])
                        conflict_count += 1
                    break
            if conflict_count >= int(len(parcels) * 0.10):
                break

        return zones

    # ─── Encumbrance Certificates ─────────────────────────────────────────────

    def generate_encumbrance_ec(self, parcels: List[Dict]) -> List[Dict]:
        ecs = []
        for p in parcels:
            from_date = (datetime.now() - timedelta(days=365 * 10)).strftime("%d/%m/%Y")
            to_date = datetime.now().strftime("%d/%m/%Y")
            ec = {
                "survey_number": p["survey_number"],
                "district_code": p["district_code"],
                "from_date": from_date,
                "to_date": to_date,
                "encumbrances": [],
            }

            if random.random() < 0.15:
                enc_type = weighted_choice(ENCUMBRANCE_TYPES)
                amount = round(random.uniform(100000, 5000000), 2)
                enc_date = random_date(1000, 30)

                ec["encumbrances"].append({
                    "type": enc_type,
                    "amount": amount,
                    "date": enc_date.strftime("%d/%m/%Y"),
                    "doc_number": f"DOC/{random.randint(10000, 99999)}",
                })

                if random.random() < 0.02:
                    ec["encumbrances"].append({
                        "type": weighted_choice(ENCUMBRANCE_TYPES),
                        "amount": round(random.uniform(50000, 3000000), 2),
                        "date": random_date(800, 100).strftime("%d/%m/%Y"),
                        "doc_number": f"DOC/{random.randint(10000, 99999)}",
                    })
                    self._log_defect("dual_mortgage", p["parcel_id"], "encumbrance_ec")

                if random.random() < 0.05:
                    self._log_defect("expired_encumbrance_not_cleared", p["parcel_id"],
                                     "encumbrance_ec")
            else:
                if random.random() < 0.10:
                    self._log_defect("missing_encumbrance", p["parcel_id"], "encumbrance_ec",
                                     note="Oral mortgage arrangement not reflected")

            ecs.append(ec)
        return ecs


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIAL DEFECT INJECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class SpecialDefectInjector:
    def __init__(self):
        self.defects: List[Dict] = []

    def inject(self, parcels: List[Dict]) -> None:
        self._circular_ring(parcels)
        self._survey_renumber(parcels)
        self._overlapping_geometry(parcels)
        self._benami_pattern(parcels)
        self._rapid_flip(parcels)
        self._gender_anomaly_cluster(parcels)

    def _circular_ring(self, parcels: List[Dict]) -> None:
        if len(parcels) < 54:
            return
        ring = parcels[50:54]
        parties = [faker_en.name() for _ in range(4)]
        for i, p in enumerate(ring):
            p["_circular_ring_party"] = parties[i]
            self.defects.append({
                "type": "circular_transaction_ring",
                "parcel_id": p["parcel_id"],
                "party": parties[i],
                "next_party": parties[(i + 1) % 4],
            })

    def _survey_renumber(self, parcels: List[Dict]) -> None:
        if len(parcels) < 100:
            return
        p = parcels[99]
        old_survey = p["survey_number"]
        new_survey = old_survey.replace("/", "-NEW-") if "/" in old_survey else old_survey + "-NEW"
        self.defects.append({
            "type": "survey_renumber_lineage",
            "parcel_id": p["parcel_id"],
            "old_survey": old_survey,
            "new_survey": new_survey,
        })

    def _overlapping_geometry(self, parcels: List[Dict]) -> None:
        if len(parcels) < 80:
            return
        p1, p2 = parcels[78], parcels[79]
        g1 = shape(p1["geometry"])
        g2 = shape(p2["geometry"])
        shift_x = (g1.centroid.x - g2.centroid.x) * 0.3
        shift_y = (g1.centroid.y - g2.centroid.y) * 0.3
        g2_shifted = translate(g2, xoff=shift_x, yoff=shift_y)
        p2["geometry"] = mapping(g2_shifted)
        self.defects.append({
            "type": "overlapping_geometry",
            "parcel_a": p1["parcel_id"],
            "parcel_b": p2["parcel_id"],
        })

    def _benami_pattern(self, parcels: List[Dict]) -> None:
        if len(parcels) < 200:
            return
        surname = random.choice(["Kumar", "Singh", "Sharma", "Murugan", "Selvam"])
        benami_parcels = parcels[180:188]
        base_date = random_date(60, 30)
        for j, p in enumerate(benami_parcels):
            fake_first = faker_en.first_name()
            p["owners"] = [{
                "name_native": p["owners"][0]["name_native"] if p["owners"] else "",
                "name_latin": f"{fake_first} {surname}",
                "name_latin_alt": f"{fake_first} {surname}",
                "name_phonetic": soundex(fake_first),
                "gender": "M",
                "share_fraction": 1.0,
                "right_type": "ownership",
            }]
            p["base_transaction_date"] = (base_date + timedelta(days=j * 2)).strftime("%Y-%m-%d")
            self.defects.append({
                "type": "benami_pattern",
                "parcel_id": p["parcel_id"],
                "shared_surname": surname,
            })

    def _rapid_flip(self, parcels: List[Dict]) -> None:
        if len(parcels) < 160:
            return
        p = parcels[155]
        self.defects.append({
            "type": "rapid_flip",
            "parcel_id": p["parcel_id"],
            "survey_number": p["survey_number"],
            "flips": 3,
            "window_days": 90,
        })

    def _gender_anomaly_cluster(self, parcels: List[Dict]) -> None:
        if len(parcels) < 151:
            return
        for p in parcels[120:150]:
            new_owners = []
            for o in p["owners"]:
                if o["gender"] == "F":
                    pool = TN_MALE_NAMES if p["state_code"] == "TN" else CH_MALE_NAMES
                    replacement = random.choice(pool)
                    o["name_native"] = replacement[0]
                    o["name_latin"] = replacement[1]
                    o["name_latin_alt"] = replacement[2]
                    o["gender"] = "M"
                new_owners.append(o)
            p["owners"] = new_owners
        self.defects.append({
            "type": "gender_anomaly_cluster",
            "parcel_range": "120-149",
            "note": "0% female ownership in cluster vs 14% national average",
        })


# ═══════════════════════════════════════════════════════════════════════════════
# RAPID FLIP SRO RECORDS HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def generate_rapid_flip_sro(parcel: Dict) -> List[Dict]:
    base = datetime.strptime(parcel["base_transaction_date"], "%Y-%m-%d")
    area_sqft = parcel["area_sq_m"] * 10.7639
    records = []
    prev_buyer = parcel["owners"][0]["name_latin"] if parcel["owners"] else faker_en.name()
    base_value = parcel["area_sq_m"] * random.uniform(5000, 20000)

    for flip in range(3):
        reg_date = base + timedelta(days=flip * 30)
        value = base_value * (1 + 0.75 * flip)
        new_buyer = faker_en.name()
        records.append({
            "doc_number": f"SRO/{parcel['state_code']}/{random.randint(10000, 99999)}",
            "survey_number": parcel["survey_number"],
            "registration_date": reg_date.strftime("%d/%m/%Y"),
            "area_sqft": round(area_sqft, 2),
            "seller": prev_buyer,
            "buyer": new_buyer,
            "sale_value": round(value, 2),
        })
        prev_buyer = new_buyer
    return records


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Bhoomi Dhrishti realistic mock data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tn-count", type=int, default=2000)
    parser.add_argument("--ch-count", type=int, default=1000)
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Write all output into this directory instead of data/raw + data/ground_truth")
    args = parser.parse_args()

    print(f"Generating realistic data with seed={args.seed}, TN={args.tn_count}, CH={args.ch_count}...")

    if args.output_dir:
        base = Path(args.output_dir)
    else:
        base = Path(__file__).parent.parent
    raw_tn = base / "raw" / "tn_rural"
    raw_ch = base / "raw" / "ch_urban"
    ground_truth_dir = base / "ground_truth"
    for d in [raw_tn, raw_ch, ground_truth_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Ground Truth ──────────────────────────────────────────────────────────
    gen = GroundTruthGenerator(seed=args.seed)
    tn_parcels = gen.generate_tn_rural(target_count=args.tn_count)
    ch_parcels = gen.generate_ch_urban(target_count=args.ch_count)
    all_parcels = tn_parcels + ch_parcels

    print(f"  TN rural: {len(tn_parcels)} parcels")
    print(f"  CH urban: {len(ch_parcels)} parcels (1 apartment block with 40 units)")

    # Area distribution check
    tn_areas = [p["area_sq_m"] for p in tn_parcels]
    ch_areas = [p["area_sq_m"] for p in ch_parcels]
    if tn_areas:
        pct_small = sum(1 for a in tn_areas if a < 20000) / len(tn_areas) * 100
        print(f"  TN area: median={np.median(tn_areas):.0f} sq_m, "
              f"mean={np.mean(tn_areas):.0f}, "
              f"<2ha={pct_small:.1f}% (target: 86.2%)")
    if ch_areas:
        print(f"  CH area: median={np.median(ch_areas):.0f} sq_m, "
              f"mean={np.mean(ch_areas):.0f}")

    # Gender check
    total_m = gen.gender_stats["male"]
    total_f = gen.gender_stats["female"]
    total = total_m + total_f
    print(f"  Gender: {total_f}/{total} female = {total_f/total*100:.1f}% (target: 14%)")

    # ── Special Defects ───────────────────────────────────────────────────────
    injector = SpecialDefectInjector()
    injector.inject(tn_parcels)
    if len(ch_parcels) > 50:
        injector.inject(ch_parcels)

    # ── Write Ground Truth ────────────────────────────────────────────────────
    gt_records = []
    for p in all_parcels:
        rec = dict(p)
        rec.pop("_circular_ring_party", None)
        gt_records.append(rec)
    write_jsonl(ground_truth_dir / "parcels.jsonl", gt_records)

    # ── Departmental Views ────────────────────────────────────────────────────
    print("\nGenerating departmental views...")
    dept = DepartmentalViewGenerator(seed=args.seed)

    for label, parcels, out_dir in [("TN", tn_parcels, raw_tn), ("CH", ch_parcels, raw_ch)]:
        ror = dept.generate_revenue_ror(parcels)
        sro = dept.generate_sro_registrations(parcels)
        tax = dept.generate_municipal_tax(parcels)
        bp = dept.generate_building_permissions(parcels)
        cases = dept.generate_court_cases(parcels)
        zones = dept.generate_land_use_zoning(parcels)
        ec = dept.generate_encumbrance_ec(parcels)

        if len(parcels) > 155:
            rapid_flip_parcel = parcels[155]
            sro.extend(generate_rapid_flip_sro(rapid_flip_parcel))

        write_jsonl(out_dir / "revenue_ror.jsonl", ror)
        write_csv(out_dir / "sro_registrations.csv", sro)
        write_csv(out_dir / "municipal_tax.csv", tax)
        write_csv(out_dir / "building_permissions.csv", bp)
        write_jsonl(out_dir / "court_cases.jsonl", cases)
        write_jsonl(out_dir / "land_use_zones.jsonl", zones)
        write_jsonl(out_dir / "encumbrance_ec.jsonl", ec)

        print(f"  {label}: {len(ror)} RoR, {len(sro)} SRO, {len(tax)} tax, "
              f"{len(bp)} permits, {len(cases)} cases, {len(zones)} zones, {len(ec)} ECs")

    # ── Defects Manifest ──────────────────────────────────────────────────────
    all_defects = dept.defects + injector.defects
    manifest = {
        "seed": args.seed,
        "generated_at": datetime.now().isoformat(),
        "total_parcels": len(all_parcels),
        "tn_parcels": len(tn_parcels),
        "ch_parcels": len(ch_parcels),
        "defects": all_defects,
    }
    with open(ground_truth_dir / "defects_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Generated {len(all_defects)} deliberate defects")
    dtype_counts: Dict[str, int] = {}
    for d in all_defects:
        dtype_counts[d["type"]] = dtype_counts.get(d["type"], 0) + 1
    for dtype, count in sorted(dtype_counts.items()):
        print(f"  {dtype}: {count}")

    print(f"\nOutput:")
    print(f"  Ground truth: {ground_truth_dir}/parcels.jsonl")
    print(f"  Defects:      {ground_truth_dir}/defects_manifest.json")
    print(f"  TN views:     {raw_tn}/")
    print(f"  CH views:     {raw_ch}/")


if __name__ == "__main__":
    main()
