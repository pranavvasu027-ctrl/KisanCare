"""Complete, structured dataset of Maharashtra's 6 Administrative Divisions,
36 Districts, and major Talukas for agricultural service coverage.
"""

from typing import Dict, List, Any

MAHARASHTRA_DIVISIONS: Dict[str, Dict[str, Any]] = {
    "Amravati": {
        "name": "Amravati Division (Vidarbha)",
        "regional_university": "Dr. Panjabrao Deshmukh Krishi Vidyapeeth (PDKV), Akola",
        "districts": {
            "Akola": ["Akola", "Murtizapur", "Barshitakli", "Telhara", "Balapur", "Patur", "Akot"],
            "Amravati": ["Amravati", "Achalpur", "Chandur Bazar", "Warud", "Morshi", "Daryapur", "Anjangaon Surji", "Nandgaon Khandeshwar", "Teosa", "Dhamangaon Railway"],
            "Buldhana": ["Buldhana", "Khamgaon", "Malkapur", "Shegaon", "Mehkar", "Chikhli", "Deulgaon Raja", "Jalgaon Jamod", "Nandura", "Motala"],
            "Washim": ["Washim", "Malegaon", "Risod", "Mangrulpir", "Karanja", "Manora"],
            "Yavatmal": ["Yavatmal", "Pusad", "Umarkhed", "Digras", "Darwha", "Wani", "Pandharkawada", "Ner", "Ghatanji", "Ralegaon"]
        }
    },
    "Nagpur": {
        "name": "Nagpur Division (Vidarbha)",
        "regional_university": "Dr. Panjabrao Deshmukh Krishi Vidyapeeth (PDKV) / CICR Nagpur",
        "districts": {
            "Nagpur": ["Nagpur Urban", "Nagpur Rural", "Kamptee", "Hingna", "Umred", "Saoner", "Katol", "Narkhed", "Ramtek", "Kalameshwar", "Bhiwapur"],
            "Wardha": ["Wardha", "Deoli", "Seloo", "Arvi", "Ashti", "Hinganghat", "Samudrapur", "Karanja"],
            "Bhandara": ["Bhandara", "Tumsar", "Pauni", "Mohadi", "Sakoli", "Lakhani", "Lakhandur"],
            "Gondia": ["Gondia", "Tirora", "Goregaon", "Arjuni Morgaon", "Deori", "Salekasa", "Amgaon", "Sadak Arjuni"],
            "Chandrapur": ["Chandrapur", "Ballarpur", "Warora", "Bhadravati", "Rajura", "Mul", "Bramhapuri", "Chimur", "Nagbhid", "Sindewahi"],
            "Gadchiroli": ["Gadchiroli", "Armori", "Chamorshi", "Kurkheda", "Dhanora", "Aheri", "Desaiganj", "Sironcha"]
        }
    },
    "Pune": {
        "name": "Pune Division (Western Maharashtra)",
        "regional_university": "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri / Pune College of Agri",
        "districts": {
            "Pune": ["Haveli", "Pune City", "Baramati", "Shirur", "Daund", "Indapur", "Junnar", "Ambegaon", "Khed", "Maval", "Mulshi", "Bhor", "Purandar", "Velhe"],
            "Satara": ["Satara", "Karad", "Phaltan", "Wai", "Koregaon", "Khatav", "Man", "Patan", "Jaoli", "Mahabaleshwar", "Khandala"],
            "Sangli": ["Miraj", "Walwa (Islampur)", "Tasgaon", "Shirala", "Khanapur", "Atpadi", "Kavathe Mahankal", "Jath", "Kadegaon", "Palus"],
            "Solapur": ["Solapur North", "Solapur South", "Pandharpur", "Barshi", "Mohol", "Madha", "Karmala", "Sangola", "Malshiras", "Akkalkot", "Mangalwedha"],
            "Kolhapur": ["Karvir", "Hatkanangle", "Shirol", "Radhanagari", "Panhala", "Kagal", "Gadhinglaj", "Bhudargad", "Shahuwadi", "Ajra", "Chandgad", "Bawda"]
        }
    },
    "Nashik": {
        "name": "Nashik Division (North Maharashtra)",
        "regional_university": "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri / NRC Grapes Nashik",
        "districts": {
            "Nashik": ["Nashik", "Niphad", "Dindori", "Sinnar", "Yeola", "Malegaon", "Chandwad", "Kalwan", "Baglan (Satana)", "Igatpuri", "Trimbakeshwar", "Deola", "Nandgaon"],
            "Ahilyanagar": ["Nagar", "Sangamner", "Rahata", "Shrirampur", "Kopargaon", "Newasa", "Shevgaon", "Parner", "Pathardi", "Karjat", "Jamkhed", "Akole", "Shrigonda"],
            "Jalgaon": ["Jalgaon", "Bhusawal", "Chalisgaon", "Raver", "Yawal", "Chopda", "Amalner", "Pachora", "Erandol", "Jamner", "Parola", "Bhadgaon", "Dharangaon", "Bodwad", "Muktainagar"],
            "Dhule": ["Dhule", "Sakri", "Shirpur", "Sindkheda"],
            "Nandurbar": ["Nandurbar", "Shahada", "Taloda", "Navapur", "Akkalkuwa", "Dhadgaon"]
        }
    },
    "Chhatrapati Sambhajinagar": {
        "name": "Chhatrapati Sambhajinagar Division (Marathwada)",
        "regional_university": "Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV), Parbhani",
        "districts": {
            "Chhatrapati Sambhajinagar": ["Chhatrapati Sambhajinagar", "Paithan", "Gangapur", "Vaijapur", "Kannad", "Sillod", "Phulambri", "Khuldabad", "Soegaon"],
            "Jalna": ["Jalna", "Ambad", "Partur", "Bhokardan", "Jafrabad", "Badnapur", "Ghansawangi", "Mantha"],
            "Beed": ["Beed", "Georai", "Majalgaon", "Ambejogai", "Kaij", "Parli", "Ashti", "Patoda", "Wadwani", "Shirur Kasar", "Dharur"],
            "Parbhani": ["Parbhani", "Gangakhed", "Jintur", "Selu", "Manwath", "Pathri", "Sonpeth", "Purna", "Palam"],
            "Hingoli": ["Hingoli", "Basmath", "Kalamnuri", "Sengaon", "Aundha Nagnath"],
            "Nanded": ["Nanded", "Ardhapur", "Mudkhed", "Bhokar", "Biloli", "Deglur", "Mukhed", "Kandhar", "Loha", "Hadgaon", "Kinwat", "Himayatnagar", "Mahoor", "Dharmabad", "Naigaon", "Umri"],
            "Latur": ["Latur", "Ausa", "Nilanga", "Udgir", "Ahmedpur", "Renapur", "Chakur", "Shirur Anantpal", "Deoni", "Jalkot"],
            "Dharashiv": ["Dharashiv", "Tuljapur", "Omerga", "Kalamb", "Bhum", "Paranda", "Washi", "Lohara"]
        }
    },
    "Konkan": {
        "name": "Konkan Division (Coastal Maharashtra)",
        "regional_university": "Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth (BSKKV), Dapoli",
        "districts": {
            "Ratnagiri": ["Ratnagiri", "Chiplun", "Dapoli", "Guhagar", "Khed", "Sangameshwar", "Rajapur", "Lanja", "Mandangad"],
            "Sindhudurg": ["Kudal", "Sawantwadi", "Malvan", "Vengurla", "Kankavli", "Devgad", "Vaibhavwadi", "Dodamarg"],
            "Raigad": ["Alibag", "Panvel", "Pen", "Roha", "Mangaon", "Mahad", "Karjat", "Khalapur", "Murud", "Shrivardhan", "Tala", "Poladpur", "Uran", "Mhasla"],
            "Palghar": ["Palghar", "Dahanu", "Wada", "Jawhar", "Vikramgad", "Mokhada", "Talasari", "Vasai"],
            "Thane": ["Thane", "Kalyan", "Murbad", "Bhiwandi", "Shahapur", "Ambernath", "Ulhasnagar"],
            "Mumbai Suburban": ["Kurla", "Andheri", "Borivali"]
        }
    }
}


def get_all_districts() -> List[str]:
    """Return flat list of all 36 Maharashtra districts."""
    districts = []
    for div in MAHARASHTRA_DIVISIONS.values():
        districts.extend(list(div["districts"].keys()))
    return sorted(list(set(districts)))


def get_division_for_district(district: str) -> str:
    """Find administrative division given a district."""
    d_clean = district.strip().lower()
    for div_name, div_data in MAHARASHTRA_DIVISIONS.items():
        for d in div_data["districts"]:
            if d.lower() == d_clean:
                return div_name
    return "Amravati"  # Default fallback


def get_talukas_for_district(district: str) -> List[str]:
    """Return all talukas for a specific Maharashtra district."""
    d_clean = district.strip().lower()
    for div_data in MAHARASHTRA_DIVISIONS.values():
        for d, talukas in div_data["districts"].items():
            if d.lower() == d_clean:
                return talukas
    return ["Central Taluka"]
