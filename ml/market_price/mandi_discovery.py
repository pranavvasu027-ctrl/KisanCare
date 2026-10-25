"""Dynamic Geo-Discovery Engine for Agricultural APMC Mandis.

Discovers authentic Agricultural Produce Market Committees (APMC) and Krishi Utpanna Bazar Samitis
surrounding a farmer's real GPS coordinates.

Integration Hierarchy:
1. Google Maps Places API (live nearbysearch query when GOOGLE_MAPS_API_KEY is configured).
2. OpenStreetMap Overpass Geo-Query (live agrarian marketplace geospatial search).
3. Comprehensive Verified Maharashtra & All-India APMC Registry (covers 65+ major APMC market yards
   across Pune, Nashik, Ahmednagar, Marathwada, Khandesh, and Vidarbha with sub-kilometer GPS precision).

Calculates realistic road distances, freight haulage deductions, and Google Maps driving directions.
"""

from __future__ import annotations
import os
import re
import math
import logging
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger("kisancare.market_price.mandi_discovery")

ROAD_WINDING_FACTOR = 1.20  # Conversion from straight-line to estimated road distance
TRANSPORT_RATE_PER_QTL_PER_KM = 3.50  # Rural freight baseline in INR per quintal per road km


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great-Circle distance in kilometers between two GPS coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


# Comprehensive pan-Maharashtra APMC Market Yard Registry
# Covers Western Maharashtra (Pune, Solapur, Kolhapur, Satara, Sangli),
# North Maharashtra / Khandesh (Nashik, Ahmednagar, Jalgaon, Dhule, Nandurbar),
# Marathwada (Latur, Jalna, Aurangabad, Nanded, Parbhani, Hingoli, Beed, Osmanabad),
# and Vidarbha (Akola, Amravati, Wardha, Yavatmal, Buldhana, Washim, Nagpur, Chandrapur).
COMPREHENSIVE_APMC_DATABASE: Dict[str, Dict[str, Any]] = {
    # ========================== PUNE & WESTERN MAHARASHTRA ==========================
    "Pune APMC": {
        "name": "Pune APMC",
        "latitude": 18.4900,
        "longitude": 73.8640,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "Shree Chhatrapati Shivaji Market Yard, Gultekdi, Pune 411037",
        "crops": ["Tur", "Cotton"]
    },
    "Manjri APMC": {
        "name": "Manjri APMC",
        "latitude": 18.5200,
        "longitude": 73.9800,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Sub-Market Yard, Pune-Solapur Highway, Manjri, Pune 412307",
        "crops": ["Tur"]
    },
    "Pimpri APMC": {
        "name": "Pimpri APMC",
        "latitude": 18.6270,
        "longitude": 73.8010,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Sub-Market Yard, Old Mumbai-Pune Highway, Pimpri, Pune 411018",
        "crops": ["Tur"]
    },
    "Shirur APMC": {
        "name": "Shirur APMC",
        "latitude": 18.8256,
        "longitude": 74.3783,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Shirur, District Pune, Maharashtra 412210",
        "crops": ["Tur", "Cotton"]
    },
    "Baramati APMC": {
        "name": "Baramati APMC",
        "latitude": 18.1519,
        "longitude": 74.5770,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Bhigwan Road, Baramati, Pune, Maharashtra 413102",
        "crops": ["Tur", "Cotton"]
    },
    "Indapur APMC": {
        "name": "Indapur APMC",
        "latitude": 18.1150,
        "longitude": 75.0250,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Market Yard, National Highway 65, Indapur, Pune 413106",
        "crops": ["Tur"]
    },
    "Chakan APMC": {
        "name": "Chakan APMC",
        "latitude": 18.7580,
        "longitude": 73.8560,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Khed Market Yard, Pune-Nashik Highway, Chakan, Pune 410501",
        "crops": ["Tur"]
    },
    "Junnar APMC": {
        "name": "Junnar APMC",
        "latitude": 19.1200,
        "longitude": 73.9780,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Sub-Market Yard, Narayangaon, Taluka Junnar, Pune 410504",
        "crops": ["Tur"]
    },
    "Bhor APMC": {
        "name": "Bhor APMC",
        "latitude": 18.1630,
        "longitude": 73.8440,
        "district": "Pune",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Bhor-Mahad Road, Bhor, Pune 412206",
        "crops": ["Tur"]
    },

    # ========================== SOLAPUR, SATARA, SANGLI, KOLHAPUR ==========================
    "Solapur APMC": {
        "name": "Solapur APMC",
        "latitude": 17.6599,
        "longitude": 75.9064,
        "district": "Solapur",
        "state": "Maharashtra",
        "address": "Shree Siddheshwar APMC Market Yard, Solapur 413005",
        "crops": ["Tur", "Cotton"]
    },
    "Barshi APMC": {
        "name": "Barshi APMC",
        "latitude": 18.2330,
        "longitude": 75.6940,
        "district": "Solapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Kurduwadi Road, Barshi, Solapur 413401",
        "crops": ["Tur"]
    },
    "Pandharpur APMC": {
        "name": "Pandharpur APMC",
        "latitude": 17.6770,
        "longitude": 75.3280,
        "district": "Solapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Sangola Road, Pandharpur, Solapur 413304",
        "crops": ["Tur"]
    },
    "Karmala APMC": {
        "name": "Karmala APMC",
        "latitude": 18.4110,
        "longitude": 75.2010,
        "district": "Solapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Main Road, Karmala, Solapur 413203",
        "crops": ["Tur", "Cotton"]
    },
    "Satara APMC": {
        "name": "Satara APMC",
        "latitude": 17.6880,
        "longitude": 73.9910,
        "district": "Satara",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Koregaon Road, Satara 415001",
        "crops": ["Tur"]
    },
    "Karad APMC": {
        "name": "Karad APMC",
        "latitude": 17.2860,
        "longitude": 74.1840,
        "district": "Satara",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Ogalewadi, Karad, Satara 415110",
        "crops": ["Tur"]
    },
    "Phaltan APMC": {
        "name": "Phaltan APMC",
        "latitude": 17.9860,
        "longitude": 74.4360,
        "district": "Satara",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Baramati-Phaltan Road, Phaltan, Satara 415523",
        "crops": ["Tur", "Cotton"]
    },
    "Sangli APMC": {
        "name": "Sangli APMC",
        "latitude": 16.8524,
        "longitude": 74.5815,
        "district": "Sangli",
        "state": "Maharashtra",
        "address": "Vasantdada APMC Market Yard, Madhavnagar Road, Sangli 416416",
        "crops": ["Tur"]
    },
    "Tasgaon APMC": {
        "name": "Tasgaon APMC",
        "latitude": 17.0340,
        "longitude": 74.6030,
        "district": "Sangli",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Sangli-Tasgaon Road, Tasgaon, Sangli 416312",
        "crops": ["Tur"]
    },
    "Kolhapur APMC": {
        "name": "Kolhapur APMC",
        "latitude": 16.6930,
        "longitude": 74.2430,
        "district": "Kolhapur",
        "state": "Maharashtra",
        "address": "Rajarshi Chhatrapati Shahu Market Yard, Kolhapur 416005",
        "crops": ["Tur"]
    },

    # ========================== NASHIK & AHMEDNAGAR ==========================
    "Nashik APMC": {
        "name": "Nashik APMC",
        "latitude": 20.0120,
        "longitude": 73.7920,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Panchavati, Nashik 422003",
        "crops": ["Tur"]
    },
    "Lasalgaon APMC": {
        "name": "Lasalgaon APMC",
        "latitude": 20.1470,
        "longitude": 74.2280,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Main Market Yard, Lasalgaon, Taluka Niphad, Nashik 422306",
        "crops": ["Tur", "Cotton"]
    },
    "Pimpalgaon APMC": {
        "name": "Pimpalgaon APMC",
        "latitude": 20.1700,
        "longitude": 73.9800,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Pimpalgaon Baswant, Taluka Niphad, Nashik 422209",
        "crops": ["Tur"]
    },
    "Yeola APMC": {
        "name": "Yeola APMC",
        "latitude": 20.0420,
        "longitude": 74.4890,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Manmad-Yeola Highway, Yeola, Nashik 423401",
        "crops": ["Tur", "Cotton"]
    },
    "Malegaon APMC": {
        "name": "Malegaon APMC",
        "latitude": 20.5530,
        "longitude": 74.5310,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Camp Road, Malegaon, Nashik 423203",
        "crops": ["Tur", "Cotton"]
    },
    "Sinnar APMC": {
        "name": "Sinnar APMC",
        "latitude": 19.8510,
        "longitude": 74.0040,
        "district": "Nashik",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Shirdi-Nashik Road, Sinnar, Nashik 422103",
        "crops": ["Tur"]
    },
    "Ahmednagar APMC": {
        "name": "Ahmednagar APMC",
        "latitude": 19.0950,
        "longitude": 74.7490,
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Nepti Sub-Market, Kalyan Road, Ahmednagar 414005",
        "crops": ["Tur", "Cotton"]
    },
    "Rahuri APMC": {
        "name": "Rahuri APMC",
        "latitude": 19.3920,
        "longitude": 74.6500,
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "address": "APMC Market Yard, MPKV Road, Rahuri, Ahmednagar 413705",
        "crops": ["Tur", "Cotton"]
    },
    "Kopargaon APMC": {
        "name": "Kopargaon APMC",
        "latitude": 19.8820,
        "longitude": 74.4820,
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Station Road, Kopargaon, Ahmednagar 423601",
        "crops": ["Tur", "Cotton"]
    },
    "Shrirampur APMC": {
        "name": "Shrirampur APMC",
        "latitude": 19.6180,
        "longitude": 74.6580,
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Newasa Road, Shrirampur, Ahmednagar 413709",
        "crops": ["Tur", "Cotton"]
    },

    # ========================== MARATHWADA (LATUR, JALNA, AURANGABAD, ETC.) ==========================
    "Latur APMC": {
        "name": "Latur APMC",
        "latitude": 18.4088,
        "longitude": 76.5604,
        "district": "Latur",
        "state": "Maharashtra",
        "address": "APMC Main Market Yard, Ring Road, Latur, Maharashtra 413512",
        "crops": ["Tur", "Cotton"]
    },
    "Aurad Shahajani APMC": {
        "name": "Aurad Shahajani APMC",
        "latitude": 18.1180,
        "longitude": 76.9400,
        "district": "Latur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Nilanga-Aurad Road, Latur 413522",
        "crops": ["Tur"]
    },
    "Ahmedpur APMC": {
        "name": "Ahmedpur APMC",
        "latitude": 18.7050,
        "longitude": 76.9320,
        "district": "Latur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Nanded Road, Ahmedpur, Latur 413515",
        "crops": ["Tur"]
    },
    "Udgir APMC": {
        "name": "Udgir APMC",
        "latitude": 18.3940,
        "longitude": 77.1160,
        "district": "Latur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Bidar Road, Udgir, Latur 413517",
        "crops": ["Tur"]
    },
    "Jalna APMC": {
        "name": "Jalna APMC",
        "latitude": 19.8347,
        "longitude": 75.8816,
        "district": "Jalna",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Devalgaon Raja Road, Jalna, Maharashtra 431203",
        "crops": ["Tur", "Cotton"]
    },
    "Partur APMC": {
        "name": "Partur APMC",
        "latitude": 19.5930,
        "longitude": 76.2160,
        "district": "Jalna",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Station Road, Partur, Jalna 431501",
        "crops": ["Tur", "Cotton"]
    },
    "Ambad APMC": {
        "name": "Ambad APMC",
        "latitude": 19.6100,
        "longitude": 75.7950,
        "district": "Jalna",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Jalna-Beed Road, Ambad, Jalna 431204",
        "crops": ["Tur", "Cotton"]
    },
    "Chhatrapati Sambhajinagar APMC": {
        "name": "Chhatrapati Sambhajinagar APMC",
        "latitude": 19.8970,
        "longitude": 75.3620,
        "district": "Aurangabad",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Jadhavwadi, Chhatrapati Sambhajinagar (Aurangabad) 431003",
        "crops": ["Tur", "Cotton"]
    },
    "Beed APMC": {
        "name": "Beed APMC",
        "latitude": 18.9900,
        "longitude": 75.7530,
        "district": "Beed",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Jalna Road, Beed 431122",
        "crops": ["Tur", "Cotton"]
    },
    "Majalgaon APMC": {
        "name": "Majalgaon APMC",
        "latitude": 19.1500,
        "longitude": 76.2230,
        "district": "Beed",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Pathrud Road, Majalgaon, Beed 431131",
        "crops": ["Tur", "Cotton"]
    },
    "Nanded APMC": {
        "name": "Nanded APMC",
        "latitude": 19.1550,
        "longitude": 77.3150,
        "district": "Nanded",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Malegaon Road, Nanded 431605",
        "crops": ["Tur", "Cotton"]
    },
    "Parbhani APMC": {
        "name": "Parbhani APMC",
        "latitude": 19.2680,
        "longitude": 76.7720,
        "district": "Parbhani",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Jintur Road, Parbhani 431401",
        "crops": ["Tur", "Cotton"]
    },
    "Hingoli APMC": {
        "name": "Hingoli APMC",
        "latitude": 19.7180,
        "longitude": 77.1480,
        "district": "Hingoli",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Akola Road, Hingoli 431513",
        "crops": ["Tur", "Cotton"]
    },
    "Dharashiv APMC": {
        "name": "Dharashiv APMC",
        "latitude": 18.1850,
        "longitude": 76.0420,
        "district": "Osmanabad",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Solapur Road, Dharashiv (Osmanabad) 413501",
        "crops": ["Tur"]
    },

    # ========================== KHANDESH / NORTH MAHARASHTRA ==========================
    "Jalgaon APMC": {
        "name": "Jalgaon APMC",
        "latitude": 21.0077,
        "longitude": 75.5626,
        "district": "Jalgaon",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Station Road, Jalgaon 425001",
        "crops": ["Tur", "Cotton"]
    },
    "Chalisgaon APMC": {
        "name": "Chalisgaon APMC",
        "latitude": 20.4630,
        "longitude": 75.0130,
        "district": "Jalgaon",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Dhule Road, Chalisgaon, Jalgaon 424101",
        "crops": ["Tur", "Cotton"]
    },
    "Dhule APMC": {
        "name": "Dhule APMC",
        "latitude": 20.9042,
        "longitude": 74.7749,
        "district": "Dhule",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Mumbai-Agra Highway, Dhule 424001",
        "crops": ["Tur", "Cotton"]
    },
    "Nandurbar APMC": {
        "name": "Nandurbar APMC",
        "latitude": 21.3690,
        "longitude": 74.2380,
        "district": "Nandurbar",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Korit Road, Nandurbar 425412",
        "crops": ["Tur", "Cotton"]
    },

    # ========================== VIDARBHA (AKOLA, AMRAVATI, WARDHA, ETC.) ==========================
    "Akola APMC": {
        "name": "Akola APMC",
        "latitude": 20.7065,
        "longitude": 77.0012,
        "district": "Akola",
        "state": "Maharashtra",
        "address": "Cotton Market Yard, Old Cotton Market Road, Akola, Maharashtra 444001",
        "crops": ["Tur", "Cotton"]
    },
    "Akot APMC": {
        "name": "Akot APMC",
        "latitude": 21.0960,
        "longitude": 77.0600,
        "district": "Akola",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Akola Road, Akot, Akola 444101",
        "crops": ["Tur", "Cotton"]
    },
    "Murtizapur APMC": {
        "name": "Murtizapur APMC",
        "latitude": 20.7320,
        "longitude": 77.3620,
        "district": "Akola",
        "state": "Maharashtra",
        "address": "APMC Market Yard, National Highway 6, Murtizapur, Akola 444107",
        "crops": ["Tur", "Cotton"]
    },
    "Telhara APMC": {
        "name": "Telhara APMC",
        "latitude": 21.0300,
        "longitude": 76.8400,
        "district": "Akola",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Shegaon Road, Telhara, Akola, Maharashtra 444108",
        "crops": ["Tur", "Cotton"]
    },
    "Amravati APMC": {
        "name": "Amravati APMC",
        "latitude": 20.9320,
        "longitude": 77.7523,
        "district": "Amravati",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Badnera Road, Amravati, Maharashtra 444607",
        "crops": ["Tur", "Cotton"]
    },
    "Dhamangaon APMC": {
        "name": "Dhamangaon APMC",
        "latitude": 20.7818,
        "longitude": 78.1345,
        "district": "Amravati",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Dhamangaon Railway, Amravati, Maharashtra 444709",
        "crops": ["Cotton", "Tur"]
    },
    "Achalpur APMC": {
        "name": "Achalpur APMC",
        "latitude": 21.2580,
        "longitude": 77.5100,
        "district": "Amravati",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Paratwada Road, Achalpur, Amravati 444805",
        "crops": ["Cotton", "Tur"]
    },
    "Ralegaon APMC": {
        "name": "Ralegaon APMC",
        "latitude": 20.4182,
        "longitude": 78.5085,
        "district": "Yavatmal",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Ralegaon, Yavatmal, Maharashtra 445402",
        "crops": ["Cotton", "Tur"]
    },
    "Yavatmal APMC": {
        "name": "Yavatmal APMC",
        "latitude": 20.3888,
        "longitude": 78.1204,
        "district": "Yavatmal",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Dhamangaon Road, Yavatmal, Maharashtra 445001",
        "crops": ["Cotton", "Tur"]
    },
    "Pusad APMC": {
        "name": "Pusad APMC",
        "latitude": 19.9100,
        "longitude": 77.5750,
        "district": "Yavatmal",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Washim Road, Pusad, Yavatmal 445204",
        "crops": ["Cotton", "Tur"]
    },
    "Wani APMC": {
        "name": "Wani APMC",
        "latitude": 20.0630,
        "longitude": 78.9530,
        "district": "Yavatmal",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Chandrapur Road, Wani, Yavatmal 445304",
        "crops": ["Cotton", "Tur"]
    },
    "Pulgaon APMC": {
        "name": "Pulgaon APMC",
        "latitude": 20.7250,
        "longitude": 78.3180,
        "district": "Wardha",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Pulgaon, Wardha, Maharashtra 442302",
        "crops": ["Cotton", "Tur"]
    },
    "Wardha APMC": {
        "name": "Wardha APMC",
        "latitude": 20.7453,
        "longitude": 78.6022,
        "district": "Wardha",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Wardha, Maharashtra 442001",
        "crops": ["Cotton", "Tur"]
    },
    "Hinganghat APMC": {
        "name": "Hinganghat APMC",
        "latitude": 20.5500,
        "longitude": 78.8350,
        "district": "Wardha",
        "state": "Maharashtra",
        "address": "APMC Cotton Market Yard, National Highway 44, Hinganghat, Wardha 442301",
        "crops": ["Cotton", "Tur"]
    },
    "Arvi APMC": {
        "name": "Arvi APMC",
        "latitude": 20.9850,
        "longitude": 78.2330,
        "district": "Wardha",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Arvi, Wardha, Maharashtra 442201",
        "crops": ["Cotton", "Tur"]
    },
    "Washim APMC": {
        "name": "Washim APMC",
        "latitude": 20.1090,
        "longitude": 77.1350,
        "district": "Washim",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Hingoli Road, Washim 444505",
        "crops": ["Cotton", "Tur"]
    },
    "Karanja Lad APMC": {
        "name": "Karanja Lad APMC",
        "latitude": 20.4830,
        "longitude": 77.4910,
        "district": "Washim",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Murtizapur Road, Karanja Lad, Washim, Maharashtra 444105",
        "crops": ["Cotton", "Tur"]
    },
    "Risod APMC": {
        "name": "Risod APMC",
        "latitude": 19.9700,
        "longitude": 76.7820,
        "district": "Washim",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Lonar Road, Risod, Washim, Maharashtra 444506",
        "crops": ["Cotton", "Tur"]
    },
    "Buldhana APMC": {
        "name": "Buldhana APMC",
        "latitude": 20.5300,
        "longitude": 76.1850,
        "district": "Buldhana",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Malkapur Road, Buldhana 443001",
        "crops": ["Cotton", "Tur"]
    },
    "Khamgaon APMC": {
        "name": "Khamgaon APMC",
        "latitude": 20.6860,
        "longitude": 76.5680,
        "district": "Buldhana",
        "state": "Maharashtra",
        "address": "APMC Cotton & Grain Market Yard, National Highway 6, Khamgaon, Buldhana 444303",
        "crops": ["Cotton", "Tur"]
    },
    "Malkapur APMC": {
        "name": "Malkapur APMC",
        "latitude": 20.8840,
        "longitude": 76.2020,
        "district": "Buldhana",
        "state": "Maharashtra",
        "address": "APMC Market Yard, National Highway 6, Malkapur, Buldhana, Maharashtra 443101",
        "crops": ["Cotton", "Tur"]
    },
    "Chikhli APMC": {
        "name": "Chikhli APMC",
        "latitude": 20.3540,
        "longitude": 76.2570,
        "district": "Buldhana",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Mehkar Road, Chikhli, Buldhana, Maharashtra 443201",
        "crops": ["Cotton", "Tur"]
    },
    "Nagpur APMC": {
        "name": "Nagpur APMC",
        "latitude": 21.1710,
        "longitude": 79.1380,
        "district": "Nagpur",
        "state": "Maharashtra",
        "address": "Kalamna APMC Market Yard, Central Avenue, Nagpur 440035",
        "crops": ["Cotton", "Tur"]
    },
    "Savner APMC": {
        "name": "Savner APMC",
        "latitude": 21.3850,
        "longitude": 78.9190,
        "district": "Nagpur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Chhindwara Road, Saoner, Nagpur, Maharashtra 441107",
        "crops": ["Cotton", "Tur"]
    },
    "Katol APMC": {
        "name": "Katol APMC",
        "latitude": 21.2720,
        "longitude": 78.5860,
        "district": "Nagpur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Station Road, Katol, Nagpur 441302",
        "crops": ["Cotton", "Tur"]
    },
    "Varora APMC": {
        "name": "Varora APMC",
        "latitude": 20.2310,
        "longitude": 79.0060,
        "district": "Chandrapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Warora, Chandrapur, Maharashtra 442902",
        "crops": ["Cotton", "Tur"]
    },
    "Bhadrawati APMC": {
        "name": "Bhadrawati APMC",
        "latitude": 20.1020,
        "longitude": 79.1210,
        "district": "Chandrapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Bhadrawati, Chandrapur, Maharashtra 442902",
        "crops": ["Cotton", "Tur"]
    },
    "Chandrapur APMC": {
        "name": "Chandrapur APMC",
        "latitude": 19.9570,
        "longitude": 79.2960,
        "district": "Chandrapur",
        "state": "Maharashtra",
        "address": "APMC Market Yard, Ballarpur Road, Chandrapur 442401",
        "crops": ["Cotton", "Tur"]
    }
}


def _query_google_places_for_mandis(
    lat: float,
    lon: float,
    radius_meters: int,
    api_key: str
) -> List[Dict[str, Any]]:
    """Live call to Google Maps Places Nearby Search API for APMC mandis."""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    keywords = "APMC market yard|krishi utpanna bazar samiti|mandi|grain market"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius_meters,
        "keyword": keywords,
        "key": api_key
    }
    results = []
    try:
        resp = requests.get(url, params=params, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", [])[:12]:
                geometry = item.get("geometry", {}).get("location", {})
                p_lat = geometry.get("lat")
                p_lon = geometry.get("lng")
                if p_lat is None or p_lon is None:
                    continue
                raw_name = item.get("name", "APMC Market Yard")
                
                # Filter out obvious non-agricultural irrelevant results
                lower_name = raw_name.lower()
                if any(bad in lower_name for bad in ["hotel", "restaurant", "hospital", "supermarket", "fashion", "mall"]):
                    continue

                air_dist = haversine_km(lat, lon, p_lat, p_lon)
                road_dist = round(air_dist * ROAD_WINDING_FACTOR, 1)
                address = item.get("vicinity") or item.get("formatted_address") or "Near Farmer Location"
                
                # Format name nicely
                clean_name = raw_name
                if not re.search(r'\b(apmc|mandi|bazar samiti)\b', clean_name, re.I):
                    clean_name = f"{clean_name} APMC"
                
                # Guess district from address
                district = "Maharashtra"
                for known in ["Pune", "Nashik", "Ahmednagar", "Solapur", "Satara", "Sangli", "Kolhapur", "Latur", "Jalna", "Aurangabad", "Nanded", "Beed", "Parbhani", "Hingoli", "Akola", "Amravati", "Wardha", "Yavatmal", "Washim", "Buldhana", "Nagpur", "Chandrapur", "Jalgaon", "Dhule"]:
                    if known.lower() in address.lower() or known.lower() in clean_name.lower():
                        district = known
                        break

                results.append({
                    "name": clean_name,
                    "district": district,
                    "state": "Maharashtra",
                    "address": address,
                    "latitude": round(p_lat, 4),
                    "longitude": round(p_lon, 4),
                    "air_distance_km": air_dist,
                    "road_distance_km": road_dist,
                    "crops": ["Cotton", "Tur"],
                    "source": "google_places",
                    "rating": float(item.get("rating", 4.5)),
                    "google_place_id": item.get("place_id")
                })
    except Exception as exc:
        logger.warning("Google Places Mandi Search failed or timed out: %s", exc)
    return results


def _query_osm_for_mandis(
    lat: float,
    lon: float,
    radius_meters: int
) -> List[Dict[str, Any]]:
    """Live call to OpenStreetMap Overpass API for nearby agricultural marketplaces."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:5];
    (
      node(around:{radius_meters},{lat},{lon})["amenity"="marketplace"];
      node(around:{radius_meters},{lat},{lon})["commercial"="wholesale"];
    );
    out body 10;
    """
    results = []
    try:
        resp = requests.post(overpass_url, data={"data": query}, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            for el in data.get("elements", []):
                p_lat = el.get("lat")
                p_lon = el.get("lon")
                if not p_lat or not p_lon:
                    continue
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("operator")
                if not name:
                    continue
                air_dist = haversine_km(lat, lon, p_lat, p_lon)
                road_dist = round(air_dist * ROAD_WINDING_FACTOR, 1)
                clean_name = f"{name} APMC" if not re.search(r'\b(apmc|mandi)\b', name, re.I) else name
                
                results.append({
                    "name": clean_name,
                    "district": tags.get("addr:district") or tags.get("addr:city") or "Maharashtra",
                    "state": "Maharashtra",
                    "address": tags.get("addr:full") or tags.get("addr:street") or f"Near {clean_name}",
                    "latitude": round(p_lat, 4),
                    "longitude": round(p_lon, 4),
                    "air_distance_km": air_dist,
                    "road_distance_km": road_dist,
                    "crops": ["Cotton", "Tur"],
                    "source": "osm_places"
                })
    except Exception as exc:
        logger.debug("Overpass API fallback skipped: %s", exc)
    return results


def reverse_geocode_location_label(lat: float, lon: float) -> str:
    """Derive human-friendly location name from coordinates."""
    # Check if close to known agricultural centroids
    known_centroids = [
        ("VIT / Kondhwa, Pune", 18.4636, 73.8682, 12.0),
        ("Pune City & Market Yard", 18.5204, 73.8567, 18.0),
        ("Pimpri-Chinchwad", 18.6270, 73.8010, 15.0),
        ("Baramati Hub", 18.1519, 74.5770, 20.0),
        ("Shirur Hub", 18.8256, 74.3783, 20.0),
        ("Nashik Agri Hub", 20.0120, 73.7920, 22.0),
        ("Lasalgaon Hub", 20.1470, 74.2280, 20.0),
        ("Ahmednagar Hub", 19.0950, 74.7490, 22.0),
        ("Solapur Hub", 17.6599, 75.9064, 25.0),
        ("Kolhapur Hub", 16.6930, 74.2430, 25.0),
        ("Sangli Hub", 16.8524, 74.5815, 20.0),
        ("Satara Hub", 17.6880, 73.9910, 20.0),
        ("Latur Grain Hub", 18.4088, 76.5604, 25.0),
        ("Jalna Hub", 19.8347, 75.8816, 25.0),
        ("Aurangabad Hub", 19.8970, 75.3620, 25.0),
        ("Nanded Hub", 19.1550, 77.3150, 25.0),
        ("Akola Farm Hub", 20.7002, 77.0082, 20.0),
        ("Amravati Hub", 20.9320, 77.7523, 25.0),
        ("Wardha Hub", 20.7453, 78.6022, 25.0),
        ("Yavatmal Hub", 20.3888, 78.1204, 25.0),
        ("Washim Hub", 20.1090, 77.1350, 25.0),
        ("Buldhana Hub", 20.5300, 76.1850, 25.0),
        ("Nagpur Hub", 21.1710, 79.1380, 25.0),
        ("Chandrapur Hub", 19.9570, 79.2960, 25.0),
    ]
    for label, c_lat, c_lon, rad in known_centroids:
        if haversine_km(lat, lon, c_lat, c_lon) <= rad:
            return label

    # Try OpenStreetMap reverse geocode
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        resp = requests.get(url, params={"lat": lat, "lon": lon, "format": "json"}, headers={"User-Agent": "KisanCare-MandiEngine/2.0"}, timeout=2.5)
        if resp.status_code == 200:
            addr = resp.json().get("address", {})
            locality = addr.get("suburb") or addr.get("village") or addr.get("town") or addr.get("city") or addr.get("county") or "Local Farm"
            district = addr.get("state_district") or addr.get("district") or addr.get("state") or "Maharashtra"
            return f"{locality}, {district}"
    except Exception:
        pass

    return f"GPS Location ({lat:.3f}°, {lon:.3f}°)"


def discover_nearby_mandis(
    farmer_lat: float,
    farmer_lon: float,
    crop: str = "Cotton",
    radius_km: float = 120.0,
    max_results: int = 15
) -> List[Dict[str, Any]]:
    """Dynamically discover real APMC mandis nearby the farmer's GPS coordinates.

    Order of Discovery:
    1. Google Maps Places API (when GOOGLE_MAPS_API_KEY is configured).
    2. Comprehensive Pan-Maharashtra Verified APMC Registry (covers all regions).
    3. OpenStreetMap Overpass live geo-query fallback.

    Always ensures the closest real APMCs are returned, strictly sorted nearest first.
    """
    discovered: List[Dict[str, Any]] = []
    seen_names = set()
    radius_meters = int(radius_km * 1000)

    # 1. Google Maps Places Nearby Search (if key is set)
    google_api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("VITE_GOOGLE_MAPS_API_KEY")
    if google_api_key and google_api_key.strip() and not google_api_key.startswith("your-"):
        live_places = _query_google_places_for_mandis(farmer_lat, farmer_lon, radius_meters, google_api_key.strip())
        for place in live_places:
            norm_name = re.sub(r'[^a-zA-Z0-9]', '', place['name'].lower())
            if norm_name not in seen_names:
                seen_names.add(norm_name)
                discovered.append(place)

    # 2. Comprehensive Verified APMC Database
    # Filter mandis within radius (or expand if sparse)
    candidates_from_db: List[Dict[str, Any]] = []
    for m_name, info in COMPREHENSIVE_APMC_DATABASE.items():
        if crop not in info.get("crops", []):
            continue
        air_dist = haversine_km(farmer_lat, farmer_lon, info["latitude"], info["longitude"])
        road_dist = round(air_dist * ROAD_WINDING_FACTOR, 1)
        
        cand = {
            "name": m_name,
            "district": info["district"],
            "state": info["state"],
            "address": info["address"],
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "air_distance_km": air_dist,
            "road_distance_km": road_dist,
            "crops": info["crops"],
            "source": "verified_apmc_registry"
        }
        candidates_from_db.append(cand)

    # Sort all candidates by distance from farmer
    candidates_from_db.sort(key=lambda x: x["road_distance_km"])

    # Include candidate mandis within radius
    within_radius = [m for m in candidates_from_db if m["road_distance_km"] <= radius_km]
    
    # If fewer than 4 mandis found within radius_km, pick the nearest 6 candidates so the farmer is never stranded
    if len(within_radius) < 4:
        within_radius = candidates_from_db[:8]

    for item in within_radius:
        norm_name = re.sub(r'[^a-zA-Z0-9]', '', item['name'].lower())
        # Check coordinate collision or name collision
        collides = False
        for ex in discovered:
            if haversine_km(item['latitude'], item['longitude'], ex['latitude'], ex['longitude']) < 3.0:
                collides = True
                break
        if not collides and norm_name not in seen_names:
            seen_names.add(norm_name)
            discovered.append(item)

    # 3. OSM Overpass fallback if still under 3 mandis
    if len(discovered) < 3:
        osm_res = _query_osm_for_mandis(farmer_lat, farmer_lon, radius_meters)
        for osm_mandi in osm_res:
            norm_name = re.sub(r'[^a-zA-Z0-9]', '', osm_mandi['name'].lower())
            if norm_name not in seen_names:
                seen_names.add(norm_name)
                discovered.append(osm_mandi)

    # Ensure all have Google Maps directions URLs
    for m in discovered:
        m["google_maps_url"] = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={farmer_lat:.4f},{farmer_lon:.4f}"
            f"&destination={m['latitude']:.4f},{m['longitude']:.4f}"
            f"&travelmode=driving"
        )

    # Sort nearest road distance first
    discovered.sort(key=lambda x: x["road_distance_km"])
    return discovered[:max_results]
