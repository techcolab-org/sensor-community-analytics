from pathlib import Path
from datetime import datetime, timedelta
import requests
from typing import Optional, List, Dict
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GetSensorData:

    def __init__(self, output_dir='sensor_data', max_workers=10):
        self.base_url = 'https://archive.sensor.community/'
        self.api_url = 'https://data.sensor.community/airrohr/v1/sensor/'
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Enhanced session with connection pooling and retry logic
        self.session = self._create_session()

        # Thread-local storage for thread-safe operations
        self._local = threading.local()

        # Concurrent download settings
        self.max_workers = max_workers  # Number of parallel downloads

        # Default date range
        self.start_date = '2025-08-15'
        self.end_date = datetime.today().strftime('%Y-%m-%d')

        # Sensor metadata
        self.sensor_metadata = {
            'sensor_id': '',
            'sensor_type': '',
            'location': '',
            'lat': '0.0',
            'lon': '0.0'
        }

    def _create_session(self):
        """Create a session with connection pooling and retry strategy."""
        session = requests.Session()

        # Retry strategy for failed requests
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )

        # HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,  # Number of connection pools
            pool_maxsize=20,  # Max connections per pool
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({'User-Agent': 'Sensolog/1.0'})

        return session

    def _get_thread_session(self):
        """Get or create a session for the current thread."""
        if not hasattr(self._local, 'session'):
            self._local.session = self._create_session()
        return self._local.session

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
            filename = f"{date_str}_{sensor_type}_sensor_{self.sensor_metadata['sensor_id']}.csv"
            file_path = month_folder / filename

            if file_path.exists():
                return file_path

            print(f" Creating placeholder file: {filename}")

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

            df.to_csv(file_path, sep=';', index=False)
            print(f"Placeholder file created")

            return file_path

        except Exception as e:
            print(f"   Error creating placeholder file: {e}")
            return None

    def _download_single_date(self, date_info: Dict) -> Dict:
        """
        Download files for a single date (used in parallel processing).

        Args:
            date_info: Dictionary containing date, sensor_id, sensor_type, month_folder, etc.

        Returns:
            Dictionary with download results
        """
        date_str = date_info['date_str']
        sensor_id = date_info['sensor_id']
        sensor_type = date_info['sensor_type']
        month_folder = date_info['month_folder']
        create_missing = date_info['create_missing']

        # Use thread-local session for thread safety
        session = self._get_thread_session()

        result = {
            'date': date_str,
            'files': [],
            'created_placeholder': False
        }

        files = self._get_files_for_date_concurrent(sensor_id, date_str, sensor_type, session)

        if not files:
            if create_missing and sensor_type:
                placeholder_file = self._create_placeholder_file(
                    date_str, sensor_type, month_folder
                )
                if placeholder_file:
                    result['files'].append(str(placeholder_file))
                    result['created_placeholder'] = True
        else:
            for file_url in files:
                file_path = self._download_file_concurrent(file_url, month_folder, session)
                if file_path:
                    result['files'].append(str(file_path))

        return result

    def _get_files_for_date_concurrent(self, sensor_id: str, date: str,
                                       sensor_type: Optional[str], session) -> List[str]:
        """
        Get list of files available for a specific date (thread-safe version).

        Args:
            sensor_id: Sensor ID
            date: Date string in format 'YYYY-MM-DD'
            sensor_type: Optional sensor type filter
            session: Requests session to use

        Returns:
            List of file URLs
        """
        date_url = f"{self.base_url}{date}/"
        files = []

        if sensor_type:
            file_url = f"{date_url}{date}_{sensor_type}_sensor_{sensor_id}.csv"
            if self._check_file_exists_concurrent(file_url, session):
                files.append(file_url)
        else:
            # Try common sensor types in parallel
            common_types = ['sds011', 'dht22', 'bmp180']

            # Check all types quickly with HEAD requests
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_type = {
                    executor.submit(
                        self._check_file_exists_concurrent,
                        f"{date_url}{date}_{s_type}_sensor_{sensor_id}.csv",
                        session
                    ): s_type for s_type in common_types
                }

                for future in as_completed(future_to_type):
                    s_type = future_to_type[future]
                    if future.result():
                        file_url = f"{date_url}{date}_{s_type}_sensor_{sensor_id}.csv"
                        files.append(file_url)

        return files

    def _check_file_exists_concurrent(self, url: str, session) -> bool:
        """
        Check if a file exists at the given URL (thread-safe version).

        Args:
            url: URL to check
            session: Requests session to use

        Returns:
            True if file exists, False otherwise
        """
        try:
            response = session.head(url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _download_file_concurrent(self, url: str, output_folder: Path, session) -> Optional[Path]:
        """
        Download a file from URL to the output folder (thread-safe version).

        Args:
            url: URL of the file to download
            output_folder: Folder to save the file
            session: Requests session to use

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            filename = url.split('/')[-1]
            file_path = output_folder / filename

            # Skip if already downloaded
            if file_path.exists():
                return file_path

            response = session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Write file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return file_path

        except requests.RequestException:
            return None

    def download_from_date(self, sensor_id: str, sensor_type: Optional[str] = None,
                           list_only: bool = False, merge: bool = True,
                           create_missing: bool = True,
                           auto_fetch_metadata: bool = True,
                           merge_by_year: bool = False) -> Dict[str, List[str]]:
        """
        Download CSV files from a specific date range, organized by month (OPTIMIZED VERSION).

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
            self.sensor_metadata = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type or 'unknown',
                'location': f'Sensor_{sensor_id}',
                'lat': '0.0',
                'lon': '0.0'
            }

        sensor_folder = Path(self.output_dir, sensor_id)
        sensor_folder.mkdir(exist_ok=True, parents=True)

        # Dictionary to track files by month
        monthly_files = {}

        # Parse date range
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')

        # Build list of all dates to process
        dates_to_process = []
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            month_str = current_date.strftime('%Y-%m')
            month_folder = sensor_folder / month_str
            month_folder.mkdir(exist_ok=True, parents=True)

            if month_str not in monthly_files:
                monthly_files[month_str] = []

            dates_to_process.append({
                'date_str': date_str,
                'month_str': month_str,
                'month_folder': month_folder,
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'create_missing': create_missing
            })

            current_date += timedelta(days=1)

        # Download files in parallel
        print(f"\n{'=' * 70}")
        print(f"DOWNLOADING DATA FOR SENSOR: {sensor_id}")
        print(f"{'=' * 70}")
        print(f"Date range: {self.start_date} to {self.end_date}")
        print(f"Total days: {len(dates_to_process)}")
        print(f"Parallel workers: {self.max_workers}")
        print(f"{'=' * 70}\n")

        if not list_only:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all download tasks
                future_to_date = {
                    executor.submit(self._download_single_date, date_info): date_info
                    for date_info in dates_to_process
                }

                # Process completed downloads
                completed = 0
                for future in as_completed(future_to_date):
                    date_info = future_to_date[future]
                    result = future.result()

                    month_str = date_info['month_str']
                    monthly_files[month_str].extend(result['files'])

                    completed += 1
                    if completed % 10 == 0 or completed == len(dates_to_process):
                        print(f"Progress: {completed}/{len(dates_to_process)} days processed")

        # Print summary
        total_files = sum(len(files) for files in monthly_files.values())
        print(f"\n{'=' * 70}")
        print(f"Total files downloaded: {total_files}")
        for month, files in monthly_files.items():
            print(f"  {month}: {len(files)} files")
        print(f"{'=' * 70}\n")

        # Merge files for each month if requested
        if merge and not list_only and total_files > 0:
            print("Merging monthly files...")
            for month, files in monthly_files.items():
                if files:
                    self._merge_csv_files(sensor_folder / month, sensor_id, sensor_type)

        # Merge by year if requested
        if merge_by_year and not list_only and total_files > 0:
            print("Merging yearly files...")
            self.merge_months_by_year(sensor_folder, sensor_id, sensor_type)

        return monthly_files

    def _get_files_for_date(self, sensor_id: str, date: str,
                            sensor_type: Optional[str] = None) -> List[str]:
        """Legacy method for compatibility."""
        return self._get_files_for_date_concurrent(sensor_id, date, sensor_type, self.session)

    def _check_file_exists(self, url: str) -> bool:
        """Legacy method for compatibility."""
        return self._check_file_exists_concurrent(url, self.session)

    def _download_file(self, url: str, output_folder: Path) -> Optional[Path]:
        """Legacy method for compatibility."""
        return self._download_file_concurrent(url, output_folder, self.session)

    def _merge_csv_files(self, month_folder: Path, sensor_id: str,
                         sensor_type: Optional[str] = None):
        """
        Merge all CSV files in a month folder into a single CSV file using pandas.
        OPTIMIZED: Uses chunked reading for large files.
        """
        try:
            if sensor_type:
                csv_files = sorted([f for f in month_folder.glob(f'*_{sensor_type}_sensor_{sensor_id}.csv')
                                    if not (f.name.startswith('merged_') or f.name.startswith('FULL_'))])
            else:
                csv_files = sorted([f for f in month_folder.glob('*.csv')
                                    if not (f.name.startswith('merged_') or f.name.startswith('FULL_'))])

            if not csv_files:
                print(f"⚠️  No CSV files found in {month_folder.name}")
                return

            sensor_folder = month_folder.parent
            station_folder = sensor_folder.parent
            merged_base_folder = station_folder / 'merged' / sensor_id
            merged_base_folder.mkdir(parents=True, exist_ok=True)

            month_name = month_folder.name
            year, month_num = month_name.split('-')
            merged_filename = f"{year}_{month_num}_{sensor_id}.csv"
            merged_path = merged_base_folder / merged_filename

            if merged_path.exists():
                print(f"✓ Merged file already exists: {merged_filename}")
                return

            print(f"\n📦 Merging {len(csv_files)} files in {month_folder.name}...")

            # Read all files - using list comprehension is faster
            dataframes = []
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file, sep=';', low_memory=False)
                    dataframes.append(df)
                except Exception as e:
                    print(f"  ✗ Error reading {csv_file.name}: {e}")

            if not dataframes:
                print(f"⚠️  No valid CSV files to merge in {month_folder.name}")
                return

            # Concatenate all at once - faster than incremental
            merged_df = pd.concat(dataframes, ignore_index=True)

            # Sort and deduplicate
            if 'timestamp' in merged_df.columns:
                merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

            initial_rows = len(merged_df)
            merged_df = merged_df.drop_duplicates()
            final_rows = len(merged_df)

            if initial_rows != final_rows:
                print(f"  ℹ️  Removed {initial_rows - final_rows:,} duplicate rows")

            # Save
            merged_df.to_csv(merged_path, sep=';', index=False)
            print(f"\n✅ MONTHLY MERGED FILE CREATED!")
            print(f"  📄 {merged_filename}")
            print(f"  📊 {len(merged_df):,} total rows")
            print(f"  📁 {merged_path}")

        except Exception as e:
            print(f"❌ Error merging CSV files in {month_folder.name}: {e}")

    def merge_months_by_year(self, sensor_folder: Path, sensor_id: str,
                             sensor_type: Optional[str] = None):
        """
        Merge all month merged files from the same year into a single yearly file.
        OPTIMIZED: Better memory management for large datasets.
        """
        try:
            station_folder = sensor_folder.parent
            merged_base_folder = station_folder / 'merged' / sensor_id
            merged_base_folder.mkdir(parents=True, exist_ok=True)

            monthly_merged_files = sorted([
                f for f in merged_base_folder.glob(f'*_{sensor_id}.csv')
                if not f.name.startswith('FULL_')
            ])

            if not monthly_merged_files:
                print("⚠️  No monthly merged files found to merge by year")
                return

            # Group by year
            years_dict = {}
            for merged_file in monthly_merged_files:
                parts = merged_file.stem.split('_')
                if len(parts) >= 3:
                    year = parts[0]
                    if year not in years_dict:
                        years_dict[year] = []
                    years_dict[year].append(merged_file)

            if not years_dict:
                print("⚠️  No valid monthly files found to merge by year")
                return

            # Merge each year
            for year, year_files in years_dict.items():
                print(f"\n📅 Merging year {year}...")
                print(f"  Found {len(year_files)} months")

                yearly_filename = f"FULL_{year}_{sensor_id}.csv"
                yearly_path = merged_base_folder / yearly_filename

                if yearly_path.exists():
                    print(f"  ✓ Yearly file already exists: {yearly_filename}")
                    continue

                print(f"\n📦 Merging {len(year_files)} monthly files for year {year}...")

                # Read all monthly files
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

                # Concatenate
                merged_df = pd.concat(dataframes, ignore_index=True)

                # Sort and deduplicate
                if 'timestamp' in merged_df.columns:
                    merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

                initial_rows = len(merged_df)
                merged_df = merged_df.drop_duplicates()
                final_rows = len(merged_df)

                if initial_rows != final_rows:
                    print(f"  ℹ️  Removed {initial_rows - final_rows:,} duplicate rows")

                # Save
                merged_df.to_csv(yearly_path, sep=';', index=False)
                print(f"\n✅ YEARLY MERGED FILE CREATED!")
                print(f"  📄 {yearly_filename}")
                print(f"  📊 {len(merged_df):,} total rows")
                print(f"  📁 {yearly_path}")

        except Exception as e:
            print(f"❌ Error merging by year: {e}")

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
            print(f"\nSENSOR {i}/{len(sensor_ids)}: {sensor_id}")
            self.download_from_date(sensor_id, sensor_type, list_only, merge,
                                    create_missing, auto_fetch_metadata, merge_by_year)


# Example usage
if __name__ == "__main__":
    # Example with optimized parallel downloads
    downloader = GetSensorData(output_dir='sensor_data', max_workers=20)

    # Set date range
    downloader.set_date_range('2024-01-01', '2024-12-31')

    # Download with parallel processing
    result = downloader.download_from_date(
        sensor_id='95522',
        sensor_type='sds011',
        merge=True,
        create_missing=True,
        auto_fetch_metadata=True,
        merge_by_year=True
    )