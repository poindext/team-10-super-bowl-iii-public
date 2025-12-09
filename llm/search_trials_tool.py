import os
import requests
from requests.auth import HTTPBasicAuth


def _get_auth():
    """
    Get authentication credentials from environment variables.
    Supports multiple authentication methods:
    1. Basic Auth: IRIS_USERNAME and IRIS_PASSWORD
    2. Bearer Token: IRIS_BEARER_TOKEN
    3. API Key Header: IRIS_API_KEY (uses X-API-Key header)

    Returns:
        requests.auth.HTTPBasicAuth, dict with headers, or None
    """
    # Method 1: Basic Authentication
    username = os.getenv("IRIS_USERNAME")
    password = os.getenv("IRIS_PASSWORD")
    if username and password:
        return HTTPBasicAuth(username, password)

    # Method 2: Bearer Token
    bearer_token = os.getenv("IRIS_BEARER_TOKEN")
    if bearer_token:
        return {"Authorization": f"Bearer {bearer_token}"}

    # Method 3: API Key in custom header
    api_key = os.getenv("IRIS_API_KEY")
    if api_key:
        return {"X-API-Key": api_key}

    # No authentication configured
    return None


def search_trials_tool(queryText: str, maxRows: int = None):
    """
    Implementation of the search_trials tool; calls the IRIS VectorTrialSearch
    REST API.

    Args:
        queryText: Natural language description of what to search for
            (conditions, goals, other context).
        maxRows: Maximum number of trials to return (optional).

    Returns:
        JSON response from the REST service containing matching clinical
        trials.

    Raises:
        requests.HTTPError: If the request fails (e.g., authentication error,
            server error).
        ValueError: If authentication is required but not configured.
    """
    url = (
        "http://ec2-98-82-129-136.compute-1.amazonaws.com"
        "/i4h/ctgov/VectorTrialSearch"
    )

    payload = {
        "queryText": queryText
    }

    # Only include maxRows if it's provided
    if maxRows is not None:
        payload["maxRows"] = maxRows

    # Get authentication
    auth = _get_auth()
    headers = {}

    if auth is None:
        # If no auth is configured, you might want to raise an error
        # or proceed without auth. Uncomment the next line if auth is
        # mandatory:
        # raise ValueError(
        #     "Authentication required. Set IRIS_USERNAME/IRIS_PASSWORD, "
        #     "IRIS_BEARER_TOKEN, or IRIS_API_KEY environment variables."
        # )
        pass
    elif isinstance(auth, dict):
        # Bearer token or API key (headers)
        headers.update(auth)
        auth = None  # Don't pass to requests as auth parameter
    # else: auth is HTTPBasicAuth, pass it directly to requests

    resp = requests.post(
        url, json=payload, auth=auth, headers=headers, timeout=30
    )
    resp.raise_for_status()
    return resp.json()  # this is the JSON your REST service returns
