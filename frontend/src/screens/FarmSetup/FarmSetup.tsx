import React, { useState } from 'react';
import { Map, Plus, Trash2, Save, ArrowRight, Leaf, Droplets } from 'lucide-react';

export default function FarmSetup() {
  const [fields, setFields] = useState([{ id: 1, name: 'Field 1', size: '', crop: '' }]);

  const addField = () => {
    setFields([...fields, { id: fields.length + 1, name: `Field ${fields.length + 1}`, size: '', crop: '' }]);
  };

  const removeField = (id: number) => {
    setFields(fields.filter(f => f.id !== id));
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Setup</h1>
          <p className="text-[#292B26]/70 mt-1">Configure your farm details and field boundaries.</p>
        </div>
        <button className="bg-[#103D2C] text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-[#17643E] transition-colors">
          <Save size={18} />
          Save Changes
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="p-6 border-b border-[#E5DDCF]">
          <h2 className="text-xl font-bold text-[#103D2C] mb-4">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Farm Name</label>
              <input type="text" defaultValue="Patil Farm" className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]" />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Total Area (Acres)</label>
              <input type="number" defaultValue={12} className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]" />
            </div>
            <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">State</label>
                <select className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]">
                  <option>Maharashtra</option>
                  <option>Gujarat</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">District</label>
                <select className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]">
                  <option>Nagpur</option>
                  <option>Pune</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#292B26] mb-1">Village</label>
                <input type="text" defaultValue="Shirpur" className="w-full border border-[#E5DDCF] rounded-lg px-4 py-2 bg-[#FBF7EF] focus:outline-none focus:border-[#17643E]" />
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-[#FBF7EF]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-[#103D2C]">Fields Configuration</h2>
            <button onClick={addField} className="text-[#17643E] font-medium text-sm flex items-center gap-1 hover:underline">
              <Plus size={16} /> Add Field
            </button>
          </div>
          
          <div className="space-y-4">
            {fields.map((field) => (
              <div key={field.id} className="bg-white p-4 rounded-xl border border-[#E5DDCF] flex items-end gap-4">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Field Name</label>
                  <input type="text" value={field.name} onChange={() => {}} className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm" />
                </div>
                <div className="w-32">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Size (Acres)</label>
                  <input type="number" placeholder="0.0" className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm" />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-[#292B26] mb-1">Current Crop</label>
                  <select className="w-full border border-[#E5DDCF] rounded-md px-3 py-1.5 text-sm">
                    <option>Select...</option>
                    <option>Soybean</option>
                    <option>Cotton</option>
                  </select>
                </div>
                <button onClick={() => removeField(field.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-md">
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
