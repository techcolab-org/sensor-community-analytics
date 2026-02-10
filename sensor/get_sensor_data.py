from pathlib import Path
from datetime import datetime, timedelta
import requests
from typing import Optional, List, Dict
import pandas as pd


class GetSensorData:

    def __init__(self, output_dir='sensor_data'):
        self.base_url = 'https://archive.sensor.community/'
        self.api_url = 'https://data.sensor.community/airrohr/v1/sensor/'
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Sensolog/1.0'})

        # Default date range - CHANGE THESE or use set_date_range()
        self.start_date = '2025-08-15'
        self.end_date = datetime.today().strftime('%Y-%m-%d')

        # Sensor metadata - automatically fetched or manually set
        self.sensor_metadata = {
            'sensor_id': '',
            'sensor_type': '',
            'location': '',
            'lat': '0.0',
            'lon': '0.0'
        }

    def fetch_sensor_metadata(self, sensor_id: str, sensor_type: str = 'sds011') -> bool:
        """
        Automatically fetch sensor metadata (location, lat, lon) from sensor.community API.

        Args:
            sensor_id: Sensor ID
            sensor_type: Sensor type (default: 'sds011')

        Returns:
            True if metadata was successfully fetched, False otherwise
        """
        try:
            # print(f"\n Fetching metadata for sensor {sensor_id}...")
            url = f"{self.api_url}{sensor_id}/"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data or len(data) == 0:
                print(f" No data returned from API for sensor {sensor_id}")
                return False

            # Get location info from the first data point
            location_data = data[0].get('location', {})

            # Extract metadata
            location_id = location_data.get('id', 0)
            latitude = location_data.get('latitude', '0.0')
            longitude = location_data.get('longitude', '0.0')
            location_name = location_data.get('location', f'Location_{location_id}')

            # Try to get country/city info if available
            country = location_data.get('country', '')
            city = location_data.get('city', '')
            if country and city:
                location_name = f"{city}, {country}"
            elif country:
                location_name = country

            # Update metadata
            self.sensor_metadata = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'location': location_name,
                'lat': str(latitude),
                'lon': str(longitude)
            }

            print(f" Metadata fetched successfully!")
            print(f" Location: {location_name}")
            print(f" Coordinates: {latitude}, {longitude}")

            return True

        except requests.RequestException as e:
            print(f"Error fetching metadata: {e}")
            print(f"   Using default values instead")
            self.sensor_metadata = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'location': f'Sensor_{sensor_id}',
                'lat': '0.0',
                'lon': '0.0'
            }
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def set_sensor_metadata(self, sensor_id: str, sensor_type: str,
                            location: str = '', lat: str = '0.0', lon: str = '0.0'):
        """
        Manually set metadata for the sensor (alternative to automatic fetching).

        Args:
            sensor_id: Sensor ID
            sensor_type: Sensor type (e.g., 'sds011', 'dht22')
            location: Location description
            lat: Latitude as string
            lon: Longitude as string
        """
        self.sensor_metadata = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'location': location,
            'lat': lat,
            'lon': lon
        }
        print(f"📍 Sensor metadata set manually for: {sensor_id} ({sensor_type})")

    def _create_placeholder_file(self, date_str: str, sensor_type: str,
                                 month_folder: Path) -> Optional[Path]:
        """
        Create a placeholder CSV file with header and zero data when file is not found.

        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            sensor_type: Sensor type
            month_folder: Folder to save the file

        Returns:
            Path to created file or None if failed
        """
        try:
            # Create filename following the sensor.community pattern
            filename = f"{date_str}_{sensor_type}_sensor_{self.sensor_metadata['sensor_id']}.csv"
            file_path = month_folder / filename

            # Skip if file already exists
            if file_path.exists():
                return file_path

            print(f" Creating placeholder file: {filename}")

            # Create DataFrame with the required structure
            df = pd.DataFrame({
                'sensor_id': [self.sensor_metadata['sensor_id']],
                'sensor_type': [sensor_type],
                'location': [self.sensor_metadata['location']],
                'lat': [self.sensor_metadata['lat']],
                'lon': [self.sensor_metadata['lon']],
                'timestamp': [date_str + ' 00:00:00'],
                'P1': [0.0],
                'durP1': [0.0],
                'ratioP1': [0.0],
                'P2': [0.0],
                'durP2': [0.0],
                'ratioP2': [0.0]
            })

            # Save with semicolon separator (sensor.community format)
            df.to_csv(file_path, sep=';', index=False)
            print(f"Placeholder file created")

            return file_path

        except Exception as e:
            print(f"   Error creating placeholder file: {e}")
            return None

    def download_from_date(self, sensor_id: str, sensor_type: Optional[str] = None,
                           list_only: bool = False, merge: bool = True,
                           create_missing: bool = True,
                           auto_fetch_metadata: bool = True,
                           merge_by_year: bool = False) -> Dict[str, List[str]]:
        """
        Download CSV files from a specific date range, organized by month.

        Args:
            sensor_id: Sensor id to download from the website
            sensor_type: Optional sensor type filter (e.g., 'sds011', 'dht22')
            list_only: If True, only list files without downloading
            merge: If True, merge all CSV files in each month folder into one file
            create_missing: If True, create placeholder files when data is not found
            auto_fetch_metadata: If True, automatically fetch location data from API
            merge_by_year: If True, merge all months in the same year into a single file

        Returns:
            Dictionary with month as key and list of downloaded files as value
        """
        # Automatically fetch metadata if enabled
        if auto_fetch_metadata and sensor_type:
            self.fetch_sensor_metadata(sensor_id, sensor_type)
        elif not self.sensor_metadata['sensor_id']:
            # Set basic metadata if not fetched
            self.sensor_metadata = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type or 'unknown',
                'location': f'Sensor_{sensor_id}',
                'lat': '0.0',
                'lon': '0.0'
            }

        sensor_folder = Path(self.output_dir, sensor_id)
        sensor_folder.mkdir(exist_ok=True, parents=True)

        # print(f"\n{'=' * 70}")
        # print(f"DOWNLOADING DATA FOR SENSOR: {sensor_id}")
        # print(f"{'=' * 70}")
        # print(f"Date range: {self.start_date} to {self.end_date}")
        # print(f"Sensor type: {sensor_type if sensor_type else 'ALL (trying common types)'}")
        # print(f"Output folder: {sensor_folder}")
        # print(f"Create missing files: {create_missing}")
        # print(f"Merge by year: {merge_by_year}")
        # print(f"{'=' * 70}\n")

        # Dictionary to track files by month: {month_folder: [files]}
        monthly_files = {}

        # Parse date range
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')

        # Iterate through each date in the range
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')

            # Create month folder (format: YYYY-MM)
            month_str = current_date.strftime('%Y-%m')
            month_folder = sensor_folder / month_str
            month_folder.mkdir(exist_ok=True, parents=True)

            if month_str not in monthly_files:
                monthly_files[month_str] = []

            files = self._get_files_for_date(sensor_id, date_str, sensor_type)

            if not files:
                print(f"No files found for {date_str}")

                # Create placeholder file if requested and not in list_only mode
                if create_missing and not list_only and sensor_type:
                    placeholder_file = self._create_placeholder_file(
                        date_str, sensor_type, month_folder
                    )
                    if placeholder_file:
                        monthly_files[month_str].append(str(placeholder_file))

            for file_url in files:
                if list_only:
                    print(f"   📄 Found: {file_url}")
                    monthly_files[month_str].append(file_url)
                else:
                    file_path = self._download_file(file_url, month_folder)
                    if file_path:
                        monthly_files[month_str].append(str(file_path))

            current_date += timedelta(days=1)

        # Print summary
        total_files = sum(len(files) for files in monthly_files.values())
        print(f"Total files: {total_files}")
        for month, files in monthly_files.items():
            print(f"  {month}: {len(files)} files")

        # Merge files for each month if requested
        if merge and not list_only and total_files > 0:
            for month, files in monthly_files.items():
                if files:
                    self._merge_csv_files(sensor_folder / month, sensor_id, sensor_type)

        # Merge by year if requested
        if merge_by_year and not list_only and total_files > 0:
            self.merge_months_by_year(sensor_folder, sensor_id, sensor_type)

        return monthly_files

    def _get_files_for_date(self, sensor_id: str, date: str,
                            sensor_type: Optional[str] = None) -> List[str]:
        """
        Get list of files available for a specific date and sensor.

        Args:
            sensor_id: Sensor ID
            date: Date string in format 'YYYY-MM-DD'
            sensor_type: Optional sensor type filter

        Returns:
            List of file URLs
        """
        # Format: https://archive.sensor.community/YYYY-MM-DD/
        date_url = f"{self.base_url}{date}/"

        files = []

        # Try different sensor type patterns if specified
        if sensor_type:
            # Format: YYYY-MM-DD_sensor_type_sensor_SENSOR_ID.csv
            file_url = f"{date_url}{date}_{sensor_type}_sensor_{sensor_id}.csv"
            print(f"   🔍 Trying: {file_url}")
            if self._check_file_exists(file_url):
                files.append(file_url)
                print(f"Found!")
            else:
                print(f"Not found")
        else:
            # Try common sensor types
            common_types = ['sds011', 'dht22', 'bmp180']

            for s_type in common_types:
                file_url = f"{date_url}{date}_{s_type}_sensor_{sensor_id}.csv"
                if self._check_file_exists(file_url):
                    files.append(file_url)
                    print(f"Found {s_type} data")

        return files

    def _check_file_exists(self, url: str) -> bool:
        """
        Check if a file exists at the given URL.

        Args:
            url: URL to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _download_file(self, url: str, output_folder: Path) -> Optional[Path]:
        """
        Download a file from URL to the output folder.

        Args:
            url: URL of the file to download
            output_folder: Folder to save the file

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            filename = url.split('/')[-1]
            file_path = output_folder / filename

            # Skip if already downloaded
            if file_path.exists():
                print(f"Already exists: {file_path.name}")
                return file_path

            print(f" Downloading: {filename}...", end=" ")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Track total bytes downloaded
            total_bytes = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_bytes += len(chunk)

            size_kb = total_bytes / 1024
            print(f"Done ({size_kb:.1f} KB)")
            return file_path

        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def _merge_csv_files(self, month_folder: Path, sensor_id: str,
                         sensor_type: Optional[str] = None):
        """
        Merge all CSV files in a month folder into a single CSV file using pandas.
        Merged file is saved in {station_folder}/merged/{sensor_id}/ directory.
        Filename format: {year}_{month_num}_{sensor_id}.csv

        Args:
            month_folder: Path to the folder containing CSV files
            sensor_id: Sensor ID
            sensor_type: Optional sensor type for naming the merged file
        """
        try:
            # Get all CSV files in the folder (exclude already merged files)
            # IMPORTANT: Only merge files of the same sensor type
            if sensor_type:
                # Filter by sensor type pattern
                csv_files = sorted([f for f in month_folder.glob(f'*_{sensor_type}_sensor_{sensor_id}.csv')
                                    if not (f.name.startswith('merged_') or f.name.startswith('FULL_'))])
            else:
                csv_files = sorted([f for f in month_folder.glob('*.csv')
                                    if not (f.name.startswith('merged_') or f.name.startswith('FULL_'))])

            if not csv_files:
                print(f"⚠️  No CSV files found in {month_folder.name}")
                return

            # Create merged directory structure at station level: {station_folder}/merged/{sensor_id}/
            sensor_folder = month_folder.parent  # Get sensor folder (parent of month folder)
            station_folder = sensor_folder.parent  # Get station folder (parent of sensor folder)
            merged_base_folder = station_folder / 'merged' / sensor_id
            merged_base_folder.mkdir(parents=True, exist_ok=True)

            # Create merged filename with new format: {year}_{month_num}_{sensor_id}.csv
            month_name = month_folder.name  # Format: YYYY-MM
            year, month_num = month_name.split('-')
            merged_filename = f"{year}_{month_num}_{sensor_id}.csv"

            merged_path = merged_base_folder / merged_filename

            if merged_path.exists():
                print(f"✓ Merged file already exists: {merged_filename}")
                return

            print(f"\n📦 Merging {len(csv_files)} files in {month_folder.name}...")

            # Read and concatenate all CSV files
            dataframes = []
            for csv_file in csv_files:
                try:
                    # Read with pandas using semicolon separator
                    df = pd.read_csv(csv_file, sep=';', low_memory=False)
                    dataframes.append(df)
                    print(f"  ✓ {csv_file.name}: {len(df):,} rows, {len(df.columns)} columns")
                except Exception as e:
                    print(f"  ✗ Error reading {csv_file.name}: {e}")

            if not dataframes:
                print(f"⚠️  No valid CSV files to merge in {month_folder.name}")
                return

            # Concatenate all dataframes with pandas
            # ignore_index=True creates a new sequential index
            merged_df = pd.concat(dataframes, ignore_index=True)

            # Sort by timestamp if available
            if 'timestamp' in merged_df.columns:
                merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

            # Remove duplicates if any
            initial_rows = len(merged_df)
            merged_df = merged_df.drop_duplicates()
            final_rows = len(merged_df)

            if initial_rows != final_rows:
                print(f"  ℹ️  Removed {initial_rows - final_rows:,} duplicate rows")

            # Save merged file
            merged_df.to_csv(merged_path, sep=';', index=False)
            print(f"\n✅ MONTHLY MERGED FILE CREATED!")
            print(f"  📄 {merged_filename}")
            print(f"  📊 {len(merged_df):,} total rows")
            print(f"  📁 {merged_path}")

        except Exception as e:
            print(f"❌ Error merging CSV files in {month_folder.name}: {e}")
            import traceback
            traceback.print_exc()

    def merge_months_by_year(self, sensor_folder: Path, sensor_id: str,
                             sensor_type: Optional[str] = None):
        """
        Merge all month merged files from the same year into a single yearly file.
        Yearly file is saved in {station_folder}/merged/{sensor_id}/ directory.
        Filename format: FULL_{year}_{sensor_id}.csv

        Args:
            sensor_folder: Path to the sensor folder containing month folders
            sensor_id: Sensor ID
            sensor_type: Optional sensor type for naming the merged file
        """
        try:
            # Create merged directory structure at station level: {station_folder}/merged/{sensor_id}/
            station_folder = sensor_folder.parent  # Get station folder (parent of sensor folder)
            merged_base_folder = station_folder / 'merged' / sensor_id
            merged_base_folder.mkdir(parents=True, exist_ok=True)

            # Look for monthly merged files with new naming pattern: {year}_{month_num}_{sensor_id}.csv
            # Pattern matches files like: 2024_01_12345.csv, 2024_02_12345.csv, etc.
            monthly_merged_files = sorted([
                f for f in merged_base_folder.glob(f'*_{sensor_id}.csv')
                if not f.name.startswith('FULL_')  # Exclude yearly files
            ])

            if not monthly_merged_files:
                print("⚠️  No monthly merged files found to merge by year")
                return

            # Group monthly files by year
            years_dict = {}
            for merged_file in monthly_merged_files:
                # Extract year from filename: {year}_{month_num}_{sensor_id}.csv
                parts = merged_file.stem.split('_')

                if len(parts) >= 3:
                    year = parts[0]  # First part is the year
                    if year not in years_dict:
                        years_dict[year] = []
                    years_dict[year].append(merged_file)

            if not years_dict:
                print("⚠️  No valid monthly files found to merge by year")
                return

            # Merge each year separately
            for year, year_files in years_dict.items():
                print(f"\n📅 Merging year {year}...")
                print(f"  Found {len(year_files)} months")

                # Create yearly merged filename with new format: FULL_{year}_{sensor_id}.csv
                yearly_filename = f"FULL_{year}_{sensor_id}.csv"

                yearly_path = merged_base_folder / yearly_filename

                # Skip if yearly file already exists
                if yearly_path.exists():
                    print(f"  ✓ Yearly file already exists: {yearly_filename}")
                    continue

                print(f"\n📦 Merging {len(year_files)} monthly files for year {year}...")

                # Read and concatenate all monthly merged files
                dataframes = []
                for csv_file in sorted(year_files):
                    try:
                        df = pd.read_csv(csv_file, sep=';', low_memory=False)
                        dataframes.append(df)
                        print(f"  ✓ {csv_file.name}: {len(df):,} rows")
                    except Exception as e:
                        print(f"  ✗ Error reading {csv_file.name}: {e}")

                if not dataframes:
                    print(f"⚠️  No valid CSV files to merge for year {year}")
                    continue

                # Concatenate all dataframes
                merged_df = pd.concat(dataframes, ignore_index=True)

                # Sort by timestamp if available
                if 'timestamp' in merged_df.columns:
                    merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

                # Remove duplicates if any
                initial_rows = len(merged_df)
                merged_df = merged_df.drop_duplicates()
                final_rows = len(merged_df)

                if initial_rows != final_rows:
                    print(f"  ℹ️  Removed {initial_rows - final_rows:,} duplicate rows")

                # Save yearly merged file
                merged_df.to_csv(yearly_path, sep=';', index=False)
                print(f"\n✅ YEARLY MERGED FILE CREATED!")
                print(f"  📄 {yearly_filename}")
                print(f"  📊 {len(merged_df):,} total rows")
                print(f"  📁 {yearly_path}")

        except Exception as e:
            print(f"❌ Error merging by year: {e}")
            import traceback
            traceback.print_exc()

    def set_date_range(self, start_date: str, end_date: str):
        """
        Set the date range for downloads.

        Args:
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
        """
        self.start_date = start_date
        self.end_date = end_date
        print(f"📅 Date range set: {start_date} to {end_date}")

    def download_multiple_sensors(self, sensor_ids: List[str],
                                  sensor_type: Optional[str] = None,
                                  list_only: bool = False,
                                  merge: bool = True,
                                  create_missing: bool = True,
                                  auto_fetch_metadata: bool = True,
                                  merge_by_year: bool = False):
        """
        Download data for multiple sensors.

        Args:
            sensor_ids: List of sensor IDs
            sensor_type: Optional sensor type filter
            list_only: If True, only list files without downloading
            merge: If True, merge CSV files by month
            create_missing: If True, create placeholder files when data is not found
            auto_fetch_metadata: If True, automatically fetch location data from API
            merge_by_year: If True, merge all months in the same year into a single file
        """
        for i, sensor_id in enumerate(sensor_ids, 1):
            print(f"SENSOR {i}/{len(sensor_ids)}: {sensor_id}")
            self.download_from_date(sensor_id, sensor_type, list_only, merge,
                                    create_missing, auto_fetch_metadata, merge_by_year)


# Example usage
if __name__ == "__main__":
    # Example 1: Download with yearly merging

    downloader = GetSensorData(output_dir='sensor_data')

    # Set date range (multiple months across a year)
    # downloader.set_date_range('2024-01-01', '2024-12-31')

    # Download with merge_by_year=True
    result = downloader.download_from_date(
        sensor_id='95522',
        sensor_type='sds011',
        merge=True,  # Merge monthly files
        create_missing=True,
        auto_fetch_metadata=True,
        merge_by_year=True  # NEW: Merge all months into yearly file
    )
