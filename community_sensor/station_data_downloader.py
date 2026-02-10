"""
OPTIMIZED Utility module for downloading sensor data organized by station.
Includes performance improvements like parallel downloads and better memory management.

Usage example:
    from your_app.utils.station_data_downloader_optimized import StationDataDownloader

    # Download with 20 parallel workers for faster downloads
    downloader = StationDataDownloader(station_id=1, max_workers=20)
    downloader.download_all_sensors(
        start_date='2024-01-01',
        end_date='2024-12-31',
        merge=True,
        merge_by_year=True
    )
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union, Any
import logging

from django.core.exceptions import ObjectDoesNotExist
from sensor.models import Station, Sensor
from sensor.get_sensor_data import GetSensorData  # Use optimized version

logger = logging.getLogger(__name__)


class StationDataDownloader:
    """
    Download sensor data for all sensors in a station, organized by station folder.
    OPTIMIZED VERSION with parallel downloads.
    """

    # Map Django sensor type names to sensor.community format
    SENSOR_TYPE_MAP = {
        'sds011': 'sds011',
        'dht22': 'dht22',
        'bmp180': 'bmp180',
        'bme280': 'bme280',
        'hpm': 'hpm',
        'pms3003': 'pms3003',
        'pms5003': 'pms5003',
        'pms7003': 'pms7003',
    }

    def __init__(self, station_id: Optional[int] = None,
                 station_uid: Optional[str] = None,
                 output_base_dir: str = 'sensor_data_by_station',
                 max_workers: int = 15):  # NEW: Configurable workers
        """
        Initialize the downloader for a specific station.

        Args:
            station_id: Database ID of the station
            station_uid: UUID of the station (alternative to station_id)
            output_base_dir: Base directory for all downloads
            max_workers: Number of parallel workers for downloads (default: 15)
        """
        self.station = self._get_station(station_id, station_uid)
        self.output_base_dir = Path(output_base_dir)
        self.station_dir = self._create_station_directory()
        self.max_workers = max_workers

        # Initialize the OPTIMIZED sensor data downloader
        self.downloader = GetSensorData(
            output_dir=str(self.station_dir),
            max_workers=max_workers
        )

        logger.info(f"Initialized OPTIMIZED downloader for station: {self.station.name}")
        logger.info(f"Output directory: {self.station_dir}")
        logger.info(f"Parallel workers: {max_workers}")

    def _get_station(self, station_id: Optional[int],
                     station_uid: Optional[str]) -> Station:
        """Get station from database."""
        try:
            if station_id:
                return Station.objects.get(id=station_id)
            elif station_uid:
                return Station.objects.get(uid=station_uid)
            else:
                raise ValueError("Either station_id or station_uid must be provided")
        except ObjectDoesNotExist:
            raise ValueError(f"Station not found with the provided identifier")

    def _create_station_directory(self) -> Path:
        """
        Create station-specific directory.
        Format: output_base_dir/StationName_StationUID/
        """
        station_dir_name = (
            self.station.name.lower()
            .replace('-', '_')
            .replace('(', '_')
            .replace(')', '_')
            .replace(',', '_')
            .replace(' ', '_')
            .strip()
        )
        station_dir_name = f"{station_dir_name}_{self.station.uid}"
        station_dir = self.output_base_dir / station_dir_name
        station_dir.mkdir(parents=True, exist_ok=True)
        return station_dir

    def _get_sensor_type(self, sensor_type_name: str) -> Optional[str]:
        """
        Map Django sensor type name to sensor.community format.

        Args:
            sensor_type_name: Name from SensorType model

        Returns:
            Mapped sensor type name or None if not recognized
        """
        sensor_type_name_lower = sensor_type_name.lower()

        for key, value in self.SENSOR_TYPE_MAP.items():
            if key in sensor_type_name_lower:
                return value

        logger.warning(f"Unknown sensor type: {sensor_type_name}")
        return None

    def download_all_sensors(self,
                             start_date: str = '2024-01-01',
                             end_date: Optional[str] = None,
                             sensor_ids: Optional[List[int]] = None,
                             merge: bool = True,
                             create_missing: bool = True,
                             merge_by_year: bool = False) -> Dict[str, Any]:
        """
        Download data for all sensors in the station or specific sensors if sensor_ids provided.
        OPTIMIZED: Uses parallel downloads for faster performance.

        Args:
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD' (defaults to today)
            sensor_ids: Optional list of specific sensor IDs to download. If None, downloads all.
            merge: If True, merge monthly CSV files
            create_missing: If True, create placeholder files for missing data
            merge_by_year: If True, merge all months into yearly files

        Returns:
            Dictionary with sensor IDs as keys and download results as values
        """
        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d')

        # Set date range
        self.downloader.set_date_range(start_date, end_date)

        # Get sensors for this station
        sensors_query = Sensor.objects.filter(
            station=self.station
        ).select_related('sensor_type')

        # Filter by specific sensor IDs if provided
        if sensor_ids is not None and len(sensor_ids) > 0:
            sensors_query = sensors_query.filter(sensor_id__in=sensor_ids)
            logger.info(f"Filtering to {len(sensor_ids)} specific sensor(s): {sensor_ids}")

        sensors = sensors_query

        if not sensors.exists():
            msg = f"No sensors found for station: {self.station.name}"
            if sensor_ids:
                msg += f" with sensor IDs: {sensor_ids}"
            logger.warning(msg)
            return {}

        logger.info(f"Found {sensors.count()} sensors for station {self.station.name}")

        results = {}

        for idx, sensor in enumerate(sensors, 1):
            sensor_id = sensor.sensor_id
            sensor_type = self._get_sensor_type(sensor.sensor_type.name)

            # Skip if no sensor_id or unknown sensor type
            if not sensor_id:
                logger.warning(f"Skipping {sensor} - No sensor_id set")
                continue

            if not sensor_type:
                logger.warning(
                    f"Skipping {sensor} - Unknown sensor type: {sensor.sensor_type.name}"
                )
                continue

            logger.info(f"[{idx}/{sensors.count()}] Processing: {sensor}")
            logger.info(f"  Sensor ID: {sensor_id}, Type: {sensor_type}")

            try:
                # Set metadata from station if available
                if self.station.location:
                    self.downloader.set_sensor_metadata(
                        sensor_id=str(sensor_id),
                        sensor_type=sensor_type,
                        location=self.station.location_name or self.station.name,
                        lat=str(self.station.location.y),  # latitude
                        lon=str(self.station.location.x)  # longitude
                    )
                    auto_fetch = False
                else:
                    auto_fetch = True

                # Download the data with parallel processing
                result = self.downloader.download_from_date(
                    sensor_id=str(sensor_id),
                    sensor_type=sensor_type,
                    merge=merge,
                    create_missing=create_missing,
                    auto_fetch_metadata=auto_fetch,
                    merge_by_year=merge_by_year
                )

                results[str(sensor_id)] = {
                    'sensor': sensor,
                    'files': result,
                    'success': True,
                    'total_files': sum(len(files) for files in result.values())
                }

                logger.info(
                    f"  ✓ Downloaded {results[str(sensor_id)]['total_files']} "
                    f"files for sensor {sensor_id}"
                )

            except Exception as e:
                logger.error(f"  ✗ Error downloading data for sensor {sensor_id}: {e}")
                results[str(sensor_id)] = {
                    'sensor': sensor,
                    'success': False,
                    'error': str(e)
                }

        return results

    def download_specific_sensor(self,
                                 sensor_id: int,
                                 start_date: str = '2024-01-01',
                                 end_date: Optional[str] = None,
                                 merge: bool = True,
                                 create_missing: bool = True,
                                 merge_by_year: bool = False) -> Dict[str, Any]:
        """
        Download data for a specific sensor in the station.
        OPTIMIZED: Uses parallel downloads.

        Args:
            sensor_id: Database sensor_id (from sensor.community)
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            merge: If True, merge monthly CSV files
            create_missing: If True, create placeholder files
            merge_by_year: If True, merge into yearly files

        Returns:
            Dictionary with download results
        """
        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d')

        try:
            sensor = Sensor.objects.get(
                station=self.station,
                sensor_id=sensor_id
            )
        except Sensor.DoesNotExist:
            raise ValueError(
                f"Sensor {sensor_id} not found for station {self.station.name}"
            )

        sensor_type = self._get_sensor_type(sensor.sensor_type.name)

        if not sensor_type:
            raise ValueError(f"Unknown sensor type: {sensor.sensor_type.name}")

        # Reinitialize downloader with optimized settings
        self.downloader = GetSensorData(
            output_dir=str(self.station_dir),
            max_workers=self.max_workers
        )

        # Set date range
        self.downloader.set_date_range(start_date, end_date)

        # Set metadata
        if self.station.location:
            self.downloader.set_sensor_metadata(
                sensor_id=str(sensor_id),
                sensor_type=sensor_type,
                location=self.station.location_name or self.station.name,
                lat=str(self.station.location.y),
                lon=str(self.station.location.x)
            )
            auto_fetch = False
        else:
            auto_fetch = True

        logger.info(f"Downloading sensor {sensor_id} to: {self.station_dir}/{sensor_id}/")

        # Download with parallel processing
        result = self.downloader.download_from_date(
            sensor_id=str(sensor_id),
            sensor_type=sensor_type,
            merge=merge,
            create_missing=create_missing,
            auto_fetch_metadata=auto_fetch,
            merge_by_year=merge_by_year
        )

        return {
            'sensor': sensor,
            'files': result,
            'success': True,
            'total_files': sum(len(files) for files in result.values()),
            'output_path': str(self.station_dir / str(sensor_id))
        }

    def get_download_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the station and its sensors.

        Returns:
            Dictionary with station info and sensor list
        """
        sensors = Sensor.objects.filter(
            station=self.station
        ).select_related('sensor_type')

        return {
            'station_name': self.station.name,
            'station_uid': str(self.station.uid),
            'output_directory': str(self.station_dir),
            'max_workers': self.max_workers,
            'coordinates': {
                'lat': self.station.location.y if self.station.location else None,
                'lon': self.station.location.x if self.station.location else None,
            },
            'total_sensors': sensors.count(),
            'sensors': [
                {
                    'id': s.sensor_id,
                    'type': s.sensor_type.name,
                    'description': s.description
                }
                for s in sensors
            ]
        }


# Convenience function for quick downloads (single station)
def download_station_data(station_id: Optional[int] = None,
                          station_uid: Optional[str] = None,
                          start_date: str = '2024-01-01',
                          end_date: Optional[str] = None,
                          sensor_ids: Optional[List[int]] = None,
                          merge: bool = True,
                          merge_by_year: bool = False,
                          output_dir: str = 'sensor_data_by_station',
                          max_workers: int = 15) -> Dict[str, Any]:
    """
    Quick function to download all sensor data for a single station.
    OPTIMIZED VERSION with configurable parallel workers.

    Args:
        station_id: Database ID of the station
        station_uid: UUID of the station (alternative to station_id)
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD' (defaults to today)
        sensor_ids: Optional list of specific sensor IDs to download. If None, downloads all.
        merge: If True, merge monthly CSV files
        merge_by_year: If True, merge all months into yearly files
        output_dir: Base directory for all downloads
        max_workers: Number of parallel workers (default: 15, increase for faster downloads)

    Returns:
        Dictionary with download results

    Example:
        # Fast download with 30 parallel workers
        results = download_station_data(
            station_id=1,
            start_date='2024-01-01',
            end_date='2024-12-31',
            max_workers=30,  # Faster!
            merge=True,
            merge_by_year=True
        )
    """
    downloader = StationDataDownloader(
        station_id=station_id,
        station_uid=station_uid,
        output_base_dir=output_dir,
        max_workers=max_workers
    )

    return downloader.download_all_sensors(
        start_date=start_date,
        end_date=end_date,
        sensor_ids=sensor_ids,
        merge=merge,
        merge_by_year=merge_by_year
    )


def download_multiple_stations_data(
        station_ids: Optional[Union[int, List[int]]] = None,
        start_date: str = '2024-01-01',
        end_date: Optional[str] = None,
        sensor_ids: Optional[List[int]] = None,
        merge: bool = True,
        merge_by_year: bool = False,
        output_dir: str = 'sensor_data_by_station',
        max_workers: int = 15
) -> Dict[str, Any]:
    """
    Download sensor data for single or multiple stations.
    OPTIMIZED VERSION with parallel downloads.

    Args:
        station_ids: Single station ID or list of station database IDs
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD' (defaults to today)
        sensor_ids: Optional list of specific sensor IDs to download. If None, downloads all.
        merge: If True, merge monthly CSV files
        merge_by_year: If True, merge all months into yearly files
        output_dir: Base directory for all downloads
        max_workers: Number of parallel workers per station (default: 15)

    Returns:
        Dictionary with station identifiers as keys and download results as values

    Example:
        # Ultra-fast download with 30 workers
        results = download_multiple_stations_data(
            station_ids=[1, 2, 3],
            start_date='2024-01-01',
            end_date='2024-12-31',
            max_workers=30,  # Much faster!
            merge=True,
            merge_by_year=True
        )
    """
    if not station_ids:
        raise ValueError("station_ids must be provided")

    # Convert single values to lists
    if station_ids is not None and not isinstance(station_ids, list):
        station_ids = [station_ids]

    all_results = {}

    # Process station IDs
    if station_ids:
        logger.info(f"Processing {len(station_ids)} station(s) by ID")
        logger.info(f"Using {max_workers} parallel workers per station")
        if sensor_ids:
            logger.info(f"Filtering to specific sensor IDs: {sensor_ids}")

        for idx, station_id in enumerate(station_ids, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Station {idx}/{len(station_ids)}: ID={station_id}")
            logger.info(f"{'=' * 60}")

            try:
                downloader = StationDataDownloader(
                    station_id=station_id,
                    output_base_dir=output_dir,
                    max_workers=max_workers
                )

                results = downloader.download_all_sensors(
                    start_date=start_date,
                    end_date=end_date,
                    sensor_ids=sensor_ids,
                    merge=merge,
                    merge_by_year=merge_by_year
                )

                all_results[f"station_{station_id}"] = {
                    'station_id': station_id,
                    'station_name': downloader.station.name,
                    'station_uid': str(downloader.station.uid),
                    'output_directory': str(downloader.station_dir),
                    'sensor_results': results,
                    'success': True,
                    'total_sensors_processed': len(results),
                    'successful_sensors': sum(
                        1 for r in results.values() if r.get('success', False)
                    ),
                    'failed_sensors': sum(
                        1 for r in results.values() if not r.get('success', False)
                    )
                }

                logger.info(
                    f"✓ Completed station {station_id} ({downloader.station.name}): "
                    f"{len(results)} sensors processed"
                )

            except Exception as e:
                logger.error(f"✗ Error processing station {station_id}: {e}")
                all_results[f"station_{station_id}"] = {
                    'station_id': station_id,
                    'success': False,
                    'error': str(e)
                }

    # Print summary
    logger.info(f"\n{'=' * 60}")
    logger.info("DOWNLOAD SUMMARY")
    logger.info(f"{'=' * 60}")
    successful = sum(1 for r in all_results.values() if r.get('success', False))
    failed = len(all_results) - successful
    total_sensors = sum(
        r.get('total_sensors_processed', 0)
        for r in all_results.values()
        if r.get('success', False)
    )
    logger.info(f"Total stations: {len(all_results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total sensors processed: {total_sensors}")
    logger.info(f"Parallel workers used: {max_workers}")
    if sensor_ids:
        logger.info(f"Filtered to sensor IDs: {sensor_ids}")
    logger.info(f"{'=' * 60}\n")

    return all_results