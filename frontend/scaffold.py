import os
from pathlib import Path

BASE_DIR = Path("c:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/frontend/src")

directories = [
    "components/layout",
    "components/common",
    "components/charts",
    "screens/Auth",
    "screens/Dashboard",
    "screens/FarmSetup",
    "screens/DigitalTwin",
    "screens/CropRecommendation",
    "screens/CropComparison",
    "screens/WhatIfSimulator",
    "screens/AiRecommendation",
    "screens/SoilIntelligence",
    "screens/DiseaseDetection",
    "screens/IrrigationClimate",
    "screens/FarmEconomics",
    "screens/MarketIntelligence",
    "screens/FarmMemory",
    "screens/Copilot",
    "screens/Settings",
    "screens/GovernmentSchemes",
    "screens/Documents",
]

for d in directories:
    os.makedirs(BASE_DIR / d, exist_ok=True)

# Generate basic files
pages = [
    "Auth/Login",
    "Dashboard/Dashboard",
    "FarmSetup/FarmSetup",
    "DigitalTwin/DigitalTwin",
    "CropRecommendation/CropRecommendation",
    "CropComparison/CropComparison",
    "WhatIfSimulator/WhatIfSimulator",
    "AiRecommendation/AiRecommendation",
    "SoilIntelligence/SoilIntelligence",
    "DiseaseDetection/DiseaseDetection",
    "IrrigationClimate/IrrigationClimate",
    "FarmEconomics/FarmEconomics",
    "MarketIntelligence/MarketIntelligence",
    "FarmMemory/FarmMemory",
    "Copilot/Copilot",
    "Settings/Settings",
    "GovernmentSchemes/GovernmentSchemes",
    "Documents/Documents",
]

for page in pages:
    page_name = page.split("/")[-1]
    file_path = BASE_DIR / "screens" / f"{page}.tsx"
    if not file_path.exists():
        with open(file_path, "w") as f:
            f.write(f'''import React from "react";\n\nconst {page_name} = () => {{\n  return (\n    <div className="p-6">\n      <h1 className="text-2xl font-serif text-[#103D2C]">{page_name}</h1>\n      <p className="mt-4 text-gray-600">This feature is under construction.</p>\n    </div>\n  );\n}};\n\nexport default {page_name};\n''')

print("Scaffold complete.")
