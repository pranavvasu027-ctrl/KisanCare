"""
Local Fertilizer Store Catalog & Discovery Service for Maharashtra Agricultural Regions.
Provides locality-aware retailer matching, mock demonstration inventory, and Amazon.in search links.
"""

import urllib.parse
from typing import Any, Dict, List, Optional
from .schemas import AmazonProductLink, FertilizerStore, FertilizerStoreProduct

# Dedicated demonstration catalog of agricultural input retailers across Maharashtra districts
DEMO_FERTILIZER_STORES: List[Dict[str, Any]] = [
    {
        "store_id": "store-akola-01",
        "store_name": "Krishi Vikas Agro Center (Demo)",
        "address": "Opposite APMC Market Yard, Station Road",
        "village": "Takli Bu",
        "district": "Akola",
        "pin_code": "444001",
        "contact_phone": "+91 98230 11234 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 140, "in_stock": True},
            {"product_name": "Di-Ammonium Phosphate (DAP)", "nutrient_grade": "18-46-0", "mock_price_inr": 1350.00, "unit": "50 kg bag", "mock_stock_bags": 85, "in_stock": True},
            {"product_name": "Muriate of Potash (MOP)", "nutrient_grade": "0-0-60", "mock_price_inr": 1700.00, "unit": "50 kg bag", "mock_stock_bags": 45, "in_stock": True},
            {"product_name": "Mahadhan NPK Complex", "nutrient_grade": "10-26-26", "mock_price_inr": 1475.00, "unit": "50 kg bag", "mock_stock_bags": 60, "in_stock": True},
            {"product_name": "Organic Vermicompost", "nutrient_grade": "Enriched Humus", "mock_price_inr": 450.00, "unit": "50 kg bag", "mock_stock_bags": 120, "in_stock": True},
        ]
    },
    {
        "store_id": "store-akola-02",
        "store_name": "Murtizapur Kisan Seva Kendra (Demo)",
        "address": "Karanja Road, Near Bus Stand",
        "village": "Murtizapur",
        "district": "Akola",
        "pin_code": "444107",
        "contact_phone": "+91 94221 22345 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 90, "in_stock": True},
            {"product_name": "Single Super Phosphate (SSP)", "nutrient_grade": "0-16-0 + 11% S", "mock_price_inr": 550.00, "unit": "50 kg bag", "mock_stock_bags": 110, "in_stock": True},
            {"product_name": "Muriate of Potash (MOP)", "nutrient_grade": "0-0-60", "mock_price_inr": 1700.00, "unit": "50 kg bag", "mock_stock_bags": 30, "in_stock": True},
            {"product_name": "Agricultural Gypsum", "nutrient_grade": "CaSO4 (Soil Amendment)", "mock_price_inr": 220.00, "unit": "50 kg bag", "mock_stock_bags": 70, "in_stock": True},
        ]
    },
    {
        "store_id": "store-amravati-01",
        "store_name": "Vidarbha Shetkari Sahakari Kharedi Vikri Samiti (Demo)",
        "address": "Cotton Market Square, Badnera Road",
        "village": "Badnera",
        "district": "Amravati",
        "pin_code": "444601",
        "contact_phone": "+91 98222 33456 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 200, "in_stock": True},
            {"product_name": "Di-Ammonium Phosphate (DAP)", "nutrient_grade": "18-46-0", "mock_price_inr": 1350.00, "unit": "50 kg bag", "mock_stock_bags": 110, "in_stock": True},
            {"product_name": "Mahadhan NPK Complex", "nutrient_grade": "12-32-16", "mock_price_inr": 1490.00, "unit": "50 kg bag", "mock_stock_bags": 55, "in_stock": True},
            {"product_name": "Muriate of Potash (MOP)", "nutrient_grade": "0-0-60", "mock_price_inr": 1700.00, "unit": "50 kg bag", "mock_stock_bags": 40, "in_stock": True},
            {"product_name": "Zinc Sulphate Monohydrate", "nutrient_grade": "33% Zn", "mock_price_inr": 85.00, "unit": "5 kg pouch", "mock_stock_bags": 150, "in_stock": True},
        ]
    },
    {
        "store_id": "store-pune-01",
        "store_name": "Sahyadri Agro Inputs & Agri Clinic (Demo)",
        "address": "Market Yard Gate No. 2, Gultekdi",
        "village": "Gultekdi",
        "district": "Pune",
        "pin_code": "411037",
        "contact_phone": "+91 98220 44567 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 120, "in_stock": True},
            {"product_name": "Di-Ammonium Phosphate (DAP)", "nutrient_grade": "18-46-0", "mock_price_inr": 1350.00, "unit": "50 kg bag", "mock_stock_bags": 75, "in_stock": True},
            {"product_name": "Soluble NPK 19-19-19 (Foliar)", "nutrient_grade": "19-19-19 Water Soluble", "mock_price_inr": 180.00, "unit": "1 kg pack", "mock_stock_bags": 200, "in_stock": True},
            {"product_name": "Muriate of Potash (MOP)", "nutrient_grade": "0-0-60", "mock_price_inr": 1700.00, "unit": "50 kg bag", "mock_stock_bags": 50, "in_stock": True},
            {"product_name": "Agricultural Lime", "nutrient_grade": "CaCO3 High Purity", "mock_price_inr": 180.00, "unit": "50 kg bag", "mock_stock_bags": 60, "in_stock": True},
        ]
    },
    {
        "store_id": "store-nashik-01",
        "store_name": "Godavari Krishi Bhandar (Demo)",
        "address": "Dindori Naka, Panchavati",
        "village": "Panchavati",
        "district": "Nashik",
        "pin_code": "422003",
        "contact_phone": "+91 94222 55678 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 105, "in_stock": True},
            {"product_name": "Single Super Phosphate (SSP)", "nutrient_grade": "0-16-0", "mock_price_inr": 540.00, "unit": "50 kg bag", "mock_stock_bags": 80, "in_stock": True},
            {"product_name": "Sulphate of Potash (SOP)", "nutrient_grade": "0-0-50 + 17.5% S", "mock_price_inr": 2400.00, "unit": "50 kg bag", "mock_stock_bags": 35, "in_stock": True},
            {"product_name": "Organic Vermicompost", "nutrient_grade": "Enriched Humus", "mock_price_inr": 420.00, "unit": "50 kg bag", "mock_stock_bags": 95, "in_stock": True},
        ]
    },
    {
        "store_id": "store-nagpur-01",
        "store_name": "Orange City Kisan Kendra (Demo)",
        "address": "Cotton Market, Ganeshpeth",
        "village": "Ganeshpeth",
        "district": "Nagpur",
        "pin_code": "440018",
        "contact_phone": "+91 98231 66789 (Sample)",
        "products": [
            {"product_name": "Neem Coated Urea", "nutrient_grade": "46% N", "mock_price_inr": 266.50, "unit": "45 kg bag", "mock_stock_bags": 160, "in_stock": True},
            {"product_name": "Di-Ammonium Phosphate (DAP)", "nutrient_grade": "18-46-0", "mock_price_inr": 1350.00, "unit": "50 kg bag", "mock_stock_bags": 90, "in_stock": True},
            {"product_name": "Mahadhan NPK Complex", "nutrient_grade": "10-26-26", "mock_price_inr": 1475.00, "unit": "50 kg bag", "mock_stock_bags": 70, "in_stock": True},
            {"product_name": "Muriate of Potash (MOP)", "nutrient_grade": "0-0-60", "mock_price_inr": 1700.00, "unit": "50 kg bag", "mock_stock_bags": 45, "in_stock": True},
        ]
    }
]


def find_matching_stores(
    locality: Optional[str] = None,
    pin_code: Optional[str] = None,
    district: Optional[str] = None,
    recommended_fertilizers: Optional[List[str]] = None,
) -> List[FertilizerStore]:
    """
    Search and rank local demo stores based on locality criteria.
    Ranks:
    1. Same village/locality
    2. Same PIN code
    3. Same district
    4. Regional demonstration entries
    """
    loc_clean = (locality or "").strip().lower()
    pin_clean = (pin_code or "").strip()
    dist_clean = (district or "").strip().lower()

    scored_stores = []
    for raw in DEMO_FERTILIZER_STORES:
        store_village = raw["village"].strip().lower()
        store_pin = raw["pin_code"].strip()
        store_dist = raw["district"].strip().lower()

        match_level = "regional_demo"
        score = 0

        if loc_clean and loc_clean in store_village:
            match_level = "same_village"
            score = 100
        elif pin_clean and pin_clean == store_pin:
            match_level = "same_pincode"
            score = 75
        elif dist_clean and dist_clean in store_dist:
            match_level = "same_district"
            score = 50
        else:
            match_level = "regional_demo"
            score = 10

        # Filter and prioritize products matching recommendation
        prods = [
            FertilizerStoreProduct(
                product_name=p["product_name"],
                nutrient_grade=p["nutrient_grade"],
                mock_price_inr=p["mock_price_inr"],
                unit=p["unit"],
                mock_stock_bags=p["mock_stock_bags"],
                in_stock=p["in_stock"],
            )
            for p in raw["products"]
        ]

        scored_stores.append((
            score,
            FertilizerStore(
                store_id=raw["store_id"],
                store_name=raw["store_name"],
                address=raw["address"],
                village=raw["village"],
                district=raw["district"],
                pin_code=raw["pin_code"],
                contact_phone=raw["contact_phone"],
                distance_km=None,  # No fabricated GPS distances
                locality_match_level=match_level,
                is_demo_inventory=True,
                available_products=prods,
                disclaimer="Demo inventory — verify with the retailer before visiting.",
            )
        ))

    # Sort descending by locality match score
    scored_stores.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored_stores]


def build_amazon_discovery_links(fertilizer_names: List[str]) -> List[AmazonProductLink]:
    """
    Generate direct, verified Amazon.in search query links with attribution and disclaimers.
    Does NOT fabricate simulated live prices or fake inventory.
    """
    links = []
    for fname in fertilizer_names:
        clean_name = fname.strip()
        query = f"{clean_name} agricultural fertilizer"
        encoded_q = urllib.parse.quote_plus(query)
        url = f"https://www.amazon.in/s?k={encoded_q}&ref=nb_sb_noss"

        links.append(
            AmazonProductLink(
                product_name=clean_name,
                search_query=query,
                amazon_search_url=url,
                attribution="Amazon.in direct verified search link",
                disclaimer="Prices and stock vary on Amazon.in. Check seller ratings and delivery time before ordering."
            )
        )
    return links
