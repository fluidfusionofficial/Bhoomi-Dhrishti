"""
Standalone ETL Engine Example

Demonstrates end-to-end usage of the ETL mapping engine.
Run with: python examples/run_etl_example.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from app.engine.mapper import SourceMapper
from app.engine.validator import DataQualityValidator


def main():
    """Run ETL example."""
    print("=" * 80)
    print("Bhoomi Dhrishti - ETL Mapping Engine Example")
    print("=" * 80)

    # Paths
    base_dir = Path(__file__).parent.parent
    mapping_path = base_dir / "data" / "mappings" / "tn_rural" / "mapping.yaml"
    sample_csv = base_dir / "data" / "samples" / "tn_revenue_sample.csv"

    # Check if files exist
    if not mapping_path.exists():
        print(f"❌ Mapping file not found: {mapping_path}")
        return 1

    if not sample_csv.exists():
        print(f"❌ Sample CSV not found: {sample_csv}")
        print("Creating sample data...")
        # Create sample data if not exists
        create_sample_data(sample_csv)

    print(f"\n📁 Input Files:")
    print(f"   Mapping: {mapping_path}")
    print(f"   Data: {sample_csv}")

    # Step 1: Load mapping configuration
    print(f"\n🔧 Step 1: Loading Mapping Configuration")
    print("-" * 80)
    try:
        mapper = SourceMapper(mapping_path)
        print(f"✅ Loaded mapping for: {mapper.config['source_type']}")
        print(f"   Source System: {mapper.config.get('source_system', 'N/A')}")
        print(f"   Fields Mapped: {len(mapper.config['field_mapping'])}")
    except Exception as e:
        print(f"❌ Error loading mapping: {e}")
        return 1

    # Step 2: Load source data
    print(f"\n📊 Step 2: Loading Source Data")
    print("-" * 80)
    try:
        df = pd.read_csv(sample_csv)
        source_records = df.to_dict("records")
        print(f"✅ Loaded {len(source_records)} source records")
        print(f"   Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return 1

    # Step 3: Apply field mappings
    print(f"\n🔄 Step 3: Applying Field Mappings")
    print("-" * 80)
    canonical_records = []
    mapping_errors = 0

    for idx, record in enumerate(source_records):
        try:
            context = {"district_lgd_code": record.get("District_Code")}
            canonical = mapper.apply_mapping(record, context)
            canonical_records.append(canonical)
        except Exception as e:
            print(f"   ⚠️ Error mapping row {idx}: {e}")
            mapping_errors += 1

    print(f"✅ Mapped {len(canonical_records)} records")
    if mapping_errors > 0:
        print(f"   ⚠️ Mapping errors: {mapping_errors}")

    # Show sample mapped record
    if canonical_records:
        print(f"\n📋 Sample Canonical Record (row 0):")
        print(json.dumps(canonical_records[0], indent=2, default=str))

    # Step 4: Validate data quality
    print(f"\n✅ Step 4: Validating Data Quality")
    print("-" * 80)
    try:
        validator = DataQualityValidator("revenue_ror")
        report = validator.validate_records(canonical_records)

        print(f"   Total Rows: {report.total_rows}")
        print(f"   Valid Rows: {report.valid_rows}")
        print(f"   Quality Score: {report.quality_score:.2f}%")
        print(f"   Issues Found: {len(report.issues)}")

        # Show field statistics
        print(f"\n📈 Field Statistics:")
        for field, stats in list(report.field_statistics.items())[:5]:
            print(f"   {field}:")
            if "null_count" in stats:
                print(f"      Null: {stats['null_count']} ({stats['null_rate']:.1%})")
            if "mean" in stats:
                print(f"      Mean: {stats['mean']:.2f}")
            if "unique_count" in stats:
                print(f"      Unique: {stats['unique_count']}")

        # Show issues
        if report.issues:
            print(f"\n⚠️ Data Quality Issues (showing first 5):")
            for issue in report.issues[:5]:
                print(f"   Row {issue['row']}, Field '{issue.get('field')}': {issue['issue']}")

        # Save DQ report
        processed_dir = base_dir / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        report_path = processed_dir / "example_dq_report.json"

        with open(report_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)

        print(f"\n💾 DQ Report saved to: {report_path}")

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return 1

    # Step 5: Summary
    print(f"\n" + "=" * 80)
    print(f"✅ ETL Pipeline Completed Successfully!")
    print("=" * 80)
    print(f"Summary:")
    print(f"   Source Records: {len(source_records)}")
    print(f"   Canonical Records: {len(canonical_records)}")
    print(f"   Valid Records: {report.valid_rows}")
    print(f"   Quality Score: {report.quality_score:.2f}%")
    print(f"   Mapping Errors: {mapping_errors}")
    print(f"   Validation Issues: {len(report.issues)}")
    print(f"\n🎉 Ready for database loading!")

    return 0


def create_sample_data(output_path: Path):
    """Create sample CSV data if not exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_data = """Survey_No,Extent,Unit,Pattadar_Name,Pattadar_Name_Tamil,District_Code,Village_Code,Land_Class,Patta_Date,FMB_No,Chitta_No
0123/4A,5.5,cent,Ramesh Kumar,ரமேஷ் குமார்,33001,3300101,AGRICULTURAL,15/08/2020,FMB-123,CHT-4567
234/1,2.3,acre,Lakshmi Devi,லட்சுமி தேவி,33001,3300101,RESIDENTIAL,22/03/2019,FMB-234,CHT-4568
345/2B,12.8,veli,Murugan S,முருகன் எஸ்,33001,3300102,AGRICULTURAL,10/11/2021,FMB-345,CHT-4569"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sample_data)

    print(f"✅ Created sample data at: {output_path}")


if __name__ == "__main__":
    sys.exit(main())
