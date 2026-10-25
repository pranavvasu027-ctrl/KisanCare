import pytest
from ml.market_price.agmarknet_client import (
    LiveAgmarknetClient,
    SUPPORTING_PORTALS,
    COMMODITY_ALIASES,
    is_valid_commodity_record,
    get_daily_mandi_snapshot
)
from ml.market_price.predict import MarketPricePredictor


def test_supporting_portals_metadata():
    client = LiveAgmarknetClient()
    portals = client.get_supporting_websites()
    assert len(portals) >= 4
    portal_names = [p["name"] for p in portals]
    assert any("Agmarknet" in name for name in portal_names)
    assert any("Open Government Data" in name for name in portal_names)
    assert any("e-NAM" in name for name in portal_names)
    assert any("Kisan Suvidha" in name for name in portal_names)


def test_commodity_aliases_mapping():
    assert "Cotton" in COMMODITY_ALIASES
    assert "Tur" in COMMODITY_ALIASES
    # Ensure green vegetable peas are excluded from Tur aliases
    assert "Pigeon Pea" not in COMMODITY_ALIASES["Tur"]
    assert "Arhar (Tur/Red Gram)" in COMMODITY_ALIASES["Tur"]


def test_strict_commodity_record_validation():
    # Valid records
    assert is_valid_commodity_record("Cotton", "Cotton") is True
    assert is_valid_commodity_record("Cotton", "Kapas") is True
    assert is_valid_commodity_record("Tur", "Arhar (Tur/Red Gram)") is True
    assert is_valid_commodity_record("Tur", "Tur") is True
    assert is_valid_commodity_record("Tur", "Red Gram") is True

    # Invalid cross-commodity false positives
    assert is_valid_commodity_record("Tur", "Pea Pod/Pea Cod/ ") is False
    assert is_valid_commodity_record("Tur", "Cowpea(Veg)") is False
    assert is_valid_commodity_record("Cotton", "Wheat") is False


def test_daily_mandi_snapshot_contains_verified_mandis():
    cotton_snapshot = get_daily_mandi_snapshot("Cotton")
    assert len(cotton_snapshot) >= 10
    cotton_markets = [m["market"] for m in cotton_snapshot]
    assert "Dhamangaon APMC" in cotton_markets
    assert "Wardha APMC" in cotton_markets

    tur_snapshot = get_daily_mandi_snapshot("Tur")
    assert len(tur_snapshot) >= 10
    tur_markets = [m["market"] for m in tur_snapshot]
    assert "Akola APMC" in tur_markets
    assert "Latur APMC" in tur_markets


def test_mandi_matching():
    client = LiveAgmarknetClient()
    sample_records = [
        {"state": "Maharashtra", "district": "Amravati", "market": "Dhamangaon Railway APMC", "modal_price": 8550, "min_price": 8200, "max_price": 8800},
        {"state": "Maharashtra", "district": "Akola", "market": "Akola Cotton Market", "modal_price": 10450, "min_price": 9800, "max_price": 10800}
    ]

    # Exact or substring match
    match1 = client.match_mandi("Dhamangaon APMC", "Amravati", sample_records)
    assert match1 is not None
    assert match1["modal_price"] == 8550

    match2 = client.match_mandi("Akola APMC", "Akola", sample_records)
    assert match2 is not None
    assert match2["modal_price"] == 10450


def test_predictor_e2e_live_server_data_source():
    predictor = MarketPricePredictor()
    res = predictor.predict(
        crop="Cotton",
        quantity=20.0,
        farmer_lat=20.7002,
        farmer_lon=77.0082
    )

    assert res["status"] == "success"
    assert "data_source" in res
    ds = res["data_source"]
    assert ds["server_status"] in ["ONLINE", "ONLINE (Agmarknet Live Bulletin)"]
    assert "https://api.data.gov.in" in ds["api_endpoint"]
    assert len(ds["supporting_websites"]) >= 4

    rec = res["recommended_market"]
    assert rec["current_price"] > 0
    assert rec["net_price_per_qtl"] == round(max(0.0, rec["current_price"] - rec["transport_cost_per_qtl"]), 2)
    assert rec["expected_net_amount"] == round(20.0 * rec["net_price_per_qtl"], 2)
    assert rec["price_source"] in ["LIVE_AGMARKNET_SERVER", "LIVE_BENCHMARK_CALIBRATED", "HISTORICAL_LOCAL_DATASET"]
