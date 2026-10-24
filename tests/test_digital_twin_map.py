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



def test_gps_walked_boundary_persistence_and_reload(client):
    """
    Tests that a polygon captured via GPS walking (with mapping_method='GPS_WALKING'
    and high precision coordinate stream) persists to the database and reloads on Digital Twin.
    """
    farm_id = "52120432-c948-4026-87c4-7e2c481a7bf5"
    field_id = "e5d69ac6-bfe4-4015-a3cd-7cab06c476a6"

    # Real field walk polygon around parcel perimeter
    walked_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [76.98215, 20.91825],
                [76.98350, 20.91820],
                [76.98380, 20.91940],
                [76.98240, 20.91945],
                [76.98215, 20.91825]
            ]
        ]
    }

    metadata = {
        "mapping_method": "GPS_WALKING",
        "point_count": 5,
        "gps_accuracy_avg_meters": 3.8
    }

    # 1. Save boundary via PUT endpoint
    res = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": field_id,
        "field_name": "Field A (GPS Walked)",
        "area": 3.15,
        "area_unit": "acre",
        "geometry": walked_polygon,
        "metadata": metadata
    })
    assert res.status_code == 200
    save_data = res.json()
    assert save_data["status"] == "updated"
    assert save_data["boundaries_mapped"] is True

    # 2. Reload via Digital Twin endpoint
    dt_res = client.get(f"/api/v1/digital-twin/{farm_id}")
    assert dt_res.status_code == 200
    dt_data = dt_res.json()
    assert dt_data["boundaries_mapped"] is True

    # Locate the saved field
    target_field = next((f for f in dt_data["fields"] if f["id"] == field_id), None)
    assert target_field is not None
    assert target_field["boundaries_mapped"] is True
    assert target_field["geojson_geometry"] is not None
    assert target_field["geojson_geometry"]["type"] == "Polygon"
    assert len(target_field["geojson_geometry"]["coordinates"][0]) == 5

    # Confirm coordinates order is [lon, lat]
    p1 = target_field["geojson_geometry"]["coordinates"][0][0]
    assert 76.0 <= p1[0] <= 78.0  # longitude
    assert 20.0 <= p1[1] <= 22.0  # latitude


def test_multiple_parcels_boundary_integrity(client):
    """
    Tests that multiple field parcels on the same farm maintain their own independent boundaries
    without overwriting each other.
    """
    farm_id = "52120432-c948-4026-87c4-7e2c481a7bf5"
    field_a = "e5d69ac6-bfe4-4015-a3cd-7cab06c476a6"
    field_b = "571f6eac-de30-41d2-a2c3-0355937b9d58"

    # Parcel B boundary
    poly_b = {
        "type": "Polygon",
        "coordinates": [
            [
                [76.9840, 20.9180],
                [76.9860, 20.9180],
                [76.9860, 20.9195],
                [76.9840, 20.9195],
                [76.9840, 20.9180]
            ]
        ]
    }

    res_b = client.put(f"/api/v1/farms/{farm_id}/boundaries", json={
        "field_id": field_b,
        "field_name": "Field B (South Parcel)",
        "area": 2.1,
        "area_unit": "acre",
        "geometry": poly_b,
        "metadata": {"mapping_method": "GPS_WALKING"}
    })
    assert res_b.status_code == 200

    # Verify both fields now exist on Digital Twin simultaneously
    dt_res = client.get(f"/api/v1/digital-twin/{farm_id}")
    assert dt_res.status_code == 200
    fields_list = dt_res.json()["fields"]

    f_a = next((f for f in fields_list if f["id"] == field_a), None)
    f_b = next((f for f in fields_list if f["id"] == field_b), None)

    assert f_a is not None and f_a["boundaries_mapped"] is True
    assert f_b is not None and f_b["boundaries_mapped"] is True
    assert f_a["id"] != f_b["id"]
