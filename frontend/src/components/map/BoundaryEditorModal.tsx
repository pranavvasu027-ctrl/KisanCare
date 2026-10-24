import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polygon, Polyline, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
  X, Save, RotateCcw, Trash2, CheckCircle2, AlertCircle, Info, Layers,
  Compass, ShieldCheck, MapPin, Loader2
} from 'lucide-react';
import { calculateGeodesicAreaM2, convertM2ToUnit, validatePolygonCoordinates } from '../../utils/geoUtils';
import { api } from '../../services/api';

interface BoundaryEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  farmId: string;
  farmName: string;
  initialCenter: [number, number];
  isApproximateCenter: boolean;
  fields: Array<{
    id: string;
    name: string;
    area: number;
    area_unit: string;
    crop?: string;
    geojson_geometry?: any;
    boundaries_mapped?: boolean;
  }>;
  onSaveSuccess: (updatedField: any) => void;
}

// Marker icon for drawing polygon vertices
const createVertexIcon = (index: number, isFirst: boolean = false) => {
  return L.divIcon({
    html: `
      <div style="
        background-color: ${isFirst ? '#B6532A' : '#103D2C'};
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        cursor: grab;
      ">
        ${index + 1}
      </div>
    `,
    className: 'vertex-pin-marker',
    iconSize: [22, 22],
    iconAnchor: [11, 11]
  });
};

// Component to dynamically re-center map
function MapCenterUpdater({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

// Click listener inside MapContainer for drawing
function MapClickHandler({
  onAddPoint,
  isEditing
}: {
  onAddPoint: (lat: number, lon: number) => void;
  isEditing: boolean;
}) {
  useMapEvents({
    click(e) {
      if (isEditing) {
        onAddPoint(e.latlng.lat, e.latlng.lng);
      }
    }
  });
  return null;
}

export default function BoundaryEditorModal({
  isOpen,
  onClose,
  farmId,
  farmName,
  initialCenter,
  isApproximateCenter,
  fields,
  onSaveSuccess
}: BoundaryEditorModalProps) {
  if (!isOpen) return null;

  // Selected Field to map
  const [selectedFieldId, setSelectedFieldId] = useState<string>(
    fields && fields.length > 0 ? fields[0].id : ''
  );

  // Vertices in [lat, lon] format for Leaflet display
  const [vertices, setVertices] = useState<Array<[number, number]>>([]);
  const [isPolygonClosed, setIsPolygonClosed] = useState(false);
  const [history, setHistory] = useState<Array<Array<[number, number]>>>([]);

  // Base tile layer
  const [activeLayer, setActiveLayer] = useState<'osm' | 'satellite'>('osm');

  // Status & Feedback
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'error' | 'success' | 'warn'; msg: string } | null>(null);

  const selectedField = fields.find(f => f.id === selectedFieldId);

  // Initialize or load existing geometry when switching selected field
  useEffect(() => {
    if (selectedField && selectedField.geojson_geometry?.coordinates) {
      const rawRing = selectedField.geojson_geometry.coordinates[0];
      // Convert [lon, lat] GeoJSON to [lat, lon] Leaflet
      const leafletRing = rawRing.map((c: [number, number]) => [c[1], c[0]] as [number, number]);
      // Remove closing point for editable vertices array
      const initialPts = leafletRing.slice(0, leafletRing.length - 1);
      setVertices(initialPts);
      setIsPolygonClosed(true);
      setHistory([]);
    } else {
      setVertices([]);
      setIsPolygonClosed(false);
      setHistory([]);
    }
    setFeedback(null);
  }, [selectedFieldId]);

  // Click handler to append points
  const handleAddPoint = (lat: number, lon: number) => {
    if (isPolygonClosed) return;

    setHistory(prev => [...prev, [...vertices]]);
    setVertices(prev => [...prev, [lat, lon]]);
    setFeedback(null);
  };

  // Drag handler for vertices
  const handleVertexDrag = (index: number, newLat: number, newLon: number) => {
    setVertices(prev => {
      const updated = [...prev];
      updated[index] = [newLat, newLon];
      return updated;
    });
  };

  // Delete specific vertex
  const handleDeleteVertex = (index: number) => {
    setHistory(prev => [...prev, [...vertices]]);
    setVertices(prev => prev.filter((_, i) => i !== index));
    if (vertices.length - 1 < 3) {
      setIsPolygonClosed(false);
    }
  };

  // Undo last action
  const handleUndo = () => {
    if (history.length === 0) return;
    const lastState = history[history.length - 1];
    setVertices(lastState);
    setHistory(history.slice(0, -1));
    if (lastState.length < 3) {
      setIsPolygonClosed(false);
    }
  };

  // Clear draft
  const handleClear = () => {
    setHistory(prev => [...prev, [...vertices]]);
    setVertices([]);
    setIsPolygonClosed(false);
    setFeedback(null);
  };

  // Close polygon
  const handleClosePolygon = () => {
    if (vertices.length < 3) {
      setFeedback({ type: 'warn', msg: 'A closed polygon requires at least 3 corner boundary points.' });
      return;
    }
    setIsPolygonClosed(true);
  };

  // Re-open polygon for further vertex additions
  const handleReopenPolygon = () => {
    setIsPolygonClosed(false);
  };

  // Convert Leaflet [lat, lon] to GeoJSON [lon, lat]
  const geojsonCoords: Array<[number, number]> = vertices.map(([lat, lon]) => [lon, lat]);
  // Calculate geodesic area
  const areaM2 = calculateGeodesicAreaM2(geojsonCoords);
  const calculatedAcres = convertM2ToUnit(areaM2, selectedField?.area_unit || 'acre');

  // Discrepancy warning with declared area
  const declaredArea = selectedField?.area || 0;
  const areaDiff = declaredArea > 0 ? Math.abs(calculatedAcres - declaredArea) : 0;
  const isDiscrepant = declaredArea > 0 && areaDiff > declaredArea * 0.35 && vertices.length >= 3;

  // Validation
  const validation = validatePolygonCoordinates(geojsonCoords);
  const canSave = vertices.length >= 3 && validation.valid && !isSaving;

  // Save handler
  const handleSave = async () => {
    if (!canSave || !selectedField) return;

    // Build standard GeoJSON Polygon format
    // Standard requires closed ring: first point == last point
    const closedRing: Array<[number, number]> = [...geojsonCoords, geojsonCoords[0]];
    const geojsonPolygon = {
      type: 'Polygon',
      coordinates: [closedRing]
    };

    setIsSaving(true);
    setFeedback(null);

    try {
      const roundedArea = Math.round(calculatedAcres * 100) / 100;
      const res = await api.saveFieldBoundary(
        farmId,
        selectedField.id,
        geojsonPolygon,
        roundedArea,
        selectedField.area_unit || 'acre',
        selectedField.name
      );

      setFeedback({
        type: 'success',
        msg: `Parcel boundary successfully saved to Supabase! Measured: ${roundedArea} ${selectedField.area_unit || 'acres'}.`
      });

      onSaveSuccess({
        ...selectedField,
        area: roundedArea,
        geojson_geometry: geojsonPolygon,
        boundaries_mapped: true
      });

      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      console.error('Failed to save boundary:', err);
      setFeedback({
        type: 'error',
        msg: `Failed to save boundary: ${err.message || String(err)}. Your draft is preserved.`
      });
    } finally {
      setIsSaving(false);
    }
  };

  const tileLayers = {
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] bg-black/60 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-5xl rounded-2xl shadow-2xl border border-[#E5DDCF] flex flex-col h-[92vh] max-h-[850px] overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-[#FBF7EF] border-b border-[#E5DDCF] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#103D2C] text-white flex items-center justify-center shadow-xs">
              <MapPin size={18} />
            </div>
            <div>
              <h2 className="text-lg font-serif font-bold text-[#103D2C]">
                Map Farm &amp; Field Boundary
              </h2>
              <p className="text-xs text-[#292B26]/70">
                Farm: <strong>{farmName}</strong> &bull; Click on map to add vertices, drag to adjust.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-[#292B26]/60 hover:text-[#103D2C] hover:bg-[#E5DDCF]/50 rounded-lg transition-colors cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        {/* Toolbar & Selector Bar */}
        <div className="px-6 py-3 bg-white border-b border-[#E5DDCF] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <label className="font-semibold text-[#103D2C]">Select Parcel / Field:</label>
            <select
              value={selectedFieldId}
              onChange={(e) => setSelectedFieldId(e.target.value)}
              className="border border-[#E5DDCF] rounded-lg px-3 py-1.5 bg-[#FBF7EF] font-medium text-[#103D2C] outline-none"
            >
              {fields.map(f => (
                <option key={f.id} value={f.id}>
                  {f.name} ({f.area} {f.area_unit}) {f.boundaries_mapped ? '✓ Mapped' : '• Survey Pending'}
                </option>
              ))}
            </select>
          </div>

          {/* Map Base Tile Switcher */}
          <div className="flex items-center gap-2">
            <span className="text-[#292B26]/60 font-medium">Layer:</span>
            <div className="flex rounded-lg border border-[#E5DDCF] bg-[#FBF7EF] p-0.5">
              <button
                onClick={() => setActiveLayer('osm')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${activeLayer === 'osm' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                  }`}
              >
                Street Map
              </button>
              <button
                onClick={() => setActiveLayer('satellite')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${activeLayer === 'satellite' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                  }`}
              >
                Satellite (Esri)
              </button>
            </div>
          </div>
        </div>

        {/* Main Editor Body: Map + Sidebar */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
          {/* Map Area */}
          <div className="flex-1 relative min-h-[350px]">
            <MapContainer
              center={initialCenter}
              zoom={isApproximateCenter ? 14 : 16}
              scrollWheelZoom={true}
              className="w-full h-full"
              style={{ background: '#f2f0eb' }}
            >
              <MapCenterUpdater center={initialCenter} zoom={isApproximateCenter ? 14 : 16} />
              <MapClickHandler onAddPoint={handleAddPoint} isEditing={!isPolygonClosed} />

              <TileLayer
                url={tileLayers[activeLayer].url}
                attribution={tileLayers[activeLayer].attribution}
                maxZoom={19}
              />

              {/* Render In-Progress Polygon or Polyline */}
              {vertices.length >= 3 && isPolygonClosed ? (
                <Polygon
                  positions={vertices}
                  pathOptions={{
                    color: '#103D2C',
                    fillColor: '#17643E',
                    fillOpacity: 0.35,
                    weight: 3
                  }}
                />
              ) : vertices.length >= 2 ? (
                <Polyline
                  positions={vertices}
                  pathOptions={{
                    color: '#B6532A',
                    dashArray: '6, 6',
                    weight: 2
                  }}
                />
              ) : null}

              {/* Draggable Markers for all vertices */}
              {vertices.map((pt, idx) => (
                <Marker
                  key={`vertex-${idx}-${pt[0]}-${pt[1]}`}
                  position={pt}
                  draggable={true}
                  icon={createVertexIcon(idx, idx === 0)}
                  eventHandlers={{
                    dragend: (e) => {
                      const marker = e.target;
                      const position = marker.getLatLng();
                      handleVertexDrag(idx, position.lat, position.lng);
                    }
                  }}
                />
              ))}
            </MapContainer>

            {/* Instruction Banner at top of map */}
            <div className="absolute top-3 left-3 right-3 sm:left-4 sm:right-auto z-[1000] bg-white/95 backdrop-blur-xs px-3.5 py-2 rounded-xl border border-[#E5DDCF] shadow-md text-xs text-[#292B26] max-w-md">
              <div className="flex items-center gap-2">
                <Info size={15} className="text-[#103D2C] shrink-0" />
                <span>
                  {vertices.length === 0 ? (
                    'Click anywhere on the field parcel perimeter to drop your first vertex pin.'
                  ) : !isPolygonClosed ? (
                    `Vertices: ${vertices.length}. Click to place next point, or click "Close Boundary" when done.`
                  ) : (
                    'Boundary closed! You can drag vertex pins to fine-tune your parcel boundaries.'
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Right Editor Panel */}
          <div className="w-full md:w-80 bg-[#FBF7EF] border-t md:border-t-0 md:border-l border-[#E5DDCF] p-5 flex flex-col justify-between space-y-4 overflow-y-auto">
            <div className="space-y-4">
              {/* Geometry Measurement Card */}
              <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#292B26]/70">Calculated Area</span>
                  <span className="font-bold text-[#103D2C] text-sm">
                    {calculatedAcres.toFixed(2)} {selectedField?.area_unit || 'Acres'}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-[#292B26]/60">
                  <span>Declared Farm Area:</span>
                  <span>{declaredArea} {selectedField?.area_unit || 'Acres'}</span>
                </div>
                <div className="flex justify-between text-xs text-[#292B26]/60">
                  <span>Vertex Count:</span>
                  <span>{vertices.length} Points</span>
                </div>
                <div className="pt-2 border-t border-[#E5DDCF] text-[10px] text-[#292B26]/65 leading-tight">
                  Calculated using WGS84 ellipsoidal geodesics. This polygon is an estimated agricultural management boundary and not an official revenue cadastral survey.
                </div>
              </div>

              {/* Discrepancy warning */}
              {isDiscrepant && (
                <div className="bg-amber-50 border border-amber-300 p-3 rounded-xl text-xs text-amber-900 flex items-start gap-2">
                  <AlertCircle size={16} className="text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Acreage Discrepancy: </span>
                    Measured area ({calculatedAcres.toFixed(2)} ac) differs by more than 35% from declared field area ({declaredArea} ac). Please double-check vertices.
                  </div>
                </div>
              )}

              {/* Status & Feedback message */}
              {feedback && (
                <div className={`p-3 rounded-xl text-xs flex items-start gap-2 ${feedback.type === 'success'
                    ? 'bg-emerald-50 border border-emerald-300 text-emerald-900'
                    : feedback.type === 'error'
                      ? 'bg-red-50 border border-red-300 text-red-900'
                      : 'bg-amber-50 border border-amber-300 text-amber-900'
                  }`}>
                  {feedback.type === 'success' ? (
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle size={16} className="text-red-600 shrink-0 mt-0.5" />
                  )}
                  <span>{feedback.msg}</span>
                </div>
              )}

              {/* Editing Actions */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#103D2C]">Drawing Tools</label>
                <div className="grid grid-cols-2 gap-2">
                  {!isPolygonClosed ? (
                    <button
                      onClick={handleClosePolygon}
                      disabled={vertices.length < 3}
                      className="px-3 py-2 bg-[#17643E] hover:bg-[#103D2C] text-white rounded-lg text-xs font-semibold disabled:opacity-40 cursor-pointer transition-colors"
                    >
                      Close Boundary
                    </button>
                  ) : (
                    <button
                      onClick={handleReopenPolygon}
                      className="px-3 py-2 bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] rounded-lg text-xs font-semibold cursor-pointer transition-colors"
                    >
                      Re-open Polygon
                    </button>
                  )}

                  <button
                    onClick={handleUndo}
                    disabled={history.length === 0}
                    className="flex items-center justify-center gap-1 px-3 py-2 border border-[#E5DDCF] bg-white hover:bg-neutral-50 rounded-lg text-xs font-medium disabled:opacity-40 cursor-pointer transition-colors"
                  >
                    <RotateCcw size={13} />
                    <span>Undo Point</span>
                  </button>
                </div>

                <button
                  onClick={handleClear}
                  disabled={vertices.length === 0}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-2 border border-red-200 text-red-700 bg-red-50/50 hover:bg-red-100/50 rounded-lg text-xs font-medium disabled:opacity-40 cursor-pointer transition-colors"
                >
                  <Trash2 size={13} />
                  <span>Clear Current Draft</span>
                </button>
              </div>

              {/* Vertices List */}
              {vertices.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#292B26]/80 flex justify-between">
                    <span>Vertices ({vertices.length})</span>
                    <span className="text-[10px] text-[#292B26]/50">Lat, Lon</span>
                  </label>
                  <div className="max-h-28 overflow-y-auto space-y-1 pr-1 text-[11px]">
                    {vertices.map((pt, i) => (
                      <div key={i} className="flex items-center justify-between bg-white px-2.5 py-1 rounded-md border border-[#E5DDCF]">
                        <span className="font-mono text-[#103D2C]">
                          P{i + 1}: {pt[0].toFixed(5)}, {pt[1].toFixed(5)}
                        </span>
                        <button
                          onClick={() => handleDeleteVertex(i)}
                          className="text-red-500 hover:text-red-700 ml-1 cursor-pointer"
                          title="Delete Vertex"
                        >
                          &times;
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Commit Actions */}
            <div className="space-y-2 pt-2 border-t border-[#E5DDCF]">
              <button
                onClick={handleSave}
                disabled={!canSave}
                className="w-full py-2.5 px-4 bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-sm disabled:opacity-40 cursor-pointer transition-colors"
              >
                {isSaving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                <span>{isSaving ? 'Saving Boundary...' : 'Save & Confirm Parcel Boundary'}</span>
              </button>

              <button
                onClick={onClose}
                className="w-full py-2 px-4 border border-[#E5DDCF] bg-white hover:bg-neutral-50 text-[#292B26] font-medium rounded-xl text-xs cursor-pointer transition-colors"
              >
                Cancel &amp; Keep Existing
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
