"""Geocoding lookup engine powered exclusively by Geoapify.

Converts region and location strings into latitude and longitude coordinates
via the Geoapify Geocoding API.
"""
import logging
import os
from typing import Optional, Tuple

from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

# Dynamic runtime in-memory cache to avoid duplicate API requests during execution.
# Populated solely from successful Geoapify responses.
_GEO_CACHE: dict[str, Optional[Tuple[float, float]]] = {}


def get_geoapify_api_key() -> Optional[str]:
    """Retrieve Geoapify API key from environment variables."""
    return (
        os.getenv("GEOAPIFY_API_KEY")
        or os.getenv("GEOAPIFY_KEY")
        or os.getenv("GEOAPIFY_TOKEN")
        or None
    )


GEOAPIFY_API_KEY = get_geoapify_api_key()


def clear_cache() -> None:
    """Clear the dynamic in-memory geocoding cache."""
    _GEO_CACHE.clear()


def _normalize_region_key(region: str) -> str:
    """Normalize region text for cache lookups (lowercase + collapsed whitespace)."""
    return " ".join(str(region).strip().lower().split())


def _validate_and_format_coords(lat: any, lon: any) -> Optional[Tuple[float, float]]:
    """Validate latitude and longitude values within valid geographic boundaries."""
    if lat is None or lon is None:
        return None
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        return None

    if not (-90.0 <= lat_f <= 90.0):
        return None
    if not (-180.0 <= lon_f <= 180.0):
        return None

    return (lat_f, lon_f)


def _parse_geoapify_response(data: dict) -> Optional[Tuple[float, float]]:
    """Extract and validate (latitude, longitude) from Geoapify API response.

    Supports both JSON results format and GeoJSON FeatureCollection format.
    """
    if not isinstance(data, dict):
        return None

    # 1. Format: json (data["results"] list)
    results = data.get("results")
    if isinstance(results, list) and len(results) > 0:
        first = results[0]
        if isinstance(first, dict):
            lat = first.get("lat")
            lon = first.get("lon") if first.get("lon") is not None else first.get("lng")
            coords = _validate_and_format_coords(lat, lon)
            if coords:
                return coords

    # 2. Format: geojson (data["features"] list)
    features = data.get("features")
    if isinstance(features, list) and len(features) > 0:
        first = features[0]
        if isinstance(first, dict):
            # Check properties
            props = first.get("properties")
            if isinstance(props, dict):
                lat = props.get("lat")
                lon = props.get("lon") if props.get("lon") is not None else props.get("lng")
                coords = _validate_and_format_coords(lat, lon)
                if coords:
                    return coords

            # Check geometry coordinates [lon, lat]
            geometry = first.get("geometry")
            if isinstance(geometry, dict):
                raw_coords = geometry.get("coordinates")
                if isinstance(raw_coords, (list, tuple)) and len(raw_coords) >= 2:
                    coords = _validate_and_format_coords(raw_coords[1], raw_coords[0])
                    if coords:
                        return coords

    return None


def geocode_with_geoapify(
    region: Optional[str], api_key: Optional[str] = None
) -> Optional[Tuple[float, float]]:
    """Convert region/location string into (latitude, longitude) using Geoapify exclusively.

    Args:
        region: Address, city, state, or region name.
        api_key: Optional API key override. Defaults to GEOAPIFY_API_KEY from environment.

    Returns:
        (latitude, longitude) tuple as floats, or None if lookup fails, input is invalid,
        or no key is configured.
    """
    if not region or not str(region).strip():
        return None

    region_str = str(region).strip()
    cache_key = _normalize_region_key(region_str)

    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    key = api_key if api_key is not None else get_geoapify_api_key()
    if not key:
        logger.warning(
            "GEOAPIFY_API_KEY is not set. Cannot geocode region %r via Geoapify.",
            region_str,
        )
        # Do not cache missing API key so it can recover when key is provided
        return None

    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": region_str,
        "format": "json",
        "limit": 1,
        "apiKey": key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            coords = _parse_geoapify_response(data)
            # Cache genuine Geoapify result (coords or None if place has no valid geocode)
            _GEO_CACHE[cache_key] = coords
            return coords
        elif response.status_code in (401, 403):
            logger.error(
                "Geoapify authentication failed (HTTP %d). Please verify your GEOAPIFY_API_KEY.",
                response.status_code,
            )
            # Transient auth/HTTP error - do not cache
            return None
        else:
            logger.warning(
                "Geoapify Geocoding API returned HTTP %d for query %r: %s",
                response.status_code,
                region_str,
                response.text,
            )
            # Transient HTTP error - do not cache
            return None
    except requests.Timeout:
        logger.warning("Timeout while connecting to Geoapify API for region %r", region_str)
        return None
    except requests.ConnectionError as exc:
        logger.warning("Connection error calling Geoapify API for region %r: %s", region_str, exc)
        return None
    except requests.RequestException as exc:
        logger.warning("Request error calling Geoapify API for region %r: %s", region_str, exc)
        return None
    except (ValueError, TypeError, Exception) as exc:
        logger.warning("Unexpected error during Geoapify geocoding for region %r: %s", region_str, exc)
        return None


def geocode_region(
    region: Optional[str], api_key: Optional[str] = None
) -> Optional[Tuple[float, float]]:
    """Convert region string to coordinates. Backward-compatible wrapper for geocode_with_geoapify."""
    return geocode_with_geoapify(region, api_key=api_key)
