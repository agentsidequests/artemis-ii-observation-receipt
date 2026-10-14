"""Offline replay of sampled Horizons ranges, not flash photometry or navigation."""

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'paper-review/range-geometry'
MOON_RADIUS_KM = 1737.4  # Native observer output, not a new radius measurement.


def utc_calendar(value):
    value = value.strip().removeprefix('A.D. ')
    date = datetime.strptime(value, '%Y-%b-%d %H:%M:%S.%f').replace(tzinfo=timezone.utc)
    return date.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def table(text):
    if text.count('$$SOE') != 1 or text.count('$$EOE') != 1:
        raise ValueError('Incomplete or ambiguous source table')
    body = text.split('$$SOE', 1)[1].split('$$EOE', 1)[0]
    return [[field.strip() for field in row] for row in csv.reader(body.splitlines()) if row]


def finite(values):
    numbers = [float(value) for value in values]
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError('Non-finite source value')
    return numbers


def vectors(text, reverse=False):
    required = ['API SOURCE: NASA/JPL Horizons API', 'Output units    : KM-S',
                'Output type     : GEOMETRIC cartesian states', 'Reference frame : ICRF',
                'JDUT', 'Calendar Date (UT )', 'Geometric state vectors have NO corrections']
    if reverse:
        required += ['Target body name: Moon (301)', 'Center body name: Artemis II (spacecraft) (-1024)']
    else:
        required += ['Target body name: Artemis II (spacecraft) (-1024)', 'Center body name: Moon (301)']
    if not all(item in text for item in required):
        raise ValueError('Wrong vector identity, time, frame or units')
    result = []
    for row in table(text):
        if len(row) != 12 or row[-1] != '':
            raise ValueError('Unexpected vector column inventory')
        values = finite(row[2:11])
        position, velocity = values[:3], values[3:6]
        light_time, distance, rate = values[6:]
        if distance <= MOON_RADIUS_KM or abs(math.hypot(*position) - distance) > 1e-7:
            raise ValueError('Range does not replay Cartesian position')
        if abs(light_time * 299792.458 - distance) > 1e-7:
            raise ValueError('Light-time unit mismatch')
        if abs(sum(p*v for p, v in zip(position, velocity)) / distance - rate) > 1e-10:
            raise ValueError('Range-rate does not replay the state')
        result.append({'utc': utc_calendar(row[1]), 'position': position, 'velocity': velocity,
                       'distance_km': distance, 'range_rate_km_s': rate})
    return result


def observer(text):
    required = ['Target body name: Moon (301)', 'Center body name: Artemis II (spacecraft) (-1024)',
                'Target radii    : 1737.4, 1737.4, 1737.4 km', 'Ang-diam', 'Units: ARCSECONDS',
                'Units: KM and KM/S', 'Times AFTER 1962 are in UTC']
    if not all(item in text for item in required):
        raise ValueError('Wrong observer identity, radius, time or units')
    result = []
    for row in table(text):
        if len(row) != 7 or row[1:3] != ['', ''] or row[-1] != '':
            raise ValueError('Unexpected observer column inventory')
        diameter, distance, rate = finite(row[3:6])
        expected_diameter = 2 * math.asin(MOON_RADIUS_KM / distance) * 180 / math.pi
        if abs(diameter / 3600 - expected_diameter) > 0.00001:
            raise ValueError('Angular size/range consistency failed')
        result.append({'utc': utc_calendar(row[0]), 'apparent_range_km': distance,
                       'angular_diameter_degrees': diameter / 3600, 'range_rate_km_s': rate})
    return result


def reconcile_texts(texts, config):
    object_text = texts['object.txt']
    if not all(value in object_text for value in ['Artemis II / Spacecraft', '-1024',
             'Post-launch Orion II trajectory data from NASA/JSC navigation (concatenated)',
             'Orion_OEM_20260408_0223.V0.1              2026-Apr-06 17:35 2026-Apr-08 04:38']):
        raise ValueError('Unqualified trajectory identity or coverage')
    expected_times = [entry['utc'] for entry in config['times']]
    if len(expected_times) != 8 or len(set(expected_times)) != 8:
        raise ValueError('Unexpected epoch inventory')
    forward = vectors(texts['vectors.txt'])
    reverse = vectors(texts['reverse-vectors.txt'], reverse=True)
    apparent = observer(texts['observer.txt'])
    for parsed in [forward, reverse, apparent]:
        if [row['utc'] for row in parsed] != expected_times:
            raise ValueError('Source time list does not replay the request')
    rows = []
    for metadata, a, b, c in zip(config['times'], forward, reverse, apparent):
        if any(abs(x + y) > 1e-7 for x, y in zip(a['position'] + a['velocity'], b['position'] + b['velocity'])):
            raise ValueError('Reciprocal coordinate check failed')
        if abs(a['distance_km'] - b['distance_km']) > 1e-7:
            raise ValueError('Reciprocal range check failed')
        if abs(a['distance_km'] - c['apparent_range_km']) > 2:
            raise ValueError('Apparent versus geometric range is not within the declared check envelope')
        rows.append({'utc': a['utc'], 'role': metadata['role'], 'geometric_center_range_km': a['distance_km'],
                     'geometric_center_range_miles': a['distance_km'] / 1.609344,
                     'spherical_altitude_km': a['distance_km'] - MOON_RADIUS_KM,
                     'all_spherical_surface_points_range_envelope_km': [a['distance_km'] - MOON_RADIUS_KM, a['distance_km'] + MOON_RADIUS_KM],
                     'apparent_center_range_km': c['apparent_range_km'],
                     'native_angular_diameter_degrees': c['angular_diameter_degrees']})
    clear = [row for row in rows if row['role'] in ['first clear transcript report anchor', 'shared transcript report anchor', 'later clear transcript report anchor', 'last clear transcript report anchor']]
    if len(clear) != 4:
        raise ValueError('Clear-anchor selection changed')
    return {'status': 'SOURCE_RANGE_DISCREPANCY_AT_FOUR_RECORDED_REPORT_EPOCHS',
            'rows': rows, 'clear_report_anchor_count': len(clear),
            'clear_anchor_center_range_km': [min(row['geometric_center_range_km'] for row in clear), max(row['geometric_center_range_km'] for row in clear)],
            'nasa_feature_reported_miles': 46000, 'nasa_feature_conditional_center_range_km': 46000 * 1.609344,
            'largest_all_surface_range_at_clear_anchors_km': max(row['all_spherical_surface_points_range_envelope_km'][1] for row in clear),
            'prior_26_96_and_3_58_disposition': 'historical conditional arithmetic only; retire as an established Artemis flash-observation advantage; do not substitute a new physical visibility or flux claim',
            'limits': {'all_five_events_mapped': False, 'continuous_interval_bound': False, 'exact_flash_locations': False,
                       'photon_emission_times_verified': False, 'navigation_uncertainties_quantified': False,
                       'independent_navigation_solution': False, 'new_received_flux_advantage_established': False,
                       'event_photometry': False, 'calibrated_flux': False, 'source_typo_mechanism_proved': False,
                       'nasa_acceptance': False}}


def replay():
    acquisition = json.loads((OWNER / 'acquisition-receipt.json').read_text(encoding='utf-8'))
    config = json.loads((OWNER / 'horizons-requests.json').read_text(encoding='utf-8'))
    if hashlib.sha256((OWNER / 'horizons-requests.json').read_bytes()).hexdigest() != acquisition['request_contract_sha256']:
        raise ValueError('Frozen request contract changed')
    for source in acquisition['prior_inputs']:
        if hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Prior epoch or source custody changed')
    names = [source['file'] for source in acquisition['files']]
    if len(names) != 4 or set(names) != {'object.txt', 'vectors.txt', 'reverse-vectors.txt', 'observer.txt'}:
        raise ValueError('Unexpected source inventory or path')
    texts = {}
    for source in acquisition['files']:
        if source['http'] != 200 or not 0 < source['bytes'] <= 65536:
            raise ValueError('Unqualified acquisition status or size')
        payload = (OWNER / 'source' / source['file']).read_bytes()
        if len(payload) != source['bytes'] or hashlib.sha256(payload).hexdigest() != source['sha256']:
            raise ValueError('Preserved source-byte identity changed')
        texts[source['file']] = payload.decode('utf-8')
    result = reconcile_texts(texts, config)
    result['provenance'] = {'acquisition': acquisition, 'request_contract': config,
                            'source_folder': 'paper-review/range-geometry/source',
                            'offline_replay_command': 'python -B -m src.fcorona_range_reconciliation',
                            'scope': 'Local replay checks source bytes and configured geometry; not independent scientific acceptance'}
    return result


if __name__ == '__main__':
    print(json.dumps(replay(), indent=2, allow_nan=False))
