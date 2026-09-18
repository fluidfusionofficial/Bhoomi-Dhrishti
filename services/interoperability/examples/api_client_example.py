"""
ETL Mapping Engine - Python API Client Example

Demonstrates REST API usage with Python httpx library.
Run with: python examples/api_client_example.py
"""

import json
import sys
from pathlib import Path

import httpx


BASE_URL = "http://localhost:8005"
API_BASE = f"{BASE_URL}/ingest"


class ETLAPIClient:
    """Simple API client for ETL ingestion endpoints."""

    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.client = httpx.Client(timeout=300.0)

    def list_sources(self):
        """List available source mappings."""
        response = self.client.get(f"{self.base_url}/sources")
        response.raise_for_status()
        return response.json()

    def get_mapping(self, state_code: str, context: str):
        """Get mapping configuration."""
        response = self.client.get(f"{self.base_url}/mappings/{state_code}_{context}")
        response.raise_for_status()
        return response.json()

    def ingest_file(
        self,
        source_type: str,
        file_path: Path,
        state_code: str = "tn",
        context: str = "rural",
        conflict_strategy: str = "update"
    ):
        """
        Upload and ingest data file.

        Args:
            source_type: Type of data (revenue_ror, sro_registration)
            file_path: Path to CSV/JSON file
            state_code: State code (default: tn)
            context: Context identifier (default: rural)
            conflict_strategy: "update" or "ignore"

        Returns:
            Ingestion result with job_id and DQ report
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/csv")}
            params = {
                "state_code": state_code,
                "context": context,
                "conflict_strategy": conflict_strategy,
            }

            response = self.client.post(
                f"{self.base_url}/{source_type}",
                files=files,
                params=params
            )
            response.raise_for_status()
            return response.json()

    def get_job_status(self, job_id: str):
        """Get ingestion job status."""
        response = self.client.get(f"{self.base_url}/status/{job_id}")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close HTTP client."""
        self.client.close()


def main():
    """Run API client examples."""
    print("=" * 80)
    print("Bhoomi Dhrishti - ETL API Client Example")
    print("=" * 80)

    client = ETLAPIClient()

    try:
        # Example 1: List available sources
        print("\n📋 Example 1: List Available Source Mappings")
        print("-" * 80)
        sources = client.list_sources()
        print(f"Found {len(sources.get('sources', []))} source mappings:")
        for source in sources.get("sources", []):
            print(f"  - {source['identifier']}: {source['source_type']} ({source['source_system']})")

        # Example 2: Get mapping configuration
        print("\n🔧 Example 2: Get Mapping Configuration")
        print("-" * 80)
        try:
            mapping = client.get_mapping("tn", "rural")
            print(f"✅ Retrieved mapping for tn_rural")
            print(f"Content length: {len(mapping.get('content', ''))} characters")
            print("\nFirst 300 characters:")
            print(mapping.get("content", "")[:300])
            print("...")
        except httpx.HTTPError as e:
            print(f"⚠️ Could not retrieve mapping: {e}")

        # Example 3: Ingest data file
        print("\n📤 Example 3: Upload and Ingest Data")
        print("-" * 80)

        base_dir = Path(__file__).parent.parent
        sample_file = base_dir / "data" / "samples" / "tn_revenue_sample.csv"

        if sample_file.exists():
            print(f"Uploading: {sample_file}")

            result = client.ingest_file(
                source_type="revenue_ror",
                file_path=sample_file,
                state_code="tn",
                context="rural",
                conflict_strategy="update"
            )

            print(f"\n✅ Ingestion Completed!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Total Records: {result.get('total_records')}")
            print(f"   Rows Loaded: {result.get('rows_loaded')}")
            print(f"   Quality Score: {result.get('quality_score'):.2f}%")

            # Show DQ report summary
            dq_report = result.get("dq_report", {})
            if dq_report:
                print(f"\n📊 Data Quality Report:")
                print(f"   Valid Rows: {dq_report.get('valid_rows')}/{dq_report.get('total_rows')}")
                print(f"   Issues: {len(dq_report.get('issues', []))}")

                # Show field statistics
                field_stats = dq_report.get("field_statistics", {})
                if field_stats:
                    print(f"\n   Top Fields:")
                    for field, stats in list(field_stats.items())[:3]:
                        null_rate = stats.get("null_rate", 0)
                        print(f"      {field}: {null_rate:.1%} null")

            # Save full response
            output_path = base_dir / "data" / "processed" / "api_example_response.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n💾 Full response saved to: {output_path}")

            # Example 4: Check job status
            print("\n🔍 Example 4: Check Job Status")
            print("-" * 80)
            job_id = result.get("job_id")
            if job_id:
                status = client.get_job_status(job_id)
                print(f"Job Status: {status.get('status')}")
                print(f"Created: {status.get('created_at')}")
                if status.get("completed_at"):
                    print(f"Completed: {status.get('completed_at')}")

        else:
            print(f"⚠️ Sample file not found: {sample_file}")
            print("Skipping ingestion example")

        # Summary
        print("\n" + "=" * 80)
        print("✅ API Examples Complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Check the processed data in database")
        print("  2. Review DQ reports in data/processed/")
        print("  3. Try with your own data files")
        print("  4. Explore API docs at http://localhost:8005/docs")

    except httpx.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print("\nMake sure the service is running:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8005")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
