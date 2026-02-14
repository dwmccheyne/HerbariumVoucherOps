import requests
import json
import os
import argparse

PROJECT_ID = 263745
PROJECT_API_URL = "https://api.inaturalist.org/v1/observations"
OBS_CACHE_FILE = "inaturalist_observations.json"
FIELD_NAME = "Herbarium Catalog Number"
UWAL_M = "UWAL-M"
UWAL_L = "UWAL-L"

INAT_API_TOKEN = os.environ.get("INAT_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {INAT_API_TOKEN}"} if INAT_API_TOKEN else {}

def load_observations():
    with open(OBS_CACHE_FILE, "r") as f:
        return json.load(f)

def get_project_observation_ids():
    obs_ids = set()
    po_map = {}  # observation_id -> project_observation_id
    page = 1
    while True:
        params = {"per_page": 200, "page": page, "project_id": PROJECT_ID}
        response = requests.get(PROJECT_API_URL, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            break
        for obs in results:
            obs_id = obs["id"]
            obs_ids.add(obs_id)
            # Find project_observation_id (fix: project is an object)
            for po in obs.get("project_observations", []):
                if po.get("project", {}).get("id") == PROJECT_ID:
                    po_map[obs_id] = po.get("id")
        if len(results) < 200:
            break
        page += 1
    return obs_ids, po_map

def add_observation_to_project(obs_id, dry_run):
    if dry_run:
        print(f"Would add observation {obs_id} to project {PROJECT_ID}")
        return
    url = f"https://api.inaturalist.org/v1/projects/{PROJECT_ID}/add_observation"
    response = requests.post(url, json={"observation_id": obs_id}, headers=HEADERS)
    if response.status_code == 200:
        print(f"Added observation {obs_id} to project {PROJECT_ID}")
    else:
        print(f"Failed to add observation {obs_id}: {response.text}")

def remove_observation_from_project(obs_id, dry_run):
    if dry_run:
        print(f"Would remove observation {obs_id} from project {PROJECT_ID}")
        return
    # Need project_observation_id
    global project_observation_map
    po_id = project_observation_map.get(obs_id)
    if not po_id:
        print(f"Could not find project_observation_id for observation {obs_id}")
        return
    url = f"https://api.inaturalist.org/v1/project_observations/{po_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        print(f"Removed observation {obs_id} (project_observation_id {po_id}) from project {PROJECT_ID}")
    else:
        print(f"Failed to remove observation {obs_id} (project_observation_id {po_id}): {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Check and update project membership for UWAL-M/L observations.")
    parser.add_argument('--dry-run', action='store_true', help='Show changes without making them')
    args = parser.parse_args()
    dry_run = args.dry_run

    observations = load_observations()
    project_obs_ids, po_map = get_project_observation_ids()
    global project_observation_map
    project_observation_map = po_map
    obs_ids_to_add = set()
    obs_ids_to_remove = set()

    for obs in observations:
        obs_id = obs["id"]
        field_val = None
        for field in obs.get("observation_field_values", []):
            if field.get("name") == FIELD_NAME:
                field_val = str(field.get("value", ""))
                break
        if field_val:
            if UWAL_M in field_val:
                if obs_id not in project_obs_ids:
                    obs_ids_to_add.add(obs_id)
            if UWAL_L in field_val:
                if obs_id in project_obs_ids:
                    obs_ids_to_remove.add(obs_id)

    if obs_ids_to_add:
        print(f"{len(obs_ids_to_add)} observations would be added to the project:")
        for obs_id in obs_ids_to_add:
            obs = next((o for o in observations if o["id"] == obs_id), None)
            field_val = None
            if obs:
                for field in obs.get("ofvs", []):
                    if field.get("name") == FIELD_NAME:
                        field_val = str(field.get("value", ""))
                        break
            print(f"{obs_id}: '{field_val}'")
    else:
        print("0 observations would be added to the project.")
    for obs_id in obs_ids_to_add:
        add_observation_to_project(obs_id, dry_run)
    for obs_id in obs_ids_to_remove:
        remove_observation_from_project(obs_id, dry_run)

    # Validate project membership
    project_obs_ids, po_map = get_project_observation_ids()
    project_observation_map = po_map
    invalid_ids = []
    for obs_id in project_obs_ids:
        obs = next((o for o in observations if o["id"] == obs_id), None)
        field_val = None
        if obs:
            for field in obs.get("ofvs", []):
                if field.get("name") == FIELD_NAME:
                    field_val = str(field.get("value", ""))
                    break
        if not field_val or UWAL_M not in field_val:
            invalid_ids.append(obs_id)
    if invalid_ids:
        print(f"Project contains {len(invalid_ids)} observations without UWAL-M.")
        print("Invalid observation IDs and their Herbarium Catalog Number values:")
        for obs_id in invalid_ids:
            obs = next((o for o in observations if o["id"] == obs_id), None)
            field_val = None
            if obs:
                for field in obs.get("ofvs", []):
                    if field.get("name") == FIELD_NAME:
                        field_val = str(field.get("value", ""))
                        break
            print(f"{obs_id}: '{field_val}'")
            remove_observation_from_project(obs_id, dry_run)
    else:
        print("All project observations have UWAL-M.")

if __name__ == "__main__":
    main()
