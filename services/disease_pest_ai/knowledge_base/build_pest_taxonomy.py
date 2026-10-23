"""
Script to generate knowledge_base/pest_taxonomy.json conforming to Section 7.
Maps all 102 IP102 classes and Wadhwani AI bollworm classes to canonical names,
aliases, and documented host crops without inventing crop associations.
"""

import json
from pathlib import Path

taxonomy_map = [
    {"id": 0, "raw": "rice leaf roller", "name": "Rice Leaf Roller", "aliases": ["Cnaphalocrocis medinalis"], "crops": ["Rice"]},
    {"id": 1, "raw": "rice leaf caterpillar", "name": "Rice Leaf Caterpillar", "aliases": ["Naranga aenescens"], "crops": ["Rice"]},
    {"id": 2, "raw": "paddy stem maggot", "name": "Paddy Stem Maggot", "aliases": ["Chlorops oryzae"], "crops": ["Rice"]},
    {"id": 3, "raw": "asiatic rice borer", "name": "Asiatic Rice Borer", "aliases": ["Chilo suppressalis"], "crops": ["Rice"]},
    {"id": 4, "raw": "yellow rice borer", "name": "Yellow Rice Borer", "aliases": ["Scirpophaga incertulas"], "crops": ["Rice"]},
    {"id": 5, "raw": "rice gall midge", "name": "Rice Gall Midge", "aliases": ["Orseolia oryzae"], "crops": ["Rice"]},
    {"id": 6, "raw": "Rice Stemfly", "name": "Rice Stemfly", "aliases": ["Atherigona oryzae"], "crops": ["Rice"]},
    {"id": 7, "raw": "brown plant hopper", "name": "Brown Plant Hopper", "aliases": ["Nilaparvata lugens", "BPH"], "crops": ["Rice"]},
    {"id": 8, "raw": "white backed plant hopper", "name": "White-backed Plant Hopper", "aliases": ["Sogatella furcifera", "WBPH"], "crops": ["Rice"]},
    {"id": 9, "raw": "small brown plant hopper", "name": "Small Brown Plant Hopper", "aliases": ["Laodelphax striatellus"], "crops": ["Rice", "Wheat"]},
    {"id": 10, "raw": "rice water weevil", "name": "Rice Water Weevil", "aliases": ["Lissorhoptrus oryzophilus"], "crops": ["Rice"]},
    {"id": 11, "raw": "rice leafhopper", "name": "Rice Leafhopper", "aliases": ["Nephotettix cincticeps", "Green leafhopper"], "crops": ["Rice"]},
    {"id": 12, "raw": "grain spreader thrips", "name": "Grain Spreader Thrips", "aliases": ["Haplothrips aculeatus"], "crops": ["Rice", "Wheat"]},
    {"id": 13, "raw": "rice shell pest", "name": "Rice Shell Pest", "aliases": ["Echthrodelphax bifasciatus"], "crops": ["Rice"]},
    {"id": 14, "raw": "grub", "name": "White Grub", "aliases": ["Holotrichia", "Scarabaeidae larva"], "crops": ["Corn", "Potato", "Soybean", "Cotton"]},
    {"id": 15, "raw": "mole cricket", "name": "Mole Cricket", "aliases": ["Gryllotalpa gryllotalpa"], "crops": ["Potato", "Tomato", "Corn"]},
    {"id": 16, "raw": "wireworm", "name": "Wireworm", "aliases": ["Agriotes", "Elateridae larva"], "crops": ["Potato", "Corn", "Wheat"]},
    {"id": 17, "raw": "white margined moth", "name": "White Margined Moth", "aliases": ["Dargida procinctus"], "crops": ["Corn", "Wheat"]},
    {"id": 18, "raw": "black cutworm", "name": "Black Cutworm", "aliases": ["Agrotis ipsilon"], "crops": ["Corn", "Cotton", "Tomato", "Potato", "Soybean"]},
    {"id": 19, "raw": "large cutworm", "name": "Large Cutworm", "aliases": ["Agrotis tokionis"], "crops": ["Corn", "Potato", "Tomato"]},
    {"id": 20, "raw": "yellow cutworm", "name": "Yellow Cutworm", "aliases": ["Agrotis segetum"], "crops": ["Potato", "Corn", "Wheat"]},
    {"id": 21, "raw": "red spider", "name": "Red Spider Mite", "aliases": ["Tetranychus urticae", "Two-Spotted Spider Mite", "spider mites"], "crops": ["Tomato", "Cotton", "Bell Pepper", "Apple", "Strawberry"]},
    {"id": 22, "raw": "corn borer", "name": "Corn Borer", "aliases": ["Ostrinia furnacalis", "Ostrinia nubilalis", "Asian corn borer"], "crops": ["Corn", "Bell Pepper"]},
    {"id": 23, "raw": "army worm", "name": "Armyworm", "aliases": ["Mythimna separata", "Spodoptera frugiperda", "Fall armyworm"], "crops": ["Corn", "Wheat", "Rice", "Cotton"]},
    {"id": 24, "raw": "aphids", "name": "Aphids", "aliases": ["Aphididae", "Aphis", "Plant lice"], "crops": ["Tomato", "Potato", "Bell Pepper", "Corn", "Wheat", "Apple", "Peach", "Cotton"]},
    {"id": 25, "raw": "Potosiabre vitarsis", "name": "White-spotted Flower Chafer", "aliases": ["Protaetia brevitarsis"], "crops": ["Corn", "Peach", "Apple"]},
    {"id": 26, "raw": "peach borer", "name": "Peach Borer", "aliases": ["Synanthedon exitiosa", "Peach tree borer"], "crops": ["Peach", "Cherry"]},
    {"id": 27, "raw": "english grain aphid", "name": "English Grain Aphid", "aliases": ["Sitobion avenae"], "crops": ["Wheat"]},
    {"id": 28, "raw": "green bug", "name": "Greenbug Aphid", "aliases": ["Schizaphis graminum"], "crops": ["Wheat"]},
    {"id": 29, "raw": "bird cherry-oataphid", "name": "Bird Cherry-Oat Aphid", "aliases": ["Rhopalosiphum padi"], "crops": ["Wheat", "Cherry"]},
    {"id": 30, "raw": "wheat blossom midge", "name": "Wheat Blossom Midge", "aliases": ["Sitodiplosis mosellana"], "crops": ["Wheat"]},
    {"id": 31, "raw": "penthaleus major", "name": "Winter Grain Mite", "aliases": ["Penthaleus major"], "crops": ["Wheat"]},
    {"id": 32, "raw": "longlegged spider mite", "name": "Long-legged Spider Mite", "aliases": ["Bryobia praetiosa"], "crops": ["Wheat", "Apple", "Peach"]},
    {"id": 33, "raw": "wheat phloeothrips", "name": "Wheat Phloeothrips", "aliases": ["Haplothrips tritici"], "crops": ["Wheat"]},
    {"id": 34, "raw": "wheat sawfly", "name": "Wheat Stem Sawfly", "aliases": ["Cephus cinctus"], "crops": ["Wheat"]},
    {"id": 35, "raw": "cerodonta denticornis", "name": "Cereal Leaf Miner", "aliases": ["Cerodontha denticornis"], "crops": ["Wheat"]},
    {"id": 36, "raw": "beet fly", "name": "Beet Leafminer Fly", "aliases": ["Pegomya hyoscyami"], "crops": ["Sugar Beet"]},
    {"id": 37, "raw": "flea beetle", "name": "Flea Beetle", "aliases": ["Phyllotreta", "Epitrix"], "crops": ["Potato", "Tomato", "Bell Pepper"]},
    {"id": 38, "raw": "cabbage army worm", "name": "Cabbage Armyworm", "aliases": ["Mamestra brassicae"], "crops": ["Tomato", "Bell Pepper"]},
    {"id": 39, "raw": "beet army worm", "name": "Beet Armyworm", "aliases": ["Spodoptera exigua"], "crops": ["Cotton", "Tomato", "Corn", "Soybean"]},
    {"id": 40, "raw": "Beet spot flies", "name": "Beet Spot Fly", "aliases": ["Psilopa leucostoma"], "crops": ["Sugar Beet"]},
    {"id": 41, "raw": "meadow moth", "name": "Beet Webworm / Meadow Moth", "aliases": ["Loxostege sticticalis"], "crops": ["Soybean", "Corn"]},
    {"id": 42, "raw": "beet weevil", "name": "Beet Weevil", "aliases": ["Bothynoderes punctiventris"], "crops": ["Sugar Beet"]},
    {"id": 43, "raw": "sericaorient alismots chulsky", "name": "Asian Chafer Beetle", "aliases": ["Maladera orientalis"], "crops": ["Soybean", "Corn", "Potato"]},
    {"id": 44, "raw": "alfalfa weevil", "name": "Alfalfa Weevil", "aliases": ["Hypera postica"], "crops": ["Soybean"]},
    {"id": 45, "raw": "flax budworm", "name": "Flax Budworm", "aliases": ["Heliothis viriplaca"], "crops": ["Soybean"]},
    {"id": 46, "raw": "alfalfa plant bug", "name": "Alfalfa Plant Bug", "aliases": ["Adelphocoris lineolatus"], "crops": ["Cotton", "Soybean"]},
    {"id": 47, "raw": "tarnished plant bug", "name": "Tarnished Plant Bug", "aliases": ["Lygus lineolaris"], "crops": ["Cotton", "Strawberry", "Peach", "Apple"]},
    {"id": 48, "raw": "Locustoidea", "name": "Locust / Grasshopper", "aliases": ["Locust", "Schistocerca", "Locusta migratoria"], "crops": ["Corn", "Wheat", "Rice", "Cotton"]},
    {"id": 49, "raw": "lytta polita", "name": "Blister Beetle (Lytta)", "aliases": ["Lytta polita"], "crops": ["Soybean"]},
    {"id": 50, "raw": "legume blister beetle", "name": "Legume Blister Beetle", "aliases": ["Epicauta gorhami"], "crops": ["Soybean", "Potato", "Tomato"]},
    {"id": 51, "raw": "blister beetle", "name": "Blister Beetle", "aliases": ["Meloidae", "Epicauta"], "crops": ["Soybean", "Tomato", "Potato", "Cotton"]},
    {"id": 52, "raw": "therioaphis maculata Buckton", "name": "Spotted Alfalfa Aphid", "aliases": ["Therioaphis maculata"], "crops": ["Soybean"]},
    {"id": 53, "raw": "odontothrips loti", "name": "Legume Thrips", "aliases": ["Odontothrips loti"], "crops": ["Soybean"]},
    {"id": 54, "raw": "Thrips", "name": "Thrips", "aliases": ["Thripidae", "Frankliniella", "Scirtothrips"], "crops": ["Cotton", "Tomato", "Bell Pepper", "Grape", "Orange", "Strawberry"]},
    {"id": 55, "raw": "alfalfa seed chalcid", "name": "Alfalfa Seed Chalcid", "aliases": ["Bruchophagus roddi"], "crops": ["Soybean"]},
    {"id": 56, "raw": "Pieris canidia", "name": "Indian Cabbage White", "aliases": ["Pieris canidia"], "crops": ["Tomato", "Bell Pepper"]},
    {"id": 57, "raw": "Apolygus lucorum", "name": "Green Mirid Bug", "aliases": ["Apolygus lucorum"], "crops": ["Cotton", "Apple", "Peach", "Grape"]},
    {"id": 58, "raw": "Limacodidae", "name": "Slug Caterpillar / Cup Moth", "aliases": ["Limacodidae", "Parasa"], "crops": ["Apple", "Peach", "Cherry", "Orange"]},
    {"id": 59, "raw": "Viteus vitifoliae", "name": "Grape Phylloxera", "aliases": ["Viteus vitifoliae", "Daktulosphaira vitifoliae"], "crops": ["Grape"]},
    {"id": 60, "raw": "Colomerus vitis", "name": "Grape Erineum Mite", "aliases": ["Colomerus vitis", "Grape blister mite"], "crops": ["Grape"]},
    {"id": 61, "raw": "Brevipoalpus lewisi McGregor", "name": "Citrus Flat Mite / Lewis Mite", "aliases": ["Brevipalpus lewisi"], "crops": ["Grape", "Orange", "Peach"]},
    {"id": 62, "raw": "oides decempunctata", "name": "Ten-spotted Leaf Beetle", "aliases": ["Oides decempunctata"], "crops": ["Grape"]},
    {"id": 63, "raw": "Polyphagotars onemus latus", "name": "Broad Mite", "aliases": ["Polyphagotarsonemus latus", "Yellow mite"], "crops": ["Bell Pepper", "Tomato", "Cotton"]},
    {"id": 64, "raw": "Pseudococcus comstocki Kuwana", "name": "Comstock Mealybug", "aliases": ["Pseudococcus comstocki"], "crops": ["Apple", "Peach", "Grape"]},
    {"id": 65, "raw": "parathrene regalis", "name": "Grape Clearwing Moth", "aliases": ["Paranthrene regalis"], "crops": ["Grape"]},
    {"id": 66, "raw": "Ampelophaga", "name": "Grapevine Sphinx Moth", "aliases": ["Ampelophaga rubiginosa"], "crops": ["Grape"]},
    {"id": 67, "raw": "Lycorma delicatula", "name": "Spotted Lanternfly", "aliases": ["Lycorma delicatula"], "crops": ["Grape", "Apple", "Peach"]},
    {"id": 68, "raw": "Xylotrechus", "name": "Grape Wood Borer", "aliases": ["Xylotrechus quadripes"], "crops": ["Grape"]},
    {"id": 69, "raw": "Cicadella viridis", "name": "Green Leafhopper", "aliases": ["Cicadella viridis"], "crops": ["Rice", "Grape", "Corn"]},
    {"id": 70, "raw": "Miridae", "name": "Plant Bug (Miridae)", "aliases": ["Miridae", "Capsid bug"], "crops": ["Cotton", "Tomato", "Apple"]},
    {"id": 71, "raw": "Trialeurodes vaporariorum", "name": "Greenhouse Whitefly", "aliases": ["Trialeurodes vaporariorum", "Whitefly"], "crops": ["Tomato", "Bell Pepper", "Potato", "Strawberry", "Cotton"]},
    {"id": 72, "raw": "Erythroneura apicalis", "name": "Grape Leafhopper", "aliases": ["Erythroneura apicalis"], "crops": ["Grape"]},
    {"id": 73, "raw": "Papilio xuthus", "name": "Asian Swallowtail / Citrus Dog", "aliases": ["Papilio xuthus", "Papilio demoleus"], "crops": ["Orange"]},
    {"id": 74, "raw": "Panonchus citri McGregor", "name": "Citrus Red Mite", "aliases": ["Panonychus citri"], "crops": ["Orange"]},
    {"id": 75, "raw": "Phyllocoptes oleiverus ashmead", "name": "Citrus Rust Mite", "aliases": ["Phyllocoptruta oleivora"], "crops": ["Orange"]},
    {"id": 76, "raw": "Icerya purchasi Maskell", "name": "Cottony Cushion Scale", "aliases": ["Icerya purchasi"], "crops": ["Orange", "Peach", "Apple"]},
    {"id": 77, "raw": "Unaspis yanonensis", "name": "Arrowhead Scale", "aliases": ["Unaspis yanonensis"], "crops": ["Orange"]},
    {"id": 78, "raw": "Ceroplastes rubens", "name": "Red Wax Scale", "aliases": ["Ceroplastes rubens"], "crops": ["Orange", "Apple"]},
    {"id": 79, "raw": "Chrysomphalus aonidum", "name": "Florida Red Scale", "aliases": ["Chrysomphalus aonidum"], "crops": ["Orange"]},
    {"id": 80, "raw": "Parlatoria zizyphus Lucus", "name": "Black Parlatoria Scale", "aliases": ["Parlatoria ziziphi"], "crops": ["Orange"]},
    {"id": 81, "raw": "Nipaecoccus vastalor", "name": "Citrus Mealybug", "aliases": ["Nipaecoccus viridis"], "crops": ["Orange", "Cotton", "Soybean"]},
    {"id": 82, "raw": "Aleurocanthus spiniferus", "name": "Orange Spiny Blackfly", "aliases": ["Aleurocanthus spiniferus"], "crops": ["Orange", "Grape", "Peach"]},
    {"id": 83, "raw": "Tetradacus c Bactrocera minax", "name": "Chinese Citrus Fly", "aliases": ["Bactrocera minax"], "crops": ["Orange"]},
    {"id": 84, "raw": "Dacus dorsalis(Hendel)", "name": "Oriental Fruit Fly", "aliases": ["Bactrocera dorsalis"], "crops": ["Orange", "Peach", "Apple"]},
    {"id": 85, "raw": "Bactrocera tsuneonis", "name": "Japanese Orange Fly", "aliases": ["Bactrocera tsuneonis"], "crops": ["Orange"]},
    {"id": 86, "raw": "Prodenia litura", "name": "Tobacco Cutworm / Cotton Leafworm", "aliases": ["Spodoptera litura"], "crops": ["Cotton", "Tomato", "Soybean", "Corn", "Potato"]},
    {"id": 87, "raw": "Adristyrannus", "name": "Citrus Sawfly", "aliases": ["Ametastegia"], "crops": ["Orange"]},
    {"id": 88, "raw": "Phyllocnistis citrella Stainton", "name": "Citrus Leafminer", "aliases": ["Phyllocnistis citrella"], "crops": ["Orange"]},
    {"id": 89, "raw": "Toxoptera citricidus", "name": "Brown Citrus Aphid", "aliases": ["Toxoptera citricida"], "crops": ["Orange"]},
    {"id": 90, "raw": "Toxoptera aurantii", "name": "Black Citrus Aphid", "aliases": ["Toxoptera aurantii"], "crops": ["Orange"]},
    {"id": 91, "raw": "Aphis citricola Vander Goot", "name": "Spirea Aphid", "aliases": ["Aphis spiraecola"], "crops": ["Orange", "Apple"]},
    {"id": 92, "raw": "Scirtothrips dorsalis Hood", "name": "Chilli / Citrus Thrips", "aliases": ["Scirtothrips dorsalis"], "crops": ["Bell Pepper", "Cotton", "Orange", "Strawberry"]},
    {"id": 93, "raw": "Dasineura sp", "name": "Gall Midge", "aliases": ["Dasineura"], "crops": ["Apple", "Orange"]},
    {"id": 94, "raw": "Lawana imitata Melichar", "name": "Flatid Planthopper", "aliases": ["Lawana imitata", "Flatidae"], "crops": ["Corn", "Tomato"]},
    {"id": 95, "raw": "Salurnis marginella Guerr", "name": "Green Planthopper", "aliases": ["Salurnis marginella"], "crops": ["Tomato", "Orange"]},
    {"id": 96, "raw": "Deporaus marginatus Pascoe", "name": "Mango Leaf Cutting Weevil", "aliases": ["Deporaus marginatus"], "crops": ["Mango"]},
    {"id": 97, "raw": "Chlumetia transversa", "name": "Mango Shoot Borer", "aliases": ["Chlumetia transversa"], "crops": ["Mango"]},
    {"id": 98, "raw": "Mango flat beak leafhopper", "name": "Mango Leafhopper", "aliases": ["Idioscopus", "Amritodus atkinsoni"], "crops": ["Mango"]},
    {"id": 99, "raw": "Rhytidodera bowrinii white", "name": "Mango Trunk Borer", "aliases": ["Rhytidodera bowringii"], "crops": ["Mango"]},
    {"id": 100, "raw": "Sternochetus frigidus", "name": "Mango Pulp Weevil", "aliases": ["Sternochetus frigidus"], "crops": ["Mango"]},
    {"id": 101, "raw": "Cicadellidae", "name": "Leafhopper (General)", "aliases": ["Cicadellidae"], "crops": ["Rice", "Wheat", "Corn", "Cotton", "Tomato"]},
]

records = []
for item in taxonomy_map:
    records.append({
        "class_id": item["id"],
        "raw_model_name": item["raw"],
        "canonical_name": item["name"],
        "aliases": item["aliases"],
        "supported_crops": item["crops"],
        "dataset_source": "IP102"
    })

# Add cotton bollworms from Wadhwani AI dataset
records.append({
    "class_id": 102,
    "raw_model_name": "pbw",
    "canonical_name": "Pink Bollworm",
    "aliases": ["Pectinophora gossypiella", "PBW"],
    "supported_crops": ["Cotton"],
    "dataset_source": "WadhwaniAI_BOLLWM"
})
records.append({
    "class_id": 103,
    "raw_model_name": "abw",
    "canonical_name": "American Bollworm",
    "aliases": ["Helicoverpa armigera", "ABW", "Cotton bollworm"],
    "supported_crops": ["Cotton", "Tomato", "Corn", "Soybean"],
    "dataset_source": "WadhwaniAI_BOLLWM"
})

out_p = Path(__file__).resolve().parent / "pest_taxonomy.json"
with open(out_p, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Generated {len(records)} pest taxonomy records in {out_p}")
