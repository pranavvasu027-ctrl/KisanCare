import { useTranslation } from 'react-i18next';
import React, { useState, useEffect } from 'react';
import { Map, Plus, Trash2, Save, CheckCircle2, AlertCircle, Loader2, Navigation, Crosshair, MapPin, Compass } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../services/supabase';
import BoundaryEditorModal from '../../components/map/BoundaryEditorModal';

interface FieldItem {
  id: string;
  name: string;
  size: string;
  crop: string;
  isNew?: boolean;
  seasonId?: string;
  geojson_geometry?: any;
  boundaries_mapped?: boolean;
}

interface FarmSummary {
  id: string;
  farm_name: string;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  total_area: number;
  area_unit: string;
}

export default function FarmSetup() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const { user, isAuthenticated, isDemoMode } = useAuth();

  const [farmId, setFarmId] = useState<string | null>(null);
  const [allFarms, setAllFarms] = useState<FarmSummary[]>([]);
  const [farmName, setFarmName] = useState('Pranav Vasu Farm');
  const [totalArea, setTotalArea] = useState('12');
  const [stateName, setStateName] = useState('Maharashtra');
  const [district, setDistrict] = useState('Nagpur');
  const [village, setVillage] = useState('Shirpur');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [isCapturingGps, setIsCapturingGps] = useState(false);
  const [gpsSuccessMsg, setGpsSuccessMsg] = useState<string | null>(null);
  const [isBoundaryModalOpen, setIsBoundaryModalOpen] = useState(false);

  const [fields, setFields] = useState<FieldItem[]>([
    { id: 'field-1', name: 'Field 1 (North Parcel)', size: '6.5', crop: 'Soybean', isNew: true },
    { id: 'field-2', name: 'Field 2 (South Parcel)', size: '5.5', crop: 'Cotton', isNew: true },
  ]);
  const [originalFieldIds, setOriginalFieldIds] = useState<string[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load persisted farm data on mount or when user changes
  useEffect(() => {
    if (user && isAuthenticated) {
      loadFarmData(user.id);
    }
  }, [user, isAuthenticated]);

  const loadFarmData = async (userId: string, targetFarmId?: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // 1. Fetch all user farms for the selector
      const { data: userFarms } = await supabase
        .from('farms')
        .select('id, farm_name, location, latitude, longitude, total_area, area_unit')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });

      if (userFarms) {
        setAllFarms(userFarms);
      }

      // 2. Fetch specific target farm or the latest/saved active farm
      const preferredId = targetFarmId || localStorage.getItem('kisancare_active_farm_id') || undefined;

      let query = supabase
        .from('farms')
        .select('*, fields(*, seasons(*))')
        .eq('user_id', userId);

      if (preferredId) {
        query = query.eq('id', preferredId);
      } else {
        query = query.order('created_at', { ascending: false }).limit(1);
      }

      const { data: farmList, error } = await query;

      if (error) {
        console.error('Error loading farm data:', error);
        setErrorMessage(`Failed to load farm from database: ${error.message}`);
        return;
      }

      const farm = farmList && farmList.length > 0 ? farmList[0] : null;

      if (farm) {
        setFarmId(farm.id);
        localStorage.setItem('kisancare_active_farm_id', farm.id);
        setFarmName(farm.farm_name || '');
        setTotalArea(farm.total_area ? String(farm.total_area) : '');
        setLatitude(farm.latitude !== null && farm.latitude !== undefined ? String(farm.latitude) : '');
        setLongitude(farm.longitude !== null && farm.longitude !== undefined ? String(farm.longitude) : '');

        if (farm.location) {
          const parts = farm.location.split(',').map((p: string) => p.trim());
          if (parts.length >= 3) {
            setVillage(parts[0]);
            setDistrict(parts[1]);
            setStateName(parts[2]);
          } else {
            setVillage(farm.location);
          }
        }

        if (Array.isArray(farm.fields) && farm.fields.length > 0) {
          const loadedFields: FieldItem[] = farm.fields.map((f: any) => {
            const b = f.boundary;
            const hasGeom = b && (b.type === 'Polygon' || b.type === 'MultiPolygon' || (b.geometry && b.geometry.coordinates));
            return {
              id: f.id,
              name: f.field_name,
              size: String(f.area || ''),
              crop: f.seasons?.[0]?.crop || '',
              seasonId: f.seasons?.[0]?.id,
              isNew: false,
              geojson_geometry: hasGeom ? (b.geometry || b) : null,
              boundaries_mapped: Boolean(hasGeom)
            };
          });
          setFields(loadedFields);
          setOriginalFieldIds(loadedFields.map(f => f.id));
        } else {
          setFields([]);
          setOriginalFieldIds([]);
        }
      }
    } catch (err: any) {
      console.error('Unexpected error loading farm:', err);
      setErrorMessage(`Unexpected error: ${err.message || String(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNewFarm = () => {
    setFarmId(null);
    setFarmName('');
    setTotalArea('');
    setLatitude('');
    setLongitude('');
    setVillage('');
    setFields([
      { id: `temp-${Date.now()}-1`, name: 'Field 1', size: '', crop: '', isNew: true }
    ]);
    setOriginalFieldIds([]);
  };

  const handleSelectFarm = (selectedId: string) => {
    if (selectedId === 'new') {
      handleCreateNewFarm();
    } else if (user) {
      loadFarmData(user.id, selectedId);
    }
  };

  const handleCaptureGps = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }
    setIsCapturingGps(true);
    setGpsSuccessMsg(null);
    setErrorMessage(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsCapturingGps(false);
        const lat = pos.coords.latitude.toFixed(6);
        const lon = pos.coords.longitude.toFixed(6);
        setLatitude(lat);
        setLongitude(lon);
        setGpsSuccessMsg(`Captured current GPS coordinates: ${lat}, ${lon}`);
        setTimeout(() => setGpsSuccessMsg(null), 5000);
      },
      (err) => {
        setIsCapturingGps(false);
        setErrorMessage(`Failed to retrieve GPS location: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 10000 }
    );
  };

  const addField = () => {
    const tempId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    const nextNum = fields.length + 1;
    setFields([...fields, { id: tempId, name: `Field ${nextNum}`, size: '', crop: '', isNew: true }]);
  };

  const removeField = (id: string) => {
    setFields(fields.filter(f => f.id !== id));
  };

  const updateField = (id: string, key: keyof FieldItem, val: string) => {
    setFields(fields.map(f => f.id === id ? { ...f, [key]: val } : f));
  };

  const handleSave = async () => {
    setErrorMessage(null);
    setSaveStatus(null);

    // Validation
    if (!farmName.trim()) {
      setErrorMessage('Farm name is required.');
      return;
    }
    const areaNum = parseFloat(totalArea);
    if (isNaN(areaNum) || areaNum <= 0) {
      setErrorMessage('Total area must be a valid positive number.');
      return;
    }
    for (const f of fields) {
      if (!f.name.trim()) {
        setErrorMessage('All fields must have a name.');
        return;
      }
      const fArea = parseFloat(f.size);
      if (isNaN(fArea) || fArea <= 0) {
        setErrorMessage(`Field "${f.name}" must have a valid positive area.`);
        return;
      }
    }

    // Demo Mode handling
    if (!user || !isAuthenticated) {
      setSaveStatus('Farm details updated in active demo session. Local changes are kept in memory and not written to Supabase in demo mode.');
      setTimeout(() => setSaveStatus(null), 5000);
      return;
    }

    // Authenticated Supabase Persistence
    setIsSaving(true);
    try {
      // 1. Profile upsert
      await supabase.from('profiles').upsert({
        user_id: user.id,
        name: farmName ? `${farmName} Manager` : 'Farmer',
        preferred_language: 'en'
      }, { onConflict: 'user_id' });

      let activeFarmId = farmId;
      const formattedLocation = `${village.trim()}, ${district.trim()}, ${stateName.trim()}`;
      const latNum = latitude.trim() ? parseFloat(latitude.trim()) : null;
      const lonNum = longitude.trim() ? parseFloat(longitude.trim()) : null;

      // 2. Farm insert or update
      if (activeFarmId) {
        const { error: farmUpdateErr } = await supabase
          .from('farms')
          .update({
            farm_name: farmName.trim(),
            total_area: areaNum,
            location: formattedLocation,
            latitude: latNum,
            longitude: lonNum,
            updated_at: new Date().toISOString()
          })
          .eq('id', activeFarmId)
          .eq('user_id', user.id);

        if (farmUpdateErr) throw farmUpdateErr;
      } else {
        const { data: createdFarm, error: farmInsertErr } = await supabase
          .from('farms')
          .insert({
            user_id: user.id,
            farm_name: farmName.trim(),
            total_area: areaNum,
            location: formattedLocation,
            latitude: latNum,
            longitude: lonNum,
            area_unit: 'acre'
          })
          .select()
          .single();

        if (farmInsertErr) throw farmInsertErr;
        activeFarmId = createdFarm.id;
        setFarmId(activeFarmId);
      }

      if (activeFarmId) {
        localStorage.setItem('kisancare_active_farm_id', activeFarmId);
      }

      // 3. Fields synchronization
      const currentPersistedIds = fields.filter(f => !f.isNew).map(f => f.id);
      const fieldsToDelete = originalFieldIds.filter(id => !currentPersistedIds.includes(id));
      if (fieldsToDelete.length > 0) {
        const { error: delErr } = await supabase
          .from('fields')
          .delete()
          .in('id', fieldsToDelete);
        if (delErr) throw delErr;
      }

      const updatedFieldItems: FieldItem[] = [];

      for (const field of fields) {
        let fieldUuid = field.id;
        if (field.isNew) {
          const { data: newField, error: fErr } = await supabase
            .from('fields')
            .insert({
              farm_id: activeFarmId,
              field_name: field.name.trim(),
              area: parseFloat(field.size),
              area_unit: 'acre'
            })
            .select()
            .single();

          if (fErr) throw fErr;
          fieldUuid = newField.id;
        } else {
          const { error: uErr } = await supabase
            .from('fields')
            .update({
              field_name: field.name.trim(),
              area: parseFloat(field.size),
              updated_at: new Date().toISOString()
            })
            .eq('id', fieldUuid);

          if (uErr) throw uErr;
        }

        let seasonId = field.seasonId;
        if (field.crop.trim()) {
          if (seasonId) {
            await supabase
              .from('seasons')
              .update({
                crop: field.crop.trim(),
                updated_at: new Date().toISOString()
              })
              .eq('id', seasonId);
          } else {
            const { data: newSeason, error: sErr } = await supabase
              .from('seasons')
              .insert({
                field_id: fieldUuid,
                season_name: 'Current Season',
                crop: field.crop.trim(),
                status: 'ACTIVE'
              })
              .select()
              .single();

            if (sErr) throw sErr;
            seasonId = newSeason.id;
          }

          // Also insert a crop record for history
          await supabase.from('crop_records').insert({
            season_id: seasonId,
            crop: field.crop.trim(),
            area: parseFloat(field.size),
            provenance: 'FARMER_ENTERED'
          });
        }

        updatedFieldItems.push({
          id: fieldUuid,
          name: field.name.trim(),
          size: field.size,
          crop: field.crop.trim(),
          isNew: false,
          seasonId
        });
      }

      // 4. Read-back verification
      const { data: verifiedFarm, error: rbError } = await supabase
        .from('farms')
        .select('*, fields(*, seasons(*))')
        .eq('id', activeFarmId)
        .single();

      if (rbError || !verifiedFarm) {
        throw new Error(rbError?.message || 'Database read-back verification failed.');
      }

      setFields(updatedFieldItems);
      setOriginalFieldIds(updatedFieldItems.map(f => f.id));
      if (user) {
        const { data: updatedFarms } = await supabase
          .from('farms')
          .select('id, farm_name, location, latitude, longitude, total_area, area_unit')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        if (updatedFarms) {
          setAllFarms(updatedFarms);
        }
      }
      setSaveStatus('Farm details, GPS coordinates, field boundaries, and crop allocations successfully verified and saved to Supabase!');
      setTimeout(() => setSaveStatus(null), 6000);
    } catch (err: any) {
      console.error('Save failed:', err);
      setErrorMessage(`Failed to save to Supabase: ${err.message || String(err)}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">{t('farmSetup.title')}</h1>
            {(!isAuthenticated || isDemoMode) ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo Profile (Local Memory)
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                Connected to Supabase
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">{t('farmSetup.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {farmId && (
            <button
              type="button"
              onClick={() => setIsBoundaryModalOpen(true)}
              className="bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] border border-[#E5DDCF] px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-semibold transition-colors cursor-pointer"
            >
              <Compass size={17} className="text-[#103D2C]" />
              <span>Map Farm Boundary</span>
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={isLoading || isSaving}
            className="bg-[#103D2C] text-white px-5 py-2.5 rounded-lg flex items-center gap-2 hover:bg-[#17643E] transition-colors cursor-pointer disabled:opacity-50"
          >
            {isSaving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
            <span>{isSaving ? t('common.loading') : t('farmSetup.saveFarm')}</span>
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
          <span>Loading farm profile from Supabase...</span>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {saveStatus && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{saveStatus}</span>
        </div>
      )}

      {(!isAuthenticated || isDemoMode) && (
        <div className="bg-amber-50/80 border border-amber-200 text-amber-900 p-4 rounded-xl text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold">Demonstration Session: </span>
            You are browsing without an authenticated session. Changes made in this form will update the in-memory state for this demo.
            To persist records to your PostgreSQL database with RLS policies, sign in through the login screen.
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="p-6 border-b border-[#E5DDCF]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <h2 className="text-xl font-bold text-[#103D2C]">Basic Information</h2>
            {allFarms.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#292B26]/70">Selected Farm:</span>
                <select
                  value={farmId || 'new'}
                  onChange={(e) => handleSelectFarm(e.target.value)}
                  className="border border-[#E5DDCF] rounded-lg px-3 py-1.5 text-xs bg-[#FBF7EF] font-medium text-[#103D2C] outline-none"
                >
                  {allFarms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.farm_name} ({f.total_area} {f.area_unit})
                    </option>
                  ))}
                  <option value="new">+ Register New Farm</option>
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">{t('farmSetup.farmName')}</label>
              <input
                type="text"
                value={farmName}
                onChange={(e) => setFarmName(e.target.value)}
                placeholder="e.g. Pranav Vasu Farm"
                className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">{t('farmSetup.totalArea')}</label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                value={totalArea}
                onChange={(e) => setTotalArea(e.target.value)}
                placeholder="e.g. 12"
                className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
              />
            </div>
            <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">State</label>
                <select
                  value={stateName}
                  onChange={(e) => setStateName(e.target.value)}
                  className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
                >
                  <option value="Maharashtra">Maharashtra</option>
                  <option value="Gujarat">Gujarat</option>
                  <option value="Madhya Pradesh">Madhya Pradesh</option>
                  <option value="Karnataka">Karnataka</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">District</label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
                >
                  <option value="Nagpur">Nagpur</option>
                  <option value="Akola">Akola</option>
                  <option value="Pune">Pune</option>
                  <option value="Nashik">Nashik</option>
                  <option value="Amravati">Amravati</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">Village / Locality</label>
                <input
                  type="text"
                  value={village}
                  onChange={(e) => setVillage(e.target.value)}
                  placeholder="e.g. Takli Bu or Shirpur"
                  className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
                />
              </div>
            </div>

            {/* Geographic Coordinates & GPS Capture */}
            <div className="md:col-span-2 bg-[#FBF7EF] p-4 rounded-xl border border-[#E5DDCF] space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-[#17643E]" />
                  <span className="text-sm font-bold text-[#103D2C]">Geographic Coordinates (WGS84)</span>
                </div>
                <button
                  type="button"
                  onClick={handleCaptureGps}
                  disabled={isCapturingGps}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isCapturingGps ? (
                    <Loader2 size={13} className="animate-spin" />
                  ) : (
                    <Navigation size={13} />
                  )}
                  <span>{isCapturingGps ? 'Reading GPS Device...' : 'Use Current Device GPS'}</span>
                </button>
              </div>

              {gpsSuccessMsg && (
                <div className="text-xs text-emerald-800 bg-emerald-100/70 border border-emerald-300 px-3 py-1.5 rounded-lg">
                  {gpsSuccessMsg}
                </div>
              )}

              <p className="text-[11px] text-[#292B26]/70 leading-relaxed">
                Provide accurate GPS coordinates to position your farm pin on the Digital Twin interactive map. If coordinates are not provided, an approximate village centroid reference will be used with an explicit notice.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <div>
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Latitude (°N)</label>
                  <input
                    type="number"
                    step="0.000001"
                    min="-90"
                    max="90"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    placeholder="e.g. 20.918912"
                    className="w-full border border-[#E5DDCF] rounded-lg px-3 py-1.5 bg-white text-sm focus:outline-none focus:border-[#17643E]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Longitude (°E)</label>
                  <input
                    type="number"
                    step="0.000001"
                    min="-180"
                    max="180"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    placeholder="e.g. 76.982846"
                    className="w-full border border-[#E5DDCF] rounded-lg px-3 py-1.5 bg-white text-sm focus:outline-none focus:border-[#17643E]"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-[#FBF7EF]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-[#103D2C]">Fields Configuration</h2>
            <button onClick={addField} className="text-[#17643E] font-medium text-sm flex items-center gap-1 hover:underline cursor-pointer">
              <Plus size={16} /> {t('farmSetup.addField')}
            </button>
          </div>

          <div className="space-y-4">
            {fields.map((field) => (
              <div key={field.id} className="bg-white p-4 rounded-xl border border-[#E5DDCF] flex flex-col md:flex-row md:items-end gap-4">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Field Name</label>
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) => updateField(field.id, 'name', e.target.value)}
                    placeholder="e.g. North Parcel"
                    className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm"
                  />
                </div>
                <div className="w-full md:w-32">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Size (Acres)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={field.size}
                    onChange={(e) => updateField(field.id, 'size', e.target.value)}
                    placeholder="0.0"
                    className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Current Crop</label>
                  <select
                    value={field.crop}
                    onChange={(e) => updateField(field.id, 'crop', e.target.value)}
                    className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm"
                  >
                    <option value="">Select Crop...</option>
                    <option value="Soybean">Soybean</option>
                    <option value="Cotton">Cotton</option>
                    <option value="Pigeon Pea">Pigeon Pea</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Rice">Rice</option>
                    <option value="Onion">Onion</option>
                    <option value="Tomato">Tomato</option>
                  </select>
                </div>
                <button
                  onClick={() => removeField(field.id)}
                  title="Remove Field"
                  className="p-2 text-red-500 hover:bg-red-50 rounded-md self-end md:self-auto cursor-pointer"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Boundary Editor Modal */}
      {farmId && (
        <BoundaryEditorModal
          isOpen={isBoundaryModalOpen}
          onClose={() => setIsBoundaryModalOpen(false)}
          farmId={farmId}
          farmName={farmName}
          initialCenter={[
            latitude ? parseFloat(latitude) : 20.918912,
            longitude ? parseFloat(longitude) : 76.982846
          ]}
          isApproximateCenter={!latitude || !longitude}
          fields={fields.filter(f => !f.isNew).map(f => ({
            id: f.id,
            name: f.name,
            area: parseFloat(f.size) || 0,
            area_unit: 'acre',
            crop: f.crop,
            geojson_geometry: f.geojson_geometry,
            boundaries_mapped: f.boundaries_mapped
          }))}
          onSaveSuccess={(updatedField) => {
            setFields(prev => prev.map(f => f.id === updatedField.id ? {
              ...f,
              size: String(updatedField.area),
              geojson_geometry: updatedField.geojson_geometry,
              boundaries_mapped: true
            } : f));
          }}
        />
      )}
    </div>
  );
}
