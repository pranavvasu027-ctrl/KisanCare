import React, { useState } from 'react';
import { Map, Plus, Trash2, Save, CheckCircle2, AlertCircle } from 'lucide-react';

interface Field {
  id: number;
  name: string;
  size: string;
  crop: string;
}

export default function FarmSetup() {
  const [farmName, setFarmName] = useState('Patil Farm');
  const [totalArea, setTotalArea] = useState('12');
  const [stateName, setStateName] = useState('Maharashtra');
  const [district, setDistrict] = useState('Nagpur');
  const [village, setVillage] = useState('Shirpur');
  const [fields, setFields] = useState<Field[]>([
    { id: 1, name: 'Field 1 (North Parcel)', size: '6.5', crop: 'Soybean' },
    { id: 2, name: 'Field 2 (South Parcel)', size: '5.5', crop: 'Cotton' },
  ]);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const addField = () => {
    const nextId = fields.length > 0 ? Math.max(...fields.map(f => f.id)) + 1 : 1;
    setFields([...fields, { id: nextId, name: `Field ${nextId}`, size: '', crop: '' }]);
  };

  const removeField = (id: number) => {
    setFields(fields.filter(f => f.id !== id));
  };

  const updateField = (id: number, key: keyof Field, val: string) => {
    setFields(fields.map(f => f.id === id ? { ...f, [key]: val } : f));
  };

  const handleSave = () => {
    setSaveStatus('Farm details updated in active demo session. Local changes are not written to Supabase in demo mode.');
    setTimeout(() => {
      setSaveStatus(null);
    }, 4000);
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Setup</h1>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              Demo Profile
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1">Configure your farm profile and field boundaries.</p>
        </div>
        <button
          onClick={handleSave}
          className="bg-[#103D2C] text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-[#17643E] transition-colors cursor-pointer"
        >
          <Save size={18} />
          Save Changes
        </button>
      </div>

      {saveStatus && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{saveStatus}</span>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="p-6 border-b border-[#E5DDCF]">
          <h2 className="text-xl font-bold text-[#103D2C] mb-4">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Farm Name</label>
              <input
                type="text"
                value={farmName}
                onChange={(e) => setFarmName(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Total Area (Acres)</label>
              <input
                type="number"
                value={totalArea}
                onChange={(e) => setTotalArea(e.target.value)}
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
                  <option value="Pune">Pune</option>
                  <option value="Nashik">Nashik</option>
                  <option value="Amravati">Amravati</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">Village</label>
                <input
                  type="text"
                  value={village}
                  onChange={(e) => setVillage(e.target.value)}
                  className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-[#FBF7EF]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-[#103D2C]">Fields Configuration</h2>
            <button onClick={addField} className="text-[#17643E] font-medium text-sm flex items-center gap-1 hover:underline cursor-pointer">
              <Plus size={16} /> Add Field
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
                    className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm"
                  />
                </div>
                <div className="w-full md:w-32">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Size (Acres)</label>
                  <input
                    type="number"
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
    </div>
  );
}
