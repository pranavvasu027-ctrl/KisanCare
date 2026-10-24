/**
 * Translation helper for dynamic AI, OCR, and agronomic outputs.
 * Preserves numeric values, laboratory IDs, scientific references, and coordinates
 * while providing accurate Marathi and Hindi translations for recommendations,
 * advisory guidance, weather conditions, and diagnostic status messages.
 */

const DICTIONARY: Record<string, { mr: string; hi: string }> = {
  // Common Errors & System States
  'ML service is unavailable': { mr: 'ML सेवा उपलब्ध नाही', hi: 'ML सेवा उपलब्ध नहीं है' },
  'Model Request Error': { mr: 'मॉडेल विनंती त्रुटी', hi: 'मॉडल अनुरोध त्रुटि' },
  'Failed to fetch recommendations': { mr: 'शिफारसी मिळवण्यात अयशस्वी', hi: 'सिफारिशें प्राप्त करने में विफल' },
  'Network Error': { mr: 'नेटवर्क त्रुटी', hi: 'नेटवर्क त्रुटि' },

  // Soil Nutrient Issues & Statuses
  'Low Nitrogen': { mr: 'कमी नायट्रोजन (नत्र)', hi: 'कम नाइट्रोजन' },
  'Medium Nitrogen': { mr: 'मध्यम नायट्रोजन (नत्र)', hi: 'मध्यम नाइट्रोजन' },
  'High Nitrogen': { mr: 'जास्त नायट्रोजन (नत्र)', hi: 'अधिक नाइट्रोजन' },
  'Low Phosphorus': { mr: 'कमी फॉस्फरस (स्फुरद)', hi: 'कम फास्फोरस' },
  'Medium Phosphorus': { mr: 'मध्यम फॉस्फरस (स्फुरद)', hi: 'मध्यम फास्फोरस' },
  'High Phosphorus': { mr: 'जास्त फॉस्फरस (स्फुरद)', hi: 'अधिक फास्फोरस' },
  'Low Potassium': { mr: 'कमी पोटॅशियम (पालाश)', hi: 'कम पोटेशियम' },
  'Medium Potassium': { mr: 'मध्यम पोटॅशियम (पालाश)', hi: 'मध्यम पोटेशियम' },
  'High Potassium': { mr: 'जास्त पोटॅशियम (पालाश)', hi: 'अधिक पोटेशियम' },
  'Deficient': { mr: 'अपुऱ्या प्रमाणात / कमतरता', hi: 'कमी / अपर्याप्त' },
  'Sufficient': { mr: 'पुरेशा प्रमाणात', hi: 'पर्याप्त मात्रा' },
  'Surplus': { mr: 'जास्त प्रमाणात / अतिरिक्त', hi: 'अतिरिक्त मात्रा' },
  'Optimal': { mr: 'योग्य समतोल', hi: 'उत्कृष्ट संतुलन' },

  // Crop Names
  'Cotton': { mr: 'कापूस', hi: 'कपास' },
  'Soybean': { mr: 'सोयाबीन', hi: 'सोयाबीन' },
  'Wheat': { mr: 'गहू', hi: 'गेहूं' },
  'Rice': { mr: 'भात (तांदूळ)', hi: 'धान (चावल)' },
  'Maize': { mr: 'मका', hi: 'मक्का' },
  'Tomato': { mr: 'टोमॅटो', hi: 'टमाटर' },
  'Pigeonpeas': { mr: 'तूर', hi: 'अरहर (तूर)' },
  'Chickpea': { mr: 'हरभरा (चना)', hi: 'चना' },
  'Groundnut': { mr: 'भुईमूग', hi: 'मूंगफली' },
  'Sugarcane': { mr: 'ऊस', hi: 'गन्ना' },
  'Onion': { mr: 'कांदा', hi: 'प्याज' },
  'Potato': { mr: 'बटाटा', hi: 'आलू' },

  // Weather Conditions
  'Partly Cloudy': { mr: 'अंशतः ढगाळ', hi: 'आंशिक रूप से बादल' },
  'Sunny': { mr: 'सूर्यप्रकाश / निरभ्र', hi: 'धूप / साफ़' },
  'Clear': { mr: 'निरभ्र आकाश', hi: 'साफ़ आसमान' },
  'Rainy': { mr: 'पावसाळी', hi: 'बरसात' },
  'Thunderstorm': { mr: 'वादळी पाऊस', hi: 'तूफानी बारिश' },
  'Overcast': { mr: 'पूर्ण ढगाळ', hi: 'बादल छाए रहेंगे' },
  'Mist': { mr: 'धुके', hi: 'कोहरा' },
  'Fog': { mr: 'दाट धुके', hi: 'घना कोहरा' },

  // Farm Alerts & Statuses
  'Water Stress in Field A': { mr: 'शेत A मध्ये पाण्याचा ताण', hi: 'खेत A में जल तनाव' },
  'Critical drought stress at boll development stage in rainfed Cotton parcel': {
    mr: 'कोरडवाहू कापूस पिकामध्ये बोंड विकास अवस्थेत तीव्र पाण्याचा ताण आढळला आहे',
    hi: 'बारानी कपास के डोंडे विकास चरण में गंभीर सूखे का तनाव'
  },
  'Supplementary Irrigation': { mr: 'पूरक सिंचनाची गरज', hi: 'पूरक सिंचाई की आवश्यकता' },
  '100–500m water source available for occasional irrigation': {
    mr: '१००-५०० मीटर अंतरावर उपलब्ध जलस्रोतातून त्वरित हलके सिंचन द्या',
    hi: '१००-५०० मीटर दूरी पर उपलब्ध जल स्रोत से सामयिक सिंचाई करें'
  },
  'Soil Lab Report Pending': { mr: 'माती परीक्षण अहवाल प्रलंबित', hi: 'मृदा परीक्षण रिपोर्ट लंबित' },
  'Reported pH 7.6–8.5 (black cotton soil); NPK lab report pending upload': {
    mr: 'नोंदवलेला सामू ७.६–८.५ (काळी कापसाची जमीन); NPK प्रयोगशाळा अहवाल अपलोड करणे बाकी आहे',
    hi: 'दर्ज पीएच ७.६–८.५ (काली कपास मिट्टी); एनपीके लैब रिपोर्ट अपलोड होना बाकी है'
  },

  // AI Recommendations
  'Supplementary Irrigation for Field A': { mr: 'शेत A साठी पूरक सिंचन', hi: 'खेत A के लिए पूरक सिंचाई' },
  'Cotton is at critical boll development stage with drought stress. Occasional supplementary irrigation from 100–500m source recommended to protect 10 q/ac historical yield benchmark.': {
    mr: 'कापूस बोंड धरण्याच्या नाजूक टप्प्यावर असून पाण्याचा तीव्र ताण आहे. ऐतिहासिक १० क्विंटल/एकर उत्पादन राखण्यासाठी १००-५०० मी. स्रोतातून तातडीने पूरक सिंचन द्यावे.',
    hi: 'कपास डोंडे बनने के महत्वपूर्ण चरण में है और सूखे का तनाव है। १० क्विंटल/एकड़ के ऐतिहासिक पैदावार बेंचमार्क की रक्षा के लिए १००-५०० मीटर स्रोत से पूरक सिंचाई की सिफारिश की जाती है।'
  },

  // Field Demarcation & Unallocated
  '5.0 Acres Strictly Unallocated': { mr: '५.० एकर पूर्णपणे अवर्गीकृत', hi: '५.० एकड़ पूर्णतः अनिर्धारित' },
  'Only 5 of 10 reported acres are allocated (Field A: 3 ac, Field B: 2 ac). Farmer reported 2 locations; field demarcation pending.': {
    mr: '१० पैकी केवळ ५ एकर क्षेत्राचे वाटप झाले आहे (शेत A: ३ एकर, शेत B: २ एकर). शेतकऱ्याने २ ठिकाणे नोंदवली आहेत; सीमांकन प्रलंबित आहे.',
    hi: '१० में से केवल ५ एकड़ का आवंटन किया गया है (खेत A: ३ एकड़, खेत B: २ एकड़)। किसान ने २ स्थानों की रिपोर्ट की है; सीमांकन लंबित है।'
  },

  // Activity Feed
  'Field 1 satellite data updated': { mr: 'शेत १ चा उपग्रह डेटा अद्यतनित झाला', hi: 'खेत १ का सैटेलाइट डेटा अपडेट किया गया' },
  'Soil report added for Field 2': { mr: 'शेत २ साठी माती परीक्षण अहवाल जोडला गेला', hi: 'खेत २ के लिए मिट्टी की रिपोर्ट जोड़ी गई' },

  // Agronomic Status Tiers
  'Good': { mr: 'उत्कृष्ट', hi: 'अच्छा' },
  'Moderate': { mr: 'मध्यम', hi: 'मध्यम' },
  'Low': { mr: 'कमी', hi: 'कम' },
  'High': { mr: 'जास्त', hi: 'अधिक' },
  'Normal': { mr: 'सामान्य', hi: 'सामान्य' },
  'Acidic': { mr: 'आम्लयुक्त', hi: 'अम्लीय' },
  'Alkaline': { mr: 'अल्कलीयुक्त', hi: 'क्षारीय' },
  'Suspect': { mr: 'संशयास्पद', hi: 'संदिग्ध' },
  'Abnormal': { mr: 'असामान्य', hi: 'असामान्य' },
  'On Track': { mr: 'योग्य मार्गावर', hi: 'सही दिशा में' },
  'Water Stress': { mr: 'पाण्याचा ताण', hi: 'जल तनाव' },
  'Few / Small': { mr: 'कमी / लहान', hi: 'कम / छोटे' },
  'Primarily Rainfed': { mr: 'मुख्यतः कोरडवाहू', hi: 'मुख्य रूप से वर्षा आधारित' },
  'Limited / Drought Stressed': { mr: 'मर्यादित / पाण्याचा ताण', hi: 'सीमित / सूखा तनावग्रस्त' },
  'Low to Moderate': { mr: 'कमी ते मध्यम', hi: 'कम से मध्यम' },

  // Crop Phenology
  'Boll Development (Rainfed)': { mr: 'बोंड विकास (कोरडवाहू)', hi: 'डोंडे विकास (बारानी)' },
  'Boll Formation (Rainfed)': { mr: 'बोंड तयार होणे (कोरडवाहू)', hi: 'डोंडे निर्माण (बारानी)' },

  // Post-Harvest & Storage
  'Boll rot & trash contamination during manual picking': {
    mr: 'हस्त वेचणीदरम्यान बोंड सडणे व कचरा मिसळणे',
    hi: 'हाथ से चुनाई के दौरान गेंटी सड़न और कचरा संदूषण'
  },
  'Manual Picking / Cloth Bags': { mr: 'हातवेचणी / कापडी पिशव्या', hi: 'हाथ से चुनाई / कपड़े की थैलियां' },
  'Traditional Gunny Bags': { mr: 'पारंपारिक गोणपाटाची पोती', hi: 'पारंपरिक जूट की बोरियां' },
  'Hermetic Bags': { mr: 'हवाबंद पिशव्या (हर्मेटिक)', hi: 'हवाबंद थैलियां (हर्मेटिक)' },
  'Metal Silo': { mr: 'धातूचे सायलो / कोठी', hi: 'धातु का साइलो / टंकी' },
  'Warehouse/CWC': { mr: 'शासकीय/शास्त्रीय वखार (CWC)', hi: 'वैज्ञानिक गोदाम / सीबीसी' },
  'Sell Now': { mr: 'आता विक्री करा', hi: 'अभी बेचें' },
  'Hold for 7 Days': { mr: '७ दिवस थांबा', hi: '७ दिन प्रतीक्षा करें' },
  'Hold for 14 Days': { mr: '१४ दिवस थांबा', hi: '१४ दिन प्रतीक्षा करें' },

  // Soil Intelligence Scientific & Advisory Statements
  'Soil test values indicate low available nitrogen. Apply nitrogenous fertilizers in split doses.': {
    mr: 'माती परीक्षणानुसार उपलब्ध नत्र कमी आहे. नत्रयुक्त खते विभागून (स्प्लिट डोसेस) द्यावीत.',
    hi: 'मृदा परीक्षण के अनुसार उपलब्ध नाइट्रोजन कम है। नाइट्रोजन युक्त उर्वरक विभाजित मात्रा में दें।'
  },
  'Maintain balanced fertilization with organic manures (FYM/compost) at 5-10 t/ha.': {
    mr: '५ ते १० टन प्रति हेक्टर शेणखत किंवा कंपोस्ट खताचा वापर करून जमिनीचे संतुलन राखा.',
    hi: '५ से १० टन प्रति हेक्टेयर गोबर या कंपोस्ट खाद का उपयोग करके मिट्टी का संतुलन बनाए रखें।'
  },
  'Ensure proper soil moisture before top-dressing urea to minimize volatilization losses.': {
    mr: 'युरिया खताची मात्रा देण्यापूर्वी जमिनीत पुरेसा ओलावा असल्याची खात्री करा, जेणेकरून नत्राचे बाष्पीभवन टाळता येईल.',
    hi: 'यूरिया उर्वरक देने से पहले सुनिश्चित करें कि मिट्टी में पर्याप्त नमी हो, जिससे उड़ने से होने वाले नुकसान से बचा जा सके।'
  },
  'Soil test values indicate medium available phosphorus. Apply recommended basal P2O5 at sowing.': {
    mr: 'माती परीक्षणानुसार उपलब्ध स्फुरद मध्यम आहे. पेरणीच्या वेळी शिफारशीनुसार स्फुरदयुक्त खते द्यावीत.',
    hi: 'मृदा परीक्षण के अनुसार उपलब्ध फास्फोरस मध्यम है। बुवाई के समय अनुशंसित फास्फोरस उर्वरक दें।'
  },
  'Available potassium is high; avoid excessive potassic fertilizers to prevent nutrient imbalance.': {
    mr: 'उपलब्ध पालाशचे प्रमाण पुरेसे/जास्त आहे; पालाशयुक्त खतांचा अनावश्यक वापर टाळावा.',
    hi: 'उपलब्ध पोटेशियम पर्याप्त/अधिक है; पोटाश उर्वरकों का अत्यधिक प्रयोग न करें।'
  },
  'Soil pH is slightly alkaline; avoid liming and monitor micronutrient availability (Zinc/Iron).': {
    mr: 'मातीचा सामू किंचित अल्कधर्मी आहे; चुना देणे टाळा आणि सूक्ष्मद्रव्ये (जस्त/लोह) कमतरतेवर लक्ष ठेवा.',
    hi: 'मृदा पीएच थोड़ा क्षारीय है; चूना न डालें और सूक्ष्म पोषक तत्वों (जिंक/आयरन) की उपलब्धता पर नजर रखें।'
  },
  // Mandi & Market Price Trends
  'Rising': { mr: 'वाढता कल (तेजी)', hi: 'बढ़ती प्रवृत्ति (तेजी)' },
  'Falling': { mr: 'घटता कल (मंदी)', hi: 'घटती प्रवृत्ति (मंदी)' },
  'Stable': { mr: 'स्थिर भाव', hi: 'स्थिर मूल्य' },
  'Volatile': { mr: 'अस्थिर', hi: 'उतार-चढ़ाव' },
  'Bullish': { mr: 'तेजीचा कल', hi: 'तेजी' },
  'Bearish': { mr: 'मंदीचा कल', hi: 'मंदी' },
  'High Demand': { mr: 'उच्च मागणी', hi: 'अधिक मांग' },
  'Moderate Demand': { mr: 'मध्यम मागणी', hi: 'मध्यम मांग' },
  'Low Demand': { mr: 'कमी मागणी', hi: 'कम मांग' },

  // Additional Weather Conditions
  'Drizzle': { mr: 'रिमझिम पाऊस', hi: 'बूंदाबांदी' },
  'Haze': { mr: 'धुरकट हवामान', hi: 'धुंध' },
  'Scattered Clouds': { mr: 'विखुरलेले ढग', hi: 'छिटपुट बादल' },
  'Heavy Rain': { mr: 'मुसळधार पाऊस', hi: 'भारी बारिश' },

  // Crop Diseases & Pathological Conditions
  'Early Blight': { mr: 'लवकर येणारा करपा', hi: 'अगेती झुलसा' },
  'Late Blight': { mr: 'उशिरा येणारा करपा', hi: 'पछेती झुलसा' },
  'Leaf Spot': { mr: 'पानावरील ठिपके (टिक्का)', hi: 'पत्ती धब्बा' },
  'Powdery Mildew': { mr: 'भुरी रोग', hi: 'चूर्णिल आसिता (पाउडरी मिल्ड्यू)' },
  'Downy Mildew': { mr: 'केवडा रोग', hi: 'मृदुरोमिल आसिता' },
  'Rust': { mr: 'तांबेरा रोग', hi: 'गेरुआ / रतुआ' },
  'Bacterial Blight': { mr: 'जिवाणूजन्य करपा', hi: 'जीवाणु झुलसा' },
  'Yellow Mosaic Virus': { mr: 'पिवळा मोझॅक विषाणू', hi: 'पीला मोज़ेक वायरस' },
  'Anthracnose': { mr: 'अँथ्रॅकनोज / काळा ठिपका', hi: 'एंथ्रेक्नोज' },
  'Healthy': { mr: 'निरोगी / रोगमुक्त', hi: 'स्वस्थ / रोगमुक्त' },
  'Stem Rot': { mr: 'खोड कुज', hi: 'तना सड़न' },
  'Root Rot': { mr: 'मूळ कुज', hi: 'जड़ सड़न' },
  'Cercospora Leaf Spot': { mr: 'सार्कोस्पोरा पानांवरील ठिपके', hi: 'सर्कोस्पोरा पत्ती धब्बा' },
  'Target Spot': { mr: 'टार्गेट स्पॉट', hi: 'टारगेट स्पॉट' },
  'Septoria Brown Spot': { mr: 'सेप्टोरिया तांबूस ठिपका', hi: 'सेप्टोरिया भूरा धब्बा' },
  'Frogeye Leaf Spot': { mr: 'फ्रॉग-आय पानांवरील ठिपके', hi: 'फ्रॉग-आई पत्ती धब्बा' },
  'Charcoal Rot': { mr: 'चारकोल रॉट / कोरडी खोडकुज', hi: 'चारकोल सड़न' },
  'Sudden Death Syndrome': { mr: 'सडन डेथ सिंड्रोम (अचानक वाळणे)', hi: 'आकस्मिक मृत्यु सिंड्रोम' },
  'Soybean Rust': { mr: 'सोयाबीन तांबेरा', hi: 'सोयाबीन रतुआ' },

  // Commercial Fertilizers & Application Stages
  'Urea': { mr: 'युरिया', hi: 'यूरिया' },
  'DAP': { mr: 'डीएपी (DAP)', hi: 'डीएपी (DAP)' },
  'MOP': { mr: 'एमओपी / म्युरिएट ऑफ पोटॅश', hi: 'एमओपी / म्यूरेट ऑफ पोटाश' },
  'NPK': { mr: 'एनपीके (NPK)', hi: 'एनपीके (NPK)' },
  'Single Super Phosphate (SSP)': { mr: 'सिंगल सुपर फॉस्फेट (SSP)', hi: 'सिंगल सुपर फॉस्फेट (SSP)' },
  'Zinc Sulphate': { mr: 'झिंक सल्फेट (जस्त)', hi: 'जिंक सल्फेट' },
  'Ferrous Sulphate': { mr: 'फेरस सल्फेट (हिरकास)', hi: 'फेरस सल्फेट' },
  'Basal Application': { mr: 'पेरणीच्या वेळेची खतमात्रा (बेसल डोस)', hi: 'बुवाई के समय की खुराक (बेसल डोज़)' },
  'Top Dressing': { mr: 'उभ्या पिकात वरून खत देणे (टॉप ड्रेसिंग)', hi: 'खड़ी फसल में ऊपर से देना (टॉप ड्रेसिंग)' },
  'Foliar Spray': { mr: 'पानांवर फवारणी', hi: 'पर्ण छिड़काव' },
  'Split Dose': { mr: 'विभागून खत देणे', hi: 'विभाजित खुराक' },

  // Agricultural Equipment & Rental Categories
  'Tractor': { mr: 'ट्रॅक्टर', hi: 'ट्रैक्टर' },
  'Harvester': { mr: 'हार्वेस्टर / कापणी यंत्र', hi: 'हार्वेस्टर / कटाई मशीन' },
  'Rotavator': { mr: 'रोटाव्हेटर', hi: 'रोटावेटर' },
  'Cultivator': { mr: 'कल्टिव्हेटर / नांगर', hi: 'कल्टीवेटर' },
  'Boom Sprayer': { mr: 'बूम स्प्रेअर / फवारणी यंत्र', hi: 'बूम स्प्रेयर' },
  'Seed Drill': { mr: 'पेरणी यंत्र (सीड ड्रिल)', hi: 'सीड ड्रिल (बुवाई मशीन)' },
  'Drone': { mr: 'कृषी ड्रोन', hi: 'कृषि ड्रोन' },
  'Combine Harvester': { mr: 'कम्बाइन हार्वेस्टर', hi: 'कंबाइन हार्वेस्टर' },
  'Transport Truck': { mr: 'वाहतूक ट्रक', hi: 'परिवहन ट्रक' },
  'Pick-up Van': { mr: 'पिकअप व्हॅन', hi: 'पिकअप वैन' },
  'Farm Labour Crew': { mr: 'शेतमजूर टोळी', hi: 'श्रमिक दल' },
  'Agricultural Specialist': { mr: 'कृषी तज्ञ', hi: 'कृषि विशेषज्ञ' },
  'Per Hour': { mr: 'प्रति तास', hi: 'प्रति घंटा' },
  'Per Day': { mr: 'प्रति दिवस', hi: 'प्रति दिन' },
  'Per Acre': { mr: 'प्रति एकर', hi: 'प्रति एकड़' },
  'Available': { mr: 'उपलब्ध', hi: 'उपलब्ध' },
  'Booked': { mr: 'आरक्षित', hi: 'आरक्षित' },
  'Pending': { mr: 'प्रलंबित', hi: 'लंबित' },
  'Confirmed': { mr: 'निश्चित', hi: 'पुष्टि हो चुकी' },
  'Active': { mr: 'सक्रिय', hi: 'सक्रिय' },
  'Completed': { mr: 'पूर्ण झाले', hi: 'पूर्ण' },
  'Cancelled': { mr: 'रद्द केले', hi: 'रद्द' },

};

/**
 * Translates a dynamic string based on the active language.
 * Falls back gracefully to original text if language is English or string is unknown.
 */
export function translateDynamic(text: string | null | undefined, lang: string): string {
  if (!text) return '';
  if (lang === 'en') return text;

  // Exact match
  const entry = DICTIONARY[text];
  if (entry) {
    if (lang === 'mr' && entry.mr) return entry.mr;
    if (lang === 'hi' && entry.hi) return entry.hi;
  }

  // Trimmed match
  const trimmed = text.trim();
  const trimmedEntry = DICTIONARY[trimmed];
  if (trimmedEntry) {
    if (lang === 'mr' && trimmedEntry.mr) return trimmedEntry.mr;
    if (lang === 'hi' && trimmedEntry.hi) return trimmedEntry.hi;
  }

  // Prefix matching for Model Request Error
  if (trimmed.startsWith('Model Request Error:')) {
    const detail = trimmed.replace('Model Request Error:', '').trim();
    const translatedDetail = translateDynamic(detail, lang);
    if (lang === 'mr') {
      return `मॉडेल विनंती त्रुटी: ${translatedDetail}`;
    }
    if (lang === 'hi') {
      return `मॉडल अनुरोध त्रुटि: ${translatedDetail}`;
    }
  }

  // Prefix matching for Weather Service Notice
  if (trimmed.startsWith('Weather Service Notice:')) {
    const detail = trimmed.replace('Weather Service Notice:', '').trim();
    const translatedDetail = translateDynamic(detail, lang);
    if (lang === 'mr') {
      return `हवामान सेवा सूचना: ${translatedDetail}`;
    }
    if (lang === 'hi') {
      return `मौसम सेवा सूचना: ${translatedDetail}`;
    }
  }

  // Specific dynamic pattern: "Apply balanced NPK fertilizer calibrated for <Crop>."
  const npkMatch = trimmed.match(/^Apply balanced NPK fertilizer calibrated for (.+)\.?$/i);
  if (npkMatch) {
    const rawCrop = npkMatch[1].replace('.', '').trim();
    const translatedCrop = translateDynamic(rawCrop, lang);
    if (lang === 'mr') {
      return `${translatedCrop} पिकासाठी शिफारशीनुसार संतुलित NPK खताचा वापर करा.`;
    }
    if (lang === 'hi') {
      return `${translatedCrop} फसल के लिए अनुशंसित संतुलित NPK उर्वरक का प्रयोग करें।`;
    }
  }

  // Safe fallback to English text
  return text;
}
