"""Unit tests for Geoapify geocoding module."""
from unittest.mock import MagicMock, patch

import pytest
import requests
from backend.app.services import geo


@pytest.fixture(autouse=True)
def clean_geo_cache():
    geo.clear_cache()
    yield
    geo.clear_cache()


def test_empty_or_none_region_returns_none():
    assert geo.geocode_with_geoapify(None) is None
    assert geo.geocode_with_geoapify("") is None
    assert geo.geocode_with_geoapify("   ") is None
    assert geo.geocode_region(None) is None
    assert geo.geocode_region("") is None


def test_missing_api_key_returns_none_and_not_cached(monkeypatch):
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    monkeypatch.delenv("GEOAPIFY_KEY", raising=False)
    monkeypatch.delenv("GEOAPIFY_TOKEN", raising=False)
    geo._GEO_CACHE.clear()
    assert geo.get_geoapify_api_key() is None
    assert geo.geocode_with_geoapify("Raj Nagar, Ghaziabad") is None
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE



def test_api_key_from_env_variants(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "key_1")
    assert geo.get_geoapify_api_key() == "key_1"

    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    monkeypatch.setenv("GEOAPIFY_KEY", "key_2")
    assert geo.get_geoapify_api_key() == "key_2"

    monkeypatch.delenv("GEOAPIFY_KEY", raising=False)
    monkeypatch.setenv("GEOAPIFY_TOKEN", "key_3")
    assert geo.get_geoapify_api_key() == "key_3"


def test_parse_geoapify_json_results_format():
    data = {
        "results": [
            {"lat": 28.6926, "lon": 77.4383, "formatted": "Raj Nagar, Ghaziabad"}
        ]
    }
    coords = geo._parse_geoapify_response(data)
    assert coords == (28.6926, 77.4383)


def test_parse_geoapify_geojson_features_format():
    data = {
        "features": [
            {
                "type": "Feature",
                "properties": {"lat": 19.1136, "lon": 72.8697},
                "geometry": {"type": "Point", "coordinates": [72.8697, 19.1136]},
            }
        ]
    }
    coords = geo._parse_geoapify_response(data)
    assert coords == (19.1136, 72.8697)


def test_parse_geoapify_geometry_coordinates_fallback():
    data = {
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", "coordinates": [77.0266, 28.4595]},
            }
        ]
    }
    coords = geo._parse_geoapify_response(data)
    assert coords == (28.4595, 77.0266)


def test_parse_geoapify_invalid_bounds():
    # Latitude > 90
    assert geo._parse_geoapify_response({"results": [{"lat": 95.0, "lon": 77.0}]}) is None
    # Latitude < -90
    assert geo._parse_geoapify_response({"results": [{"lat": -95.0, "lon": 77.0}]}) is None
    # Longitude > 180
    assert geo._parse_geoapify_response({"results": [{"lat": 28.0, "lon": 195.0}]}) is None
    # Longitude < -180
    assert geo._parse_geoapify_response({"results": [{"lat": 28.0, "lon": -195.0}]}) is None


def test_parse_geoapify_missing_or_non_numeric_coordinates():
    # Missing lat
    assert geo._parse_geoapify_response({"results": [{"lon": 77.4383}]}) is None
    # Missing lon
    assert geo._parse_geoapify_response({"results": [{"lat": 28.6926}]}) is None
    # Non-numeric lat
    assert geo._parse_geoapify_response({"results": [{"lat": "invalid_lat", "lon": 77.4383}]}) is None
    # Non-numeric lon
    assert geo._parse_geoapify_response({"results": [{"lat": 28.6926, "lon": "invalid_lon"}]}) is None


def test_parse_geoapify_unexpected_structure():
    assert geo._parse_geoapify_response({"results": "not_a_list"}) is None
    assert geo._parse_geoapify_response({"results": [{}]}) is None
    assert geo._parse_geoapify_response({"results": [None]}) is None
    assert geo._parse_geoapify_response({"features": "not_a_list"}) is None
    assert geo._parse_geoapify_response("string_response") is None
    assert geo._parse_geoapify_response(12345) is None
    assert geo._parse_geoapify_response([]) is None


def test_parse_geoapify_empty_results():
    assert geo._parse_geoapify_response({"results": []}) is None
    assert geo._parse_geoapify_response({"features": []}) is None
    assert geo._parse_geoapify_response({}) is None
    assert geo._parse_geoapify_response(None) is None


@patch("requests.get")
def test_successful_geocoding_with_normalized_caching(mock_requests_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{"lat": 28.6926, "lon": 77.4383}]
    }
    mock_requests_get.return_value = mock_resp

    # First call - queries API via requests.get
    coords1 = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords1 == (28.6926, 77.4383)
    assert mock_requests_get.call_count == 1
    assert "raj nagar, ghaziabad" in geo._GEO_CACHE

    # Second call with messy whitespace + case differences - uses normalized cache, no extra HTTP call
    coords2 = geo.geocode_region("   RAJ   nagar,   GHAZIABAD   ", api_key="test_key")
    assert coords2 == (28.6926, 77.4383)
    assert mock_requests_get.call_count == 1


@patch("requests.get")
def test_invalid_json_handled_safely(mock_requests_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_resp

    coords = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords is None
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE


@patch("requests.get")
def test_transient_http_error_not_cached(mock_requests_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_requests_get.return_value = mock_resp

    coords = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords is None
    # Transient HTTP error must NOT be saved in cache
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE


@patch("requests.get", side_effect=requests.Timeout("Request timed out"))
def test_timeout_error_not_cached(mock_requests_get):
    coords = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords is None
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE


@patch("requests.get", side_effect=requests.ConnectionError("Connection refused"))
def test_connection_error_not_cached(mock_requests_get):
    coords = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords is None
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE


@patch("requests.get")
def test_transient_failure_allows_retry(mock_requests_get):
    # Step 1: Initial call times out
    mock_requests_get.side_effect = requests.Timeout("Network hiccup")
    coords1 = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords1 is None
    assert "raj nagar, ghaziabad" not in geo._GEO_CACHE

    # Step 2: Next call succeeds once network recovers
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{"lat": 28.6926, "lon": 77.4383}]
    }
    mock_requests_get.side_effect = None
    mock_requests_get.return_value = mock_resp

    coords2 = geo.geocode_with_geoapify("Raj Nagar, Ghaziabad", api_key="test_key")
    assert coords2 == (28.6926, 77.4383)
    assert "raj nagar, ghaziabad" in geo._GEO_CACHE


@patch("requests.get", side_effect=requests.RequestException("Generic network failure"))
def test_general_request_exception_not_cached(mock_requests_get):
    coords = geo.geocode_with_geoapify("Connaught Place, Delhi", api_key="test_key")
    assert coords is None
    assert "connaught place, delhi" not in geo._GEO_CACHE


def test_boundary_coordinates():
    # Exactly on boundaries
    assert geo._validate_and_format_coords(90.0, 180.0) == (90.0, 180.0)
    assert geo._validate_and_format_coords(-90.0, -180.0) == (-90.0, -180.0)
    assert geo._validate_and_format_coords(0.0, 0.0) == (0.0, 0.0)
    # Just outside boundaries
    assert geo._validate_and_format_coords(90.0001, 50.0) is None
    assert geo._validate_and_format_coords(-90.0001, 50.0) is None
    assert geo._validate_and_format_coords(20.0, 180.0001) is None
    assert geo._validate_and_format_coords(20.0, -180.0001) is None


def test_normalization_helper():
    assert geo._normalize_region_key("  Raj   Nagar,   Ghaziabad  ") == "raj nagar, ghaziabad"
    assert geo._normalize_region_key("\n\tMUMBAI\t ") == "mumbai"
    assert geo._normalize_region_key("Bandra,  Mumbai") == "bandra, mumbai"

