import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';
import { useNavigate } from 'react-router-dom';
import {
  Map as MapIcon, Leaf, Droplets, Thermometer, Wind, AlertTriangle, Layers,
  Loader2, CheckCircle2, Info, Compass, ExternalLink, ShieldAlert, MapPin, Edit3
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../services/api';
import BoundaryEditorModal from '../../components/map/BoundaryEditorModal';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';
import GpsBoundaryModal from '../../components/map/GpsBoundaryModal';
import { Footprints } from 'lucide-react';

// Create SVG-based custom Leaflet icons to eliminate broken default asset paths in Vite
const createFarmMarkerIcon = (isApprox: boolean = false) => {
  const bg = isApprox ? '#B6532A' : '#103D2C';
  const svgHtml = `
    <div style="
      background-color: ${bg};
      width: 32px;
      height: 32px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid white;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        transform: rotate(45deg);
        color: white;
        font-size: 13px;
        font-weight: bold;
        line-height: 1;
      ">📍</div>
    </div>
  `;
  return L.divIcon({
    html: svgHtml,
    className: 'custom-leaflet-farm-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
};

// Component to dynamically re-center map when coordinates change
function ChangeView({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

export default function DigitalTwin() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const navigate = useNavigate();
  const [farmsList, setFarmsList] = useState<any[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<string>('');
  const [farmData, setFarmData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadingFarms, setLoadingFarms] = useState(true);
  const [selectedFieldId, setSelectedFieldId] = useState<string>('all');
  const [activeBaseLayer, setActiveBaseLayer] = useState<'osm' | 'satellite'>('osm');
  const [isBoundaryModalOpen, setIsBoundaryModalOpen] = useState(false);
  const [isGpsModalOpen, setIsGpsModalOpen] = useState(false);

  // Initial load: Fetch farms list
  useEffect(() => {
    loadUserFarms();
  }, []);

  const loadUserFarms = async () => {
    setLoadingFarms(true);
    try {
      const res = await api.getFarms();
      const farms = res?.farms || [];
      setFarmsList(farms);

      if (farms.length > 0) {
        // Preferred ID from localStorage if exists and in farms list, else first farm
        const savedId = localStorage.getItem('kisancare_active_farm_id');
        const defaultFarm = farms.find((f: any) => f.id === savedId) || farms[0];
        setSelectedFarmId(defaultFarm.id);
        fetchFarmDetails(defaultFarm.id);
      } else {
        setLoading(false);
      }
    } catch (e) {
      console.error('Failed to load farms list:', e);
      setLoading(false);
    } finally {
      setLoadingFarms(false);
    }
  };

  const fetchFarmDetails = async (farmId: string) => {
    setLoading(true);
    setSelectedFieldId('all');
    try {
      const res = await api.getFarmDetails(farmId);
      setFarmData(res);
      localStorage.setItem('kisancare_active_farm_id', farmId);
    } catch (e) {
      console.error('Failed to load farm details:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFarm = (farmId: string) => {
    setSelectedFarmId(farmId);
    fetchFarmDetails(farmId);
  };

  // Extract coordinates and determine veracity
  const preciseLat = farmData?.latitude;
  const preciseLon = farmData?.longitude;
  const approxLat = farmData?.approximate_coordinates?.latitude;
  const approxLon = farmData?.approximate_coordinates?.longitude;

  const hasPreciseCoordinates = farmData?.has_precise_coordinates === true && preciseLat != null && preciseLon != null;
  const hasApproxCoordinates = approxLat != null && approxLon != null;

  // Default fallback reference coordinates: Takli Bk village reference (20.918912, 76.982846)
  const mapCenterLat = hasPreciseCoordinates ? preciseLat : (hasApproxCoordinates ? approxLat : 20.918912);
  const mapCenterLon = hasPreciseCoordinates ? preciseLon : (hasApproxCoordinates ? approxLon : 76.982846);
  const isApproximate = !hasPreciseCoordinates;

  const fields = farmData?.fields || [];
  const selectedField = fields.find((f: any) => f.id === selectedFieldId);

  // Tile layer sources and legal attributions
  const tileLayers = {
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    // Esri World Imagery (high-resolution global satellite orthophoto with free public viewing tier)
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }
  };

  const handleNavigateToWeather = () => {
    navigate('/irrigation-climate');
  };

  if (!loading && !loadingFarms && (!farmData || farmsList.length === 0)) {
    return (
      <div className="p-4 lg:p-8 max-w-4xl mx-auto flex flex-col items-center justify-center min-h-[500px] text-center space-y-4">
        <div className="w-16 h-16 bg-[#FBF7EF] rounded-full flex items-center justify-center text-[#103D2C] border border-[#E5DDCF]">
          <MapIcon size={32} />
        </div>
        <h2 className="text-2xl font-serif font-bold text-[#103D2C]">No Farm Profile Found</h2>
        <p className="text-[#292B26]/70 text-sm max-w-md">
          To explore the interactive {t('digitalTwin.title', 'Digital Twin')} map and agro-climatic profile, create your first farm parcel in My Farms.
        </p>
        <button
          onClick={() => navigate('/farm-setup')}
          className="mt-2 px-5 py-2.5 bg-[#103D2C] hover:bg-[#17643E] text-white font-medium rounded-xl text-sm transition-colors cursor-pointer shadow-sm"
        >
          Go to Farm Setup &amp; Create Farm
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto flex flex-col h-full space-y-6">
      <WorkflowStepper currentStageId={1} />

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm {t('digitalTwin.title')}</h1>
            {farmData?.is_mock ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Farm Profile
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                Live Supabase Records
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">
            Geospatial virtual representation for {farmData?.name || 'Pranav Vasu Farm'} ({farmData?.area_acres || 10.0} {farmData?.area_unit || 'acres'} &bull; {farmData?.location || 'Takli Bu, Akola, Maharashtra'}).
          </p>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          {/* Dynamic Farm Selector */}
          {farmsList.length > 0 && (
            <div className="flex items-center gap-1.5 bg-white border border-[#E5DDCF] rounded-lg px-2.5 py-1 text-xs">
              <span className="text-[#292B26]/60 font-medium">Farm:</span>
              <select
                value={selectedFarmId}
                onChange={(e) => handleSelectFarm(e.target.value)}
                className="bg-transparent font-bold text-[#103D2C] outline-none cursor-pointer"
              >
                {farmsList.map((f: any) => (
                  <option key={f.id} value={f.id}>
                    {f.farm_name} ({f.total_area} {f.area_unit})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Boundary Action Buttons */}
          {farmData && (
            <>
              <button
                onClick={() => setIsBoundaryModalOpen(true)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] border border-[#E5DDCF] rounded-lg text-xs font-semibold shadow-xs cursor-pointer transition-colors"
                title="Draw parcel boundaries manually on the interactive map"
              >
                <Compass size={14} />
                <span>Map Boundary</span>
              </button>

              <button
                onClick={() => setIsGpsModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#17643E] hover:bg-[#103D2C] text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer transition-colors"
                title="Walk the field perimeter with your mobile GPS"
              >
                <Footprints size={14} />
                <span>Walk Farm Boundary</span>
              </button>
            </>
          )}

          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value)}
            className="border border-[#E5DDCF] bg-white rounded-lg px-3 py-2 text-xs font-medium text-[#103D2C] outline-none shadow-xs cursor-pointer"
          >
            <option value="all">All Fields (Overview)</option>
            {fields.map((f: any) => (
              <option key={f.id} value={f.id}>
                {f.name} ({f.crop} - {f.area} {f.area_unit})
              </option>
            ))}
          </select>

          {/* Map Base Tile Switcher */}
          <div className="flex rounded-lg border border-[#E5DDCF] bg-[#FBF7EF] p-0.5 text-xs">
            <button
              onClick={() => setActiveBaseLayer('osm')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${activeBaseLayer === 'osm' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
            >
              Standard Map
            </button>
            <button
              onClick={() => setActiveBaseLayer('satellite')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${activeBaseLayer === 'satellite' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
            >
              Satellite
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
        {/* Map View (Spans 3 cols) */}
        <div className="lg:col-span-3 bg-white rounded-2xl border border-[#E5DDCF] overflow-hidden shadow-sm relative min-h-[540px] flex flex-col">
          {loading ? (
            <div className="absolute inset-0 z-20 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-[#103D2C] mb-2" />
              <span className="text-xs font-medium text-[#292B26]/70">Loading Farm {t('digitalTwin.title')} Map...</span>
            </div>
          ) : null}

          {/* Top Notice: Truth in Geography status banner */}
          <div className="bg-[#FBF7EF] border-b border-[#E5DDCF] px-4 py-2.5 text-xs text-[#292B26] flex flex-col sm:flex-row sm:items-center justify-between gap-2 z-10">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[#B6532A] shrink-0" />
              <span>
                {isApproximate ? (
                  <>
                    <strong>Location Status:</strong> Approximate village-level reference (
                    {farmData?.location || 'Takli Bu, Akola'}). Specific on-farm pin not yet GPS calibrated.
                  </>
                ) : (
                  <>
                    <strong>Location Status:</strong> Verified on-farm GPS coordinates ({mapCenterLat.toFixed(4)}, {mapCenterLon.toFixed(4)}).
                  </>
                )}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="bg-amber-100 text-amber-900 border border-amber-300 font-semibold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider">
                Field boundary survey pending
              </span>
            </div>
          </div>

          {/* Interactive Leaflet Map Container */}
          <div className="relative flex-1 w-full min-h-[480px]">
            <MapContainer
              center={[mapCenterLat, mapCenterLon]}
              zoom={isApproximate ? 13 : 15}
              scrollWheelZoom={false}
              className="w-full h-full min-h-[480px]"
              style={{ background: '#f2f0eb' }}
            >
              <ChangeView center={[mapCenterLat, mapCenterLon]} zoom={isApproximate ? 13 : 15} />

              <TileLayer
                url={tileLayers[activeBaseLayer].url}
                attribution={tileLayers[activeBaseLayer].attribution}
                maxZoom={19}
              />

              {/* Verified or Approximate Farm Settlement Marker */}
              <Marker
                position={[mapCenterLat, mapCenterLon]}
                icon={createFarmMarkerIcon(isApproximate)}
              >
                <Popup className="custom-farm-popup">
                  <div className="p-1 space-y-1.5 text-xs">
                    <div className="font-bold text-[#103D2C] text-sm">
                      {farmData?.name || 'Pranav Vasu Farm'}
                    </div>
                    <div className="text-[#292B26]/70">
                      <strong>Location:</strong> {farmData?.location || 'Takli Bu, Akola, Maharashtra'}
                    </div>
                    <div className="text-[#292B26]/70">
                      <strong>Total Area:</strong> {farmData?.area_acres || 10.0} {farmData?.area_unit || 'acres'}
                    </div>
                    {isApproximate && (
                      <div className="bg-amber-50 text-amber-900 p-1.5 rounded border border-amber-200 text-[10px]">
                        📍 Placed at village-level settlement centroid. Not an official field survey.
                      </div>
                    )}
                    <button
                      onClick={handleNavigateToWeather}
                      className="mt-2 w-full flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-[#103D2C] hover:bg-[#17643E] text-white font-medium rounded-lg text-xs transition-colors"
                    >
                      <span>View Live Weather &amp; Irrigation</span>
                      <ExternalLink size={12} />
                    </button>
                  </div>
                </Popup>
              </Marker>

              {/* Render verified field polygons only when real GeoJSON exists */}
              {fields.map((fld: any) => {
                if (fld.geojson_geometry && fld.geojson_geometry.coordinates) {
                  // Transform GeoJSON [lon, lat] to Leaflet [lat, lon]
                  const rawCoords = fld.geojson_geometry.coordinates[0];
                  const leafletPositions = rawCoords.map((coordPair: [number, number]) => [coordPair[1], coordPair[0]]);
                  return (
                    <Polygon
                      key={fld.id}
                      positions={leafletPositions}
                      pathOptions={{
                        color: selectedFieldId === fld.id ? '#FFFFFF' : '#17643E',
                        fillColor: '#17643E',
                        fillOpacity: 0.4,
                        weight: selectedFieldId === fld.id ? 4 : 2
                      }}
                    >
                      <Popup>
                        <div className="text-xs">
                          <strong>{fld.name}</strong> ({fld.area} {fld.area_unit})<br />
                          Crop: {fld.crop} ({fld.stage})
                        </div>
                      </Popup>
                    </Polygon>
                  );
                }
                return null;
              })}
            </MapContainer>

            {/* Overlaid Field Boundary Notice */}
            <div className="absolute bottom-6 left-4 bg-white/95 backdrop-blur-xs text-[#292B26] p-3 rounded-xl border border-[#E5DDCF] shadow-md text-xs max-w-sm z-[1000]">
              <div className="flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-[#B6532A] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-[#103D2C] block">Cadastral Boundary Notice</span>
                  <span className="text-[11px] text-[#292B26]/75">
                    Field parcel polygons are not fabricated. Once farm boundaries are mapped via GPS walking, surveyed parcels will render automatically.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Info Panels */}
        <div className="space-y-6">
          {/* Field Details Card */}
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5 space-y-4">
            <div className="border-b border-[#E5DDCF] pb-2 flex justify-between items-center">
              <h3 className="font-bold text-[#103D2C] text-sm">
                {selectedField ? selectedField.name : 'All Fields (Farm Overview)'}
              </h3>
              <span className="text-[10px] text-[#292B26]/50">
                {selectedField ? `${selectedField.area} ${selectedField.area_unit}` : `${farmData?.area_acres || 10.0} ${farmData?.area_unit || 'ac'} Total`}
              </span>
            </div>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-[#17643E]" />
              </div>
            ) : selectedField ? (
              <div className="space-y-3.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Cultivated Crop</span>
                  <span className="font-bold text-[#103D2C]">
                    {selectedField.crop} <span className="font-normal text-[11px] text-[#292B26]/60">({selectedField.variety})</span>
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Phenological Stage</span>
                  <span className="font-semibold text-[#17643E] bg-[#A8C69A]/20 px-2.5 py-0.5 rounded-full text-[11px]">
                    {selectedField.stage}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Boundary Status</span>
                  <span className="font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded text-[11px]">
                    {selectedField.boundaries_mapped ? 'GPS Surveyed' : 'Survey Pending'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Soil Chemistry (pH)</span>
                  <span className="font-bold text-[#103D2C]">{farmData?.state?.soil_ph ?? 8.05} (Alkaline)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Soil Type</span>
                  <span className="font-medium text-[#292B26]">{farmData?.state?.soil_type || 'Black cotton soil'}</span>
                </div>

                <div className="mt-4 bg-[#FBF7EF] p-3.5 rounded-xl border border-[#B6532A]/30 space-y-1.5">
                  <div className="flex items-start gap-1.5">
                    <AlertTriangle size={15} className="text-[#B6532A] shrink-0 mt-0.5" />
                    <h4 className="font-bold text-[#B6532A] text-xs">Drought Stress Advisory</h4>
                  </div>
                  <p className="text-[11px] text-[#292B26]/75 leading-relaxed">
                    Boll development stage requires critical moisture support. Consult the Irrigation engine for scheduled volume.
                  </p>
                </div>
              </div>
            ) : (
              /* All Fields Overview */
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Total Farm Area</span>
                  <span className="font-bold text-[#103D2C]">{farmData?.area_acres || 10.0} Acres</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Cultivated Parcels</span>
                  <span className="font-bold text-[#103D2C]">{farmData?.allocated_acres || 5.0} Acres (2 Parcels)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Unallocated Area</span>
                  <span className="font-bold text-[#292B26]">{farmData?.unallocated_acres || 5.0} Acres</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Primary Soil</span>
                  <span className="font-bold text-[#103D2C]">Black cotton soil (pH 8.05)</span>
                </div>
                <p className="text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF]">
                  Select an individual field from the top dropdown to view parcel-specific phenology.
                </p>
              </div>
            )}
          </div>

          {/* Micro-Climate & WeatherAPI Link Panel */}
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5 space-y-3">
            <div className="border-b border-[#E5DDCF] pb-2 flex justify-between items-center">
              <h3 className="font-bold text-[#103D2C] text-sm">Micro-Climate</h3>
              <span className="text-[10px] text-[#292B26]/50">Akola Station</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Thermometer size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">
                  {farmData?.climate?.temperature ? `${farmData.climate.temperature}°C` : '31.1°C'}
                </div>
                <div className="text-[10px] text-[#292B26]/60">Air Temp</div>
              </div>
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Wind size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">
                  {farmData?.climate?.humidity ? `${farmData.climate.humidity}%` : '43%'}
                </div>
                <div className="text-[10px] text-[#292B26]/60">Rel. Humidity</div>
              </div>
            </div>

            <button
              onClick={handleNavigateToWeather}
              className="w-full mt-2 flex items-center justify-center gap-1.5 px-3 py-2 bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] font-semibold text-xs rounded-xl border border-[#E5DDCF] transition-colors"
            >
              <span>Inspect Full Weather Forecast &amp; ET₀</span>
              <ExternalLink size={13} />
            </button>
          </div>
        </div>
      </div>

      {/* GPS Boundary Walking Modal */}
      {farmData && (
        <GpsBoundaryModal
          isOpen={isGpsModalOpen}
          onClose={() => setIsGpsModalOpen(false)}
          farmId={farmData.farm_id}
          farmName={farmData.name}
          initialCenter={[mapCenterLat, mapCenterLon]}
          isApproximateCenter={isApproximate}
          fields={fields.map((f: any) => ({
            id: f.id,
            name: f.name,
            area: f.area,
            area_unit: f.area_unit,
            crop: f.crop,
            geojson_geometry: f.geojson_geometry,
            boundaries_mapped: f.boundaries_mapped
          }))}
          onSaveSuccess={(updatedField: any) => {
            fetchFarmDetails(farmData.farm_id);
          }}
        />
      )}

      {/* Boundary Mapping Modal */}
      {farmData && (
        <BoundaryEditorModal
          isOpen={isBoundaryModalOpen}
          onClose={() => setIsBoundaryModalOpen(false)}
          farmId={farmData.farm_id}
          farmName={farmData.name}
          initialCenter={[mapCenterLat, mapCenterLon]}
          isApproximateCenter={isApproximate}
          fields={fields.map((f: any) => ({
            id: f.id,
            name: f.name,
            area: f.area,
            area_unit: f.area_unit,
            crop: f.crop,
            geojson_geometry: f.geojson_geometry,
            boundaries_mapped: f.boundaries_mapped
          }))}
          onSaveSuccess={(updatedField: any) => {
            fetchFarmDetails(farmData.farm_id);
          }}
        />
      )}

      <WorkflowFooter
        currentStageNumber={1}
        currentStageName="Farm & Soil Setup"
        completedActionMessage="Digital Twin synchronized with geospatial field boundaries! Next: Evaluate soil nutrient profiles."
        prevStep={{ label: "My Farm Setup", path: "/farm-setup" }}
        nextStep={{
          label: "Soil Health Assessment",
          labelMr: "माती परीक्षण",
          path: "/soil",
          description: "Evaluate NPK & pH records for your fields"
        }}
        alternativeNextStep={{
          label: "Crop Intelligence",
          path: "/crop-recommendation"
        }}
      />
    </div>
  );
}
