"""
Simple sensor data processor.
Scans for FULL_*.csv files and creates daily min/max statistics.
Output: max_min_data/{sensor_id}_daily_stats.csv
Columns are selected based on sensor_type: BMP180(pressure), DHT22(temp/humidity), SDS011(P1/P2)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import defaultdict

import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - EDIT THESE PATHS IF NEEDED
BASE_DIR = Path.cwd()  # Current directory where script runs
DATA_DIR = BASE_DIR / "sensor_data_by_station"
OUTPUT_DIR = BASE_DIR / "max_min_data"

# Sensor type to columns mapping
SENSOR_TYPE_COLUMNS = {
    'BMP180': ['pressure'],
    'DHT22': ['temperature', 'humidity'],
    'SDS011': ['P1', 'P2'],
}


@dataclass
class DailyStats:
    """Tracks daily min/max for relevant columns."""
    date: str
    stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    columns_found: Set[str] = field(default_factory=set)

    def update(self, col: str, value: float):
        if pd.isna(value):
            return

        # Initialize column if first time seeing it
        if col not in self.stats:
            self.stats[col] = {'min': np.nan, 'max': np.nan}
            self.columns_found.add(col)

        current_min = self.stats[col]['min']
        current_max = self.stats[col]['max']

        if pd.isna(current_min) or value < current_min:
            self.stats[col]['min'] = value
        if pd.isna(current_max) or value > current_max:
            self.stats[col]['max'] = value

    def has_data(self) -> bool:
        return len(self.columns_found) > 0

    def to_dict(self) -> Dict:
        result = {'Date': self.date}
        for col in sorted(self.columns_found):
            result[f'max_{col}'] = self.stats[col]['max'] if not pd.isna(self.stats[col]['max']) else np.nan
            result[f'min_{col}'] = self.stats[col]['min'] if not pd.isna(self.stats[col]['min']) else np.nan
        return result

    def get_columns(self) -> Set[str]:
        return self.columns_found


def parse_timestamp(ts_val) -> Optional[datetime]:
    """Parse various timestamp formats."""
    if pd.isna(ts_val):
        return None

    ts_str = str(ts_val).strip()
    formats = [
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue

    try:
        return pd.to_datetime(ts_str)
    except:
        return None


def detect_sensor_type(chunk: pd.DataFrame) -> Optional[str]:
    """Detect sensor type from sensor_type column or column presence."""
    # Check sensor_type column first
    if 'sensor_type' in chunk.columns:
        # Get first non-null value
        sensor_type = chunk['sensor_type'].dropna().iloc[0] if not chunk['sensor_type'].dropna().empty else None
        if sensor_type and str(sensor_type).upper() in [k.upper() for k in SENSOR_TYPE_COLUMNS.keys()]:
            # Normalize to match our keys
            for key in SENSOR_TYPE_COLUMNS.keys():
                if str(sensor_type).upper() == key.upper():
                    return key
            return str(sensor_type).upper()

    # Fallback: detect by column presence
    columns = set(chunk.columns)
    if 'pressure' in columns and 'temperature' not in columns:
        return 'BMP180'
    elif 'temperature' in columns and 'humidity' in columns:
        return 'DHT22'
    elif 'P1' in columns and 'P2' in columns:
        return 'SDS011'

    return None


def get_columns_for_sensor(sensor_type: Optional[str]) -> List[str]:
    """Get columns to process based on sensor type."""
    if not sensor_type:
        return []  # Unknown type, process nothing

    return SENSOR_TYPE_COLUMNS.get(sensor_type, [])


def process_full_csv(filepath: Path, sensor_id: str) -> Dict[str, DailyStats]:
    """Process a single FULL_*.csv file."""
    daily_data: Dict[str, DailyStats] = {}
    detected_type = None

    try:
        file_size = filepath.stat().st_size

        # Use chunks for large files
        if file_size > 50 * 1024 * 1024:
            chunks = pd.read_csv(filepath, sep=';', chunksize=100000, dtype=str, on_bad_lines='skip')
        else:
            df = pd.read_csv(filepath, sep=';', dtype=str, on_bad_lines='skip')
            chunks = [df]

        for chunk in chunks:
            if 'timestamp' not in chunk.columns:
                continue

            # Detect sensor type from first chunk
            if detected_type is None:
                detected_type = detect_sensor_type(chunk)
                if detected_type:
                    logger.info(f"    Detected sensor type: {detected_type}")
                else:
                    logger.warning(f"    Unknown sensor type in {filepath.name}, skipping")
                    continue

            # Get columns to process for this sensor type
            target_cols = get_columns_for_sensor(detected_type)
            if not target_cols:
                logger.warning(f"    No target columns for sensor type: {detected_type}")
                continue

            chunk['parsed_time'] = chunk['timestamp'].apply(parse_timestamp)
            chunk = chunk[chunk['parsed_time'].notna()]

            if chunk.empty:
                continue

            chunk['date'] = chunk['parsed_time'].dt.strftime('%Y-%m-%d')

            # Only process columns relevant to this sensor type
            for col in target_cols:
                if col not in chunk.columns:
                    continue

                chunk[f'{col}_num'] = pd.to_numeric(chunk[col], errors='coerce')
                col_data = chunk[['date', f'{col}_num']].dropna()

                for date, group in col_data.groupby('date'):
                    if date not in daily_data:
                        daily_data[date] = DailyStats(date)

                    min_val = group[f'{col}_num'].min()
                    max_val = group[f'{col}_num'].max()
                    daily_data[date].update(col, min_val)
                    daily_data[date].update(col, max_val)

        logger.info(f"  Processed {filepath.name}: {len(daily_data)} days (type: {detected_type or 'unknown'})")
        return daily_data

    except Exception as e:
        logger.error(f"  Error in {filepath.name}: {e}")
        return {}


def merge_daily_stats(all_stats: List[Dict[str, DailyStats]]) -> Dict[str, DailyStats]:
    """Merge stats from multiple files."""
    merged: Dict[str, DailyStats] = {}

    for file_stats in all_stats:
        for date, daily_stat in file_stats.items():
            if date not in merged:
                merged[date] = DailyStats(date)

            for col in daily_stat.get_columns():
                min_v = daily_stat.stats[col]['min']
                max_v = daily_stat.stats[col]['max']
                if not pd.isna(min_v):
                    merged[date].update(col, min_v)
                if not pd.isna(max_v):
                    merged[date].update(col, max_v)

    return merged


def get_all_columns(daily_stats: Dict[str, DailyStats]) -> Set[str]:
    """Get union of all columns found across all dates."""
    all_cols = set()
    for ds in daily_stats.values():
        all_cols.update(ds.get_columns())
    return all_cols


def write_stats(sensor_id: str, daily_stats: Dict[str, DailyStats], output_path: Path):
    """Write daily stats to CSV. Only includes columns based on sensor type."""
    if not daily_stats:
        logger.warning(f"  No data for {sensor_id}")
        # Write empty file with just Date column
        pd.DataFrame(columns=['Date']).to_csv(output_path, index=False)
        return

    records = [daily_stats[d].to_dict() for d in sorted(daily_stats.keys()) if daily_stats[d].has_data()]

    if not records:
        logger.warning(f"  No valid records for {sensor_id}")
        pd.DataFrame(columns=['Date']).to_csv(output_path, index=False)
        return

    df = pd.DataFrame(records)

    # Get all columns that were actually found
    all_columns = get_all_columns(daily_stats)

    # Determine column order based on sensor type priority
    column_order = ['Date']
    priority_order = ['temperature', 'humidity', 'pressure', 'P1', 'P2']

    for col in priority_order:
        if col in all_columns:
            column_order.extend([f'max_{col}', f'min_{col}'])

    # Reorder dataframe
    df = df[column_order]

    df.to_csv(output_path, index=False, float_format='%.2f')
    logger.info(f"  Written: {output_path.name} ({len(df)} days, columns: {list(all_columns)})")


def discover_files() -> Dict[str, List[Path]]:
    """Find all FULL_*.csv files organized by sensor_id."""
    sensor_files = {}

    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        return sensor_files

    for station_dir in DATA_DIR.iterdir():
        if not station_dir.is_dir():
            continue

        merged_dir = station_dir / "merged"
        if not merged_dir.exists():
            continue

        for sensor_dir in merged_dir.iterdir():
            if not sensor_dir.is_dir():
                continue

            sensor_id = sensor_dir.name
            full_files = list(sensor_dir.glob("FULL_*.csv"))

            if full_files:
                if sensor_id not in sensor_files:
                    sensor_files[sensor_id] = []
                sensor_files[sensor_id].extend(full_files)
                logger.debug(f"Found {len(full_files)} FULL files for {sensor_id}")

    return sensor_files