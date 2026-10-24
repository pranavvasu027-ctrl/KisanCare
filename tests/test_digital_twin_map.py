"""Unit and integration tests for Digital Twin geospatial mapping endpoints and serialization."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.endpoints import _validate_coordinates, _extract_valid_geojson_polygon


@pytest.fixture
def client():
    return TestClient(app)


def test_coordinate_validation_helper():
    # Valid ranges
    lat, lon, valid = _validate_coordinates(20.7002, 77.0082)
    assert valid is True
    assert lat == 20.7002
    assert lon == 77.0082

    # None coordinates
    lat, lon, valid = _validate_coordinates(None, None)
    assert valid is False
    assert lat is None

    # Out of range coordinates
    lat, lon, valid = _validate_coordinates(95.0, 77.0)
    assert valid is False

    lat, lon, valid = _validate_coordinates(20.0, -195.0)
    assert valid is False

    # String convertible
    lat, lon, valid = _validate_coordinates("20.7002", "77.0082")
    assert valid is True


def test_geojson_polygon_extraction_helper():
    # Valid GeoJSON Polygon
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [77.005, 20.701],
                [77.009, 20.701],
                [77.009, 20.705],
                [77.005, 20.705],
                [77.005, 20.701]
            ]
        ]
    }
    extracted = _extract_valid_geojson_polygon(valid_polygon)
    assert extracted is not None
    assert extracted["type"] == "Polygon"

    # Arbitrary non-GeoJSON metadata dict (like current soil/terrain properties)
    non_geojson = {
        "terrain": "Mostly flat",
        "drainage": "Good",
        "soil_type": "Black cotton soil",
        "boundaries_mapped": False
    }
    assert _extract_valid_geojson_polygon(non_geojson) is None

    # Malformed Polygon (less than 3 points)
    invalid_polygon = {
        "type": "Polygon",
        "coordinates": [[[77.0, 20.0]]]
    }
    assert _extract_valid_geojson_polygon(invalid_polygon) is None


def test_digital_twin_endpoint_serialization(client):
    # Test verified Pranav Vasu farm endpoint
    res = client.get("/api/v1/digital-twin/52120432-c948-4026-87c4-7e2c481a7bf5")
    assert res.status_code == 200
    data = res.json()
    assert "farm_id" in data
    assert "name" in data
    assert "area_acres" in data
    assert "location" in data
    assert "has_precise_coordinates" in data
    assert "approximate_coordinates" in data
    assert "boundaries_mapped" in data
    assert "fields" in data

    # Verify field serialization
    fields = data["fields"]
    assert len(fields) >= 1
    for f in fields:
        assert "id" in f
        assert "name" in f
        assert "area" in f
        assert "boundaries_mapped" in f
        assert "geojson_geometry" in f
        assert isinstance(f["boundaries_mapped"], bool)


def test_digital_twin_mock_fallback(client):
    res = client.get("/api/v1/digital-twin/FARM-001")
    assert res.status_code == 200
    data = res.json()
    assert data["is_mock"] is True
    assert data["boundaries_mapped"] is False
    assert data["has_precise_coordinates"] is False
    assert data["approximate_coordinates"]["latitude"] == 20.918912
    assert data["approximate_coordinates"]["longitude"] == 76.982846


def test_list_farms_endpoint(client):
    # Unauthenticated / demo listing
    res = client.get("/api/v1/farms")
    assert res.status_code == 200
    data = res.json()
    assert "farms" in data
    assert "count" in data
    assert len(data["farms"]) >= 1
    farm = data["farms"][0]
    assert "id" in farm
    assert "farm_name" in farm
    assert "location" in farm
    assert "total_area" in farm
    assert "area_unit" in farm


def test_farm_creation_with_coordinates(client):
    payload = {
        "farmer_id": "test-farmer-001",
        "farm_name": "Shetkari Test Farm",
        "location": "Takli Bu, Akola, Maharashtra",
        "area": 8.5,
        "latitude": 20.9195,
        "longitude": 76.9832
    }
    res = client.post("/api/v1/farms", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "created"
    assert "farm_id" in data


def test_field_boundary_update_endpoint_validation(client):
    # Test rejection of malformed geometry
    farm_id = "52120432-c948-4026-87c4-7e2c481a7bf5"
    field_id = "e5d69ac6-bfe4-4015-a3cd-7cab06c476a6"

    # 1. Reject invalid geometry format
    res = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": field_id,
        "geometry": {"type": "InvalidType", "coordinates": []}
    })
    assert res.status_code == 422

    # 2. Reject out of range coordinates
    res = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": field_id,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[200.0, 30.0], [200.0, 31.0], [201.0, 31.0], [200.0, 30.0]]]
        }
    })
    assert res.status_code == 422

    # 3. Valid polygon structure saves successfully
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [76.9820, 20.9180],
                [76.9840, 20.9180],
                [76.9840, 20.9200],
                [76.9820, 20.9200],
                [76.9820, 20.9180]
            ]
        ]
    }
    res = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": field_id,
        "field_name": "Field A",
        "area": 3.25,
        "area_unit": "acre",
        "geometry": valid_polygon
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert data["field_id"] == field_id
    assert data["boundaries_mapped"] is True
    assert data["geometry"]["type"] == "Polygon"


def test_field_boundary_unauthorized_cross_farm_access(client):
    # Attempt to update a non-existent field or a field not belonging to farm
    farm_id = "52120432-c948-4026-87c4-7e2c481a7bf5"
    fake_field_id = "00000000-0000-0000-0000-000000000000"

    valid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [76.9820, 20.9180],
                [76.9840, 20.9180],
                [76.9840, 20.9200],
                [76.9820, 20.9200],
                [76.9820, 20.9180]
            ]
        ]
    }
    res = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": fake_field_id,
        "geometry": valid_polygon
    })
    assert res.status_code == 404

