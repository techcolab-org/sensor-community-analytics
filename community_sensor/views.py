"""
Django views for downloading sensor data organized by station.
Add these to your views.py file.
"""
import csv
import os

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import datetime
from django.shortcuts import render
import json

from django.views.generic import View

# Import your models
from sensor.models import Station

# Import the downloader utility
from .station_data_downloader import StationDataDownloader


@login_required
@require_http_methods(["POST"])
def download_station_data(request):
    """
    Handle download data requests from the frontend.
    Supports both single station and multiple station downloads.
    Now also supports downloading only selected sensors.
    """
    try:
        # Get parameters from request
        data = json.loads(request.body)
        station_ids = data.get('station_ids', [])
        sensor_ids = data.get('sensor_ids', None)  # NEW: Get selected sensor IDs
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', datetime.today().strftime('%Y-%m-%d'))
        merge = data.get('merge', True)
        merge_by_year = data.get('merge_by_year', True)

        if not station_ids:
            return JsonResponse({
                'success': False,
                'error': 'No stations selected'
            }, status=400)

        # Results container
        all_results = {}
        successful_stations = 0
        failed_stations = 0
        total_sensors_downloaded = 0
        station_path = os.path.join(settings.BASE_DIR, 'sensor_data_by_station')

        # Download data for each selected station
        for station_id in station_ids:
            try:
                station = Station.objects.get(id=station_id)

                # Initialize downloader
                downloader = StationDataDownloader(station_id=station_id)

                # Download sensors for this station
                # If sensor_ids provided, only download those; otherwise download all
                results = downloader.download_all_sensors(
                    start_date=start_date,
                    end_date=end_date,
                    sensor_ids=sensor_ids,  # NEW: Pass selected sensor IDs
                    merge=merge,
                    merge_by_year=merge_by_year
                )

                # Count successful sensor downloads
                successful_sensors = sum(1 for r in results.values() if r.get('success'))
                total_sensors_downloaded += successful_sensors

                all_results[station.name] = {
                    'success': True,
                    'total_sensors': len(results),
                    'successful_sensors': successful_sensors,
                    'output_path': str(downloader.station_dir),
                    'filtered': sensor_ids is not None and len(sensor_ids) > 0  # NEW: Indicate if filtered
                }

                successful_stations += 1

            except Station.DoesNotExist:
                all_results[f'Station_{station_id}'] = {
                    'success': False,
                    'error': 'Station not found'
                }
                failed_stations += 1

            except Exception as e:
                all_results[f'Station_{station_id}'] = {
                    'success': False,
                    'error': str(e)
                }
                failed_stations += 1

        # Prepare success message
        if sensor_ids and len(sensor_ids) > 0:
            message = f"Downloaded data for {total_sensors_downloaded} selected sensor(s) from {successful_stations} station(s)"
        else:
            message = f"Downloaded data for {total_sensors_downloaded} sensors from {successful_stations} station(s)"

        if failed_stations > 0:
            message += f". {failed_stations} station(s) failed."

        return JsonResponse({
            'success': True,
            'message': message,
            'summary': {
                'total_stations': len(station_ids),
                'successful_stations': successful_stations,
                'failed_stations': failed_stations,
                'total_sensors': total_sensors_downloaded,
                'filtered_download': sensor_ids is not None and len(sensor_ids) > 0  # NEW
            },
            'results': all_results,
            'station_path': os.path.exists(station_path),
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def download_specific_sensor(request):
    """
    Download data for a specific sensor within a station.
    """
    try:
        data = json.loads(request.body)
        station_id = data.get('station_id')
        sensor_id = data.get('sensor_id')
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', datetime.today().strftime('%Y-%m-%d'))
        merge = data.get('merge', True)
        merge_by_year = data.get('merge_by_year', True)

        if not station_id or not sensor_id:
            return JsonResponse({
                'success': False,
                'error': 'Station ID and Sensor ID are required'
            }, status=400)

        # Initialize downloader
        downloader = StationDataDownloader(station_id=station_id)
        station_path = os.path.join(settings.BASE_DIR, 'sensor_data_by_station')

        # Download specific sensor
        result = downloader.download_specific_sensor(
            sensor_id=sensor_id,
            start_date=start_date,
            end_date=end_date,
            merge=merge,
            merge_by_year=merge_by_year
        )

        return JsonResponse({
            'success': True,
            'message': f"Downloaded {result['total_files']} files for sensor {sensor_id}",
            'result': {
                'sensor_id': sensor_id,
                'total_files': result['total_files'],
                'output_path': result['output_path']
            },
            'station_path': os.path.exists(station_path),
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_station_download_info(request, station_id):
    """
    Get information about what will be downloaded for a station.
    Useful for showing a confirmation dialog before downloading.
    """
    try:
        downloader = StationDataDownloader(station_id=station_id)
        summary = downloader.get_download_summary()

        return JsonResponse({
            'success': True,
            'station': summary
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



def get_sensor_data_path():
    """Get absolute path to sensor_data_by_station folder"""
    return os.path.join(settings.BASE_DIR, 'sensor_data_by_station')

def safe_path(user_path):
    """Prevent directory traversal - ensure path stays within base directory"""
    base = os.path.abspath(get_sensor_data_path())
    requested = os.path.abspath(os.path.join(base, user_path))

    if not requested.startswith(base):
        raise ValueError("Invalid path")
    return requested

class StationDataListView(View):
    """List folders and CSV files"""

    def get(self, request):
        path = request.GET.get('path', '')

        try:
            full_path = safe_path(path)

            if not os.path.isdir(full_path):
                return JsonResponse({'error': 'Directory not found'}, status=404)

            items = []
            stats = {'folders': 0, 'files': 0}

            for entry in os.scandir(full_path):
                rel_path = os.path.relpath(entry.path, get_sensor_data_path()).replace('\\', '/')

                item = {
                    'name': entry.name,
                    'path': rel_path,
                    'type': 'folder' if entry.is_dir() else 'file',
                }

                if entry.is_dir():
                    stats['folders'] += 1
                    try:
                        item['item_count'] = len(os.listdir(entry.path))
                    except:
                        item['item_count'] = 0
                else:
                    # Only show CSV files
                    if not entry.name.lower().endswith('.csv'):
                        continue

                    stats['files'] += 1
                    stat = entry.stat()
                    item['size'] = stat.st_size
                    item['modified'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')

                items.append(item)

            # Sort: folders first, then alphabetical
            items.sort(key=lambda x: (0 if x['type'] == 'folder' else 1, x['name'].lower()))

            return JsonResponse({
                'items': items,
                'stats': stats
            })

        except ValueError:
            return JsonResponse({'error': 'Invalid path'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class CsvViewerView(View):
    """Parse CSV and return JSON data for viewing"""

    def get(self, request):
        path = request.GET.get('path', '')

        try:
            full_path = safe_path(path)

            if not os.path.isfile(full_path) or not full_path.endswith('.csv'):
                return JsonResponse({'error': 'CSV file not found'}, status=404)

            rows = []
            headers = []

            with open(full_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                # Detect CSV dialect
                sample = f.read(4096)
                f.seek(0)

                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',\t;')
                except:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                headers = reader.fieldnames or []

                for row in reader:
                    # Clean row data
                    clean_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_row[k.strip()] = v.strip() if v else ''
                    rows.append(clean_row)

                    # Limit for performance
                    if len(rows) >= 100000:
                        break

            return JsonResponse({
                'success': True,
                'headers': headers,
                'rows': rows
            })

        except ValueError:
            return JsonResponse({'error': 'Invalid path'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def station_data_manager(request):
    """Render file manager page"""
    return render(request, 'station_data.html')