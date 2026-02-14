# Herbarium Voucher Ops

This repository automates the daily fetch and project membership validation for iNaturalist herbarium voucher observations.

## Manual Workflow Execution

The workflow is run manually via GitHub Actions and requires an iNaturalist API token as input.

### Steps

1. Get your iNaturalist API token:
   - Visit https://www.inaturalist.org/users/api_token
   - Copy your token.

2. Run the workflow:
   - Go to the Actions tab in your GitHub repository.
   - Select the `Daily Herbarium Operations` workflow.
   - Click "Run workflow".
   - Paste your iNaturalist API token into the `inat_api_token` input field.

## Scripts

- `inat_herbarium_search.py`: Fetches and caches all iNaturalist observations with a Herbarium Catalog Number.
- `project_membership_check.py`: Validates and manages project membership for UWAL-M and UWAL-L observations.

## Requirements

- Python 3.11+
- `requests` package
- iNaturalist API token

## Notes

- The workflow will not run automatically; it must be triggered manually.
- The API token is required for authenticated operations (adding/removing project observations).
