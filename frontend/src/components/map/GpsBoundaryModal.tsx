import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polygon, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
  X, Play, Pause, Square, Save, RotateCcw, Trash2, CheckCircle2,
  AlertCircle, Info, Layers, Compass, ShieldAlert, Navigation, Footprints, Loader2, Edit3
} from 'lucide-react';
import {
  calculateGeodesicAreaM2,
  convertM2ToUnit,
  filterGpsFix,
  validatePolygonCoordinates
} from '../../utils/geoUtils';
import { api } from '../../services/api';

interface GpsPoint {
  lat: number;
  lon: number;
  accuracy: number;
  timestamp: number;
}

interface GpsBoundaryModalProps {
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

// Current walker location marker
const createWalkerIcon = () => {
  return L.divIcon({
    html: `
      <div style="
        background-color: #17643E;
        color: white;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 0 10px rgba(23, 100, 62, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
      ">
        🚶
      </div>
    `,
    className: 'walker-location-marker',
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });
};

// Tracked vertex pin icon
const createVertexIcon = (index: number, isFirst: boolean = false) => {
  return L.divIcon({
    html: `
      <div style="
        background-color: ${isFirst ? '#B6532A' : '#103D2C'};
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
      ">
        ${index + 1}
      </div>
    `,
    className: 'gps-vertex-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
};

function MapAutoCenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

export default function GpsBoundaryModal({
  isOpen,
  onClose,
  farmId,
  farmName,
  initialCenter,
  isApproximateCenter,
  fields,
  onSaveSuccess
}: GpsBoundaryModalProps) {
  if (!isOpen) return null;

  // Selected Field to map
  const [selectedFieldId, setSelectedFieldId] = useState<string>(
    fields && fields.length > 0 ? fields[0].id : ''
  );

  // Recording State: 'idle' | 'recording' | 'paused' | 'review'
  const [recordingState, setRecordingState] = useState<'idle' | 'recording' | 'paused' | 'review'>('idle');

  // Recorded points with accuracy
  const [gpsPoints, setGpsPoints] = useState<GpsPoint[]>([]);
  const [currentFix, setCurrentFix] = useState<GpsPoint | null>(null);

  // Time & Stats
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [activeLayer, setActiveLayer] = useState<'osm' | 'satellite'>('satellite');

  // Feedback, Alerts & Save Status
  const [feedback, setFeedback] = useState<{ type: 'error' | 'success' | 'warn' | 'info'; msg: string } | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Geolocation watch ID ref
  const watchIdRef = useRef<number | null>(null);
  const timerRef = useRef<any>(null);

  const selectedField = fields.find(f => f.id === selectedFieldId);

  // Cleanup watcher and timer on unmount or close
  useEffect(() => {
    return () => {
      stopGpsWatch();
      stopTimer();
    };
  }, []);

  const stopGpsWatch = () => {
    if (watchIdRef.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
  };

  const startTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Start GPS recording
  const handleStartRecording = () => {
    if (!navigator.geolocation) {
      setFeedback({ type: 'error', msg: 'Geolocation is not supported by your browser.' });
      return;
    }

    setFeedback(null);
    setRecordingState('recording');
    startTimer();

    // Start watching position with high accuracy
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const acc = pos.coords.accuracy;
        const ts = pos.timestamp || Date.now();

        const fix: GpsPoint = { lat, lon, accuracy: acc, timestamp: ts };
        setCurrentFix(fix);

        setGpsPoints((prev) => {
          const last = prev[prev.length - 1];
          const timeDelta = last ? (ts - last.timestamp) / 1000 : 0;

          const lastCoord: [number, number] | undefined = last ? [last.lon, last.lat] : undefined;
          const newCoord: [number, number] = [lon, lat];

          // Filter poor accuracy and jumps
          const filterResult = filterGpsFix(newCoord, acc, lastCoord, timeDelta, 35, 2.0, 15);

          if (!filterResult.accept) {
            if (filterResult.isSuspiciousJump) {
              setFeedback({ type: 'warn', msg: `GPS spike detected (${filterResult.reason}). Filtered.` });
            }
            return prev;
          }

          return [...prev, fix];
        });
      },
      (err) => {
        let errDesc = 'Location error occurred.';
        if (err.code === err.PERMISSION_DENIED) {
          errDesc = 'GPS permission was denied in your browser settings. Please grant location access.';
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          errDesc = 'GPS signal unavailable. Ensure location services are turned on.';
        } else if (err.code === err.TIMEOUT) {
          errDesc = 'Location request timed out. Retrying signal...';
        }
        setFeedback({ type: 'error', msg: errDesc });
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 3000
      }
    );
  };

  // Pause recording
  const handlePauseRecording = () => {
    setRecordingState('paused');
    stopTimer();
    stopGpsWatch();
  };

  // Resume recording
  const handleResumeRecording = () => {
    handleStartRecording();
  };

  // Finish walk and transition to review
  const handleFinishRecording = () => {
    stopTimer();
    stopGpsWatch();

    if (gpsPoints.length < 3) {
      setFeedback({
        type: 'warn',
        msg: `Only ${gpsPoints.length} points captured. A parcel boundary requires walking at least 3 distinct boundary points.`
      });
      return;
    }

    setRecordingState('review');
    setFeedback({
      type: 'info',
      msg: 'Boundary walk completed! Review the captured perimeter vertices before saving.'
    });
  };

  // Discard draft
  const handleDiscardDraft = () => {
    stopTimer();
    stopGpsWatch();
    setGpsPoints([]);
    setCurrentFix(null);
    setElapsedSeconds(0);
    setRecordingState('idle');
    setFeedback(null);
  };

  // Vertices for polygon rendering and area calculation: [lat, lon]
  const leafletVertices: Array<[number, number]> = gpsPoints.map(p => [p.lat, p.lon]);
  // GeoJSON format: [lon, lat]
  const geojsonCoords: Array<[number, number]> = gpsPoints.map(p => [p.lon, p.lat]);

  const areaM2 = calculateGeodesicAreaM2(geojsonCoords);
  const calculatedAcres = convertM2ToUnit(areaM2, selectedField?.area_unit || 'acre');

  // Discrepancy warning with declared area
  const declaredArea = selectedField?.area || 0;
  const areaDiff = declaredArea > 0 ? Math.abs(calculatedAcres - declaredArea) : 0;
  const isDiscrepant = declaredArea > 0 && areaDiff > declaredArea * 0.35 && gpsPoints.length >= 3;

  // Save polygon to Supabase
  const handleSaveBoundary = async () => {
    if (gpsPoints.length < 3 || !selectedField) return;

    const validation = validatePolygonCoordinates(geojsonCoords);
    if (!validation.valid) {
      setFeedback({ type: 'error', msg: validation.reason || 'Invalid coordinate values.' });
      return;
    }

    // Build valid closed GeoJSON Polygon
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
        msg: `GPS walked boundary verified and saved to database! Area: ${roundedArea} ${selectedField.area_unit || 'acres'}.`
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
      console.error('Failed to save walked boundary:', err);
      setFeedback({
        type: 'error',
        msg: `Failed to save boundary: ${err.message || String(err)}. Your GPS trace is preserved in memory.`
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

  // Center on current walker fix if available, else initialCenter
  const mapCenter: [number, number] = currentFix ? [currentFix.lat, currentFix.lon] : initialCenter;

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="fixed inset-0 z-[2000] bg-black/60 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-5xl rounded-2xl shadow-2xl border border-[#E5DDCF] flex flex-col h-[92vh] max-h-[850px] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-[#FBF7EF] border-b border-[#E5DDCF] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#17643E] text-white flex items-center justify-center shadow-xs">
              <Footprints size={19} />
            </div>
            <div>
              <h2 className="text-lg font-serif font-bold text-[#103D2C]">
                Walk Farm Boundary (GPS Tracking)
              </h2>
              <p className="text-xs text-[#292B26]/70">
                Farm: <strong>{farmName}</strong> &bull; Walk the perimeter of your field parcel with your mobile device.
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
              disabled={recordingState !== 'idle'}
              onChange={(e) => setSelectedFieldId(e.target.value)}
              className="border border-[#E5DDCF] rounded-lg px-3 py-1.5 bg-[#FBF7EF] font-medium text-[#103D2C] outline-none disabled:opacity-60"
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
                onClick={() => setActiveLayer('satellite')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  activeLayer === 'satellite' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                Satellite (Esri)
              </button>
              <button
                onClick={() => setActiveLayer('osm')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  activeLayer === 'osm' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                Street Map
              </button>
            </div>
          </div>
        </div>

        {/* Main Body */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
          {/* Map */}
          <div className="flex-1 relative min-h-[350px]">
            <MapContainer
              center={mapCenter}
              zoom={17}
              scrollWheelZoom={true}
              className="w-full h-full"
              style={{ background: '#f2f0eb' }}
            >
              <MapAutoCenter center={mapCenter} />

              <TileLayer
                url={tileLayers[activeLayer].url}
                attribution={tileLayers[activeLayer].attribution}
                maxZoom={19}
              />

              {/* Walker current location & accuracy circle */}
              {currentFix && (
                <>
                  <Marker
                    position={[currentFix.lat, currentFix.lon]}
                    icon={createWalkerIcon()}
                  />
                  <Circle
                    center={[currentFix.lat, currentFix.lon]}
                    radius={currentFix.accuracy}
                    pathOptions={{
                      color: currentFix.accuracy <= 10 ? '#17643E' : '#B6532A',
                      fillColor: currentFix.accuracy <= 10 ? '#17643E' : '#B6532A',
                      fillOpacity: 0.15,
                      weight: 1
                    }}
                  />
                </>
              )}

              {/* Recorded Trail */}
              {leafletVertices.length >= 2 && recordingState !== 'review' && (
                <Polyline
                  positions={leafletVertices}
                  pathOptions={{
                    color: '#103D2C',
                    weight: 3,
                    dashArray: '4, 4'
                  }}
                />
              )}

              {/* Closed Polygon on review */}
              {leafletVertices.length >= 3 && recordingState === 'review' && (
                <Polygon
                  positions={leafletVertices}
                  pathOptions={{
                    color: '#103D2C',
                    fillColor: '#17643E',
                    fillOpacity: 0.4,
                    weight: 3
                  }}
                />
              )}

              {/* Vertex pins */}
              {leafletVertices.map((pt, idx) => (
                <Marker
                  key={`gps-pt-${idx}`}
                  position={pt}
                  icon={createVertexIcon(idx, idx === 0)}
                />
              ))}
            </MapContainer>

            {/* In-Map Telemetry Overlay Banner */}
            <div className="absolute top-3 left-3 right-3 sm:left-4 sm:right-auto z-[1000] bg-white/95 backdrop-blur-xs p-3 rounded-xl border border-[#E5DDCF] shadow-md text-xs text-[#292B26] max-w-sm space-y-1.5">
              <div className="flex items-center justify-between font-bold text-[#103D2C]">
                <div className="flex items-center gap-1.5">
                  <Navigation size={14} className={recordingState === 'recording' ? 'animate-pulse text-emerald-600' : 'text-gray-400'} />
                  <span>GPS Status: {recordingState.toUpperCase()}</span>
                </div>
                <span className="font-mono text-xs">{formatTimer(elapsedSeconds)}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-[#E5DDCF]">
                <div>
                  <span className="text-[#292B26]/60">GPS Accuracy:</span>{' '}
                  <strong className={currentFix && currentFix.accuracy <= 10 ? 'text-emerald-700' : 'text-amber-700'}>
                    {currentFix ? `±${Math.round(currentFix.accuracy)}m` : 'Acquiring...'}
                  </strong>
                </div>
                <div>
                  <span className="text-[#292B26]/60">Points:</span>{' '}
                  <strong>{gpsPoints.length}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Right Control Panel */}
          <div className="w-full md:w-80 bg-[#FBF7EF] border-t md:border-t-0 md:border-l border-[#E5DDCF] p-5 flex flex-col justify-between space-y-4 overflow-y-auto">
            <div className="space-y-4">
              {/* Telemetry & Area Stats */}
              <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#292B26]/70">Enclosed Area</span>
                  <span className="font-bold text-[#103D2C] text-sm">
                    {calculatedAcres.toFixed(2)} {selectedField?.area_unit || 'Acres'}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-[#292B26]/60">
                  <span>Declared Farm Area:</span>
                  <span>{declaredArea} {selectedField?.area_unit || 'Acres'}</span>
                </div>
                <div className="flex justify-between text-xs text-[#292B26]/60">
                  <span>Elapsed Walking Time:</span>
                  <span className="font-mono">{formatTimer(elapsedSeconds)}</span>
                </div>
                <div className="flex justify-between text-xs text-[#292B26]/60">
                  <span>Captured Coordinates:</span>
                  <span>{gpsPoints.length} Points</span>
                </div>
                <div className="pt-2 border-t border-[#E5DDCF] text-[10px] text-[#292B26]/65 leading-tight">
                  GPS estimates may be less accurate under heavy tree canopies, near tall buildings, or with weak cellular reception. Not a legally certified land survey.
                </div>
              </div>

              {/* Acreage Discrepancy warning */}
              {isDiscrepant && (
                <div className="bg-amber-50 border border-amber-300 p-3 rounded-xl text-xs text-amber-900 flex items-start gap-2">
                  <AlertCircle size={16} className="text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Acreage Discrepancy: </span>
                    GPS enclosed area ({calculatedAcres.toFixed(2)} ac) differs by more than 35% from declared field area ({declaredArea} ac).
                  </div>
                </div>
              )}

              {/* Feedback messages */}
              {feedback && (
                <div className={`p-3 rounded-xl text-xs flex items-start gap-2 ${
                  feedback.type === 'success'
                    ? 'bg-emerald-50 border border-emerald-300 text-emerald-900'
                    : feedback.type === 'error'
                    ? 'bg-red-50 border border-red-300 text-red-900'
                    : feedback.type === 'warn'
                    ? 'bg-amber-50 border border-amber-300 text-amber-900'
                    : 'bg-blue-50 border border-blue-300 text-blue-900'
                }`}>
                  {feedback.type === 'success' ? (
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle size={16} className="text-red-600 shrink-0 mt-0.5" />
                  )}
                  <span>{feedback.msg}</span>
                </div>
              )}

              {/* Controls */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#103D2C]">Walking Tracker</label>
                {recordingState === 'idle' && (
                  <button
                    onClick={handleStartRecording}
                    className="w-full py-2.5 px-4 bg-[#17643E] hover:bg-[#103D2C] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-colors"
                  >
                    <Play size={15} />
                    <span>Start Walking Perimeter</span>
                  </button>
                )}

                {recordingState === 'recording' && (
                  <div className="space-y-2">
                    <button
                      onClick={handlePauseRecording}
                      className="w-full py-2 px-4 bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] font-semibold rounded-xl text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors"
                    >
                      <Pause size={14} />
                      <span>Pause Walking</span>
                    </button>
                    <button
                      onClick={handleFinishRecording}
                      disabled={gpsPoints.length < 3}
                      className="w-full py-2.5 px-4 bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-xs disabled:opacity-40 cursor-pointer transition-colors"
                    >
                      <Square size={14} />
                      <span>Finish &amp; Close Boundary</span>
                    </button>
                  </div>
                )}

                {recordingState === 'paused' && (
                  <div className="space-y-2">
                    <button
                      onClick={handleResumeRecording}
                      className="w-full py-2 px-4 bg-[#17643E] hover:bg-[#103D2C] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors"
                    >
                      <Play size={14} />
                      <span>Resume Walking</span>
                    </button>
                    <button
                      onClick={handleFinishRecording}
                      disabled={gpsPoints.length < 3}
                      className="w-full py-2.5 px-4 bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-xs disabled:opacity-40 cursor-pointer transition-colors"
                    >
                      <Square size={14} />
                      <span>Finish &amp; Close Boundary</span>
                    </button>
                  </div>
                )}

                {recordingState === 'review' && (
                  <div className="space-y-2">
                    <button
                      onClick={handleSaveBoundary}
                      disabled={isSaving}
                      className="w-full py-2.5 px-4 bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-xs disabled:opacity-50 cursor-pointer transition-colors"
                    >
                      {isSaving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                      <span>Save &amp; Confirm Walked Boundary</span>
                    </button>

                    <button
                      onClick={handleResumeRecording}
                      className="w-full py-2 px-4 border border-[#E5DDCF] bg-white hover:bg-neutral-50 text-[#103D2C] font-medium rounded-xl text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
                    >
                      <Footprints size={14} />
                      <span>Continue Walking Points</span>
                    </button>
                  </div>
                )}

                {recordingState !== 'idle' && (
                  <button
                    onClick={handleDiscardDraft}
                    className="w-full py-1.5 px-3 text-red-600 hover:text-red-800 text-xs font-medium cursor-pointer"
                  >
                    Discard Current GPS Walk
                  </button>
                )}
              </div>
            </div>

            {/* Bottom Modal Actions */}
            <div className="pt-2 border-t border-[#E5DDCF]">
              <button
                onClick={onClose}
                className="w-full py-2 px-4 border border-[#E5DDCF] bg-white hover:bg-neutral-50 text-[#292B26] font-medium rounded-xl text-xs cursor-pointer transition-colors"
              >
                Close &amp; Keep Saved Geometry
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
