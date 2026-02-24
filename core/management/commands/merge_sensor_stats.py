"""
Django management command to process FULL sensor CSVs and create daily min/max stats.
No arguments needed - runs automatically.

Usage:
    python manage.py merge_sensor_stats
"""

import logging
import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from utils.calculate_max_min import (
    discover_files,
    process_full_csv,
    merge_daily_stats,
    write_stats,
    DATA_DIR,
    OUTPUT_DIR
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Process FULL_*.csv files and create daily min/max statistics. "
        "Output: Date, max/min for temperature, humidity, pressure, P1, P2. "
        "No arguments needed - runs automatically."
    )

    def handle(self, *args, **options):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s',
            stream=self.stdout
        )

        self.stdout.write("=" * 50)
        self.stdout.write("Sensor Data Processor")
        self.stdout.write(f"Data: {DATA_DIR}")
        self.stdout.write(f"Output: {OUTPUT_DIR}")
        self.stdout.write("=" * 50)

        # Validate data directory
        if not DATA_DIR.exists():
            self.stdout.write(self.style.ERROR(f"Data directory not found: {DATA_DIR}"))
            return 1

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Discover FULL_*.csv files
        sensor_files = discover_files()

        if not sensor_files:
            self.stdout.write(self.style.WARNING("No FULL_*.csv files found"))
            return 0

        self.stdout.write(f"\nFound {len(sensor_files)} sensor(s) to process\n")

        # Process each sensor
        processed = 0
        failed = 0

        for sensor_id in sorted(sensor_files.keys()):
            files = sensor_files[sensor_id]
            output_path = OUTPUT_DIR / f"{sensor_id}_daily_stats.csv"

            self.stdout.write(f"Processing {sensor_id} ({len(files)} file(s))...")

            # Process all files for this sensor
            all_stats = []
            for filepath in files:
                file_stats = process_full_csv(filepath, sensor_id)
                if file_stats:
                    all_stats.append(file_stats)

            # Merge and write
            if all_stats:
                merged = merge_daily_stats(all_stats)
                write_stats(sensor_id, merged, output_path)
                processed += 1
            else:
                write_stats(sensor_id, {}, output_path)
                processed += 1

            self.stdout.write("")

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Complete: {processed} processed, {failed} failed")
        self.stdout.write(f"Output: {OUTPUT_DIR}")

        return 0