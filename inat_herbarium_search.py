import requests
import json
import os
import time
import random


def get_observation_field_id(field_name):
    """Return the hardcoded field ID for Herbarium Catalog Number."""
    # Herbarium Catalog Number field ID is always 1927
    return 1927


def fetch_inaturalist_observations(field_name, cache_file='inaturalist_observations.json'):
    """Fetch all iNaturalist observations with a given field name, cache them locally (incremental write)."""
    api_url = 'https://api.inaturalist.org/v1/observations'
    requests_this_minute = 0
    minute_start = time.time()
    max_requests_per_minute = 50
    max_retries = 5
    obs_count = 0
    with open(cache_file, 'w') as f:
        f.write('[')
        first = True
        id_below = None
        while True:
            params = {
                f'field:{field_name}': '',
                'per_page': 200,
                'verifiable': 'any',
                'order_by': 'id',
                'order': 'desc',
            }
            if id_below is not None:
                params['id_below'] = id_below
            now = time.time()
            if requests_this_minute >= max_requests_per_minute:
                elapsed = now - minute_start
                if elapsed < 60:
                    time.sleep(60 - elapsed)
                minute_start = time.time()
                requests_this_minute = 0
            for attempt in range(max_retries):
                try:
                    response = requests.get(api_url, params=params, timeout=30)
                    requests_this_minute += 1
                    response.raise_for_status()
                    break
                except Exception as exc:
                    print(f"Request failed: {exc} (attempt {attempt + 1})")
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
            else:
                print("Max retries exceeded. Stopping fetch.")
                break
            data = response.json()
            results = data.get('results', [])
            if not results:
                break
            for obs in results:
                if not first:
                    f.write(',\n')
                else:
                    first = False
                json.dump(obs, f)
                f.flush()
                obs_count += 1
            print(f"Fetched {len(results)} observations. Total so far: {obs_count}")
            if len(results) < 200:
                break
            id_below = results[-1]['id']
        f.write(']')
    print(f"Cached {obs_count} observations to {cache_file}")
    return obs_count


def load_cached_observations(cache_file='inaturalist_observations.json'):
    """Load cached observations from a local JSON file."""
    if not os.path.exists(cache_file):
        return []
    with open(cache_file, 'r') as f:
        return json.load(f)


def find_observations_with_substring(observations, field_name, substring):
    """Find observation IDs with a substring in a specific field value."""
    matching_ids = []
    for obs in observations:
        for field in obs.get('observation_field_values', []):
            if field.get('name') == field_name and substring in str(field.get('value', '')):
                matching_ids.append(obs['id'])
                break
    return matching_ids


def main():
    field_name = 'Herbarium Catalog Number'
    substring = 'UWAL-M'
    cache_file = 'inaturalist_observations.json'
    if not os.path.exists(cache_file):
        fetch_inaturalist_observations(field_name, cache_file)
    observations = load_cached_observations(cache_file)
    print(f"Loaded {len(observations)} cached observations.")
    matching_ids = find_observations_with_substring(observations, field_name, substring)
    print(f"Observations with '{substring}' in '{field_name}':")
    for obs_id in matching_ids:
        print(obs_id)


if __name__ == '__main__':
    main()
