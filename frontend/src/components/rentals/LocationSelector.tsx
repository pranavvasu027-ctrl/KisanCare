import React from 'react';
import { MapPin, Globe, Filter, X } from 'lucide-react';
import { MAHARASHTRA_GEOGRAPHY } from '../../data/maharashtraGeography';

interface LocationSelectorProps {
  selectedDivision?: string;
  selectedDistrict?: string;
  selectedTaluka?: string;
  onLocationChange: (loc: { division?: string; district?: string; taluka?: string }) => void;
  language?: string;
}

export const LocationSelector: React.FC<LocationSelectorProps> = ({
  selectedDivision,
  selectedDistrict,
  selectedTaluka,
  onLocationChange,
  language = 'en'
}) => {
  const divisions = Object.keys(MAHARASHTRA_GEOGRAPHY);

  // Available districts for current division
  const availableDistricts = selectedDivision && MAHARASHTRA_GEOGRAPHY[selectedDivision]
    ? Object.keys(MAHARASHTRA_GEOGRAPHY[selectedDivision].districts)
    : [];

  // Available talukas for current district
  const availableTalukas = selectedDivision && selectedDistrict && MAHARASHTRA_GEOGRAPHY[selectedDivision]?.districts[selectedDistrict]
    ? MAHARASHTRA_GEOGRAPHY[selectedDivision].districts[selectedDistrict]
    : [];

  const handleDivisionChange = (div: string) => {
    if (!div) {
      onLocationChange({});
    } else {
      onLocationChange({ division: div });
    }
  };

  const handleDistrictChange = (dist: string) => {
    if (!dist) {
      onLocationChange({ division: selectedDivision });
    } else {
      onLocationChange({ division: selectedDivision, district: dist });
    }
  };

  const handleTalukaChange = (tal: string) => {
    onLocationChange({
      division: selectedDivision,
      district: selectedDistrict,
      taluka: tal || undefined
    });
  };

  const clearLocation = () => {
    onLocationChange({});
  };

  const hasActiveFilter = Boolean(selectedDivision || selectedDistrict || selectedTaluka);

  return (
    <div className="bg-gray-800/80 border border-gray-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <span>{language === 'mr' ? 'महाराष्ट्र कार्यक्षेत्र निवडा' : language === 'hi' ? 'महाराष्ट्र कार्यक्षेत्र चुनें' : 'Maharashtra Service Area'}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700/40">
                {language === 'mr' ? '६ प्रशासकीय विभाग' : '6 Divisions'}
              </span>
            </h4>
            <p className="text-xs text-gray-400">
              {language === 'mr' 
                ? 'राज्यव्यापी कव्हरेज: सर्व ३६ जिल्हे आणि स्थानिक तालुके' 
                : 'Statewide coverage: all 36 districts and local talukas'}
            </p>
          </div>
        </div>

        {hasActiveFilter && (
          <button
            onClick={clearLocation}
            className="flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            <span>{language === 'mr' ? 'सर्व महाराष्ट्र दाखवा' : 'View All Maharashtra'}</span>
          </button>
        )}
      </div>

      {/* Quick Division Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none mb-3">
        <button
          onClick={() => onLocationChange({})}
          className={`text-xs px-3 py-1.5 rounded-xl font-medium transition-all whitespace-nowrap flex items-center gap-1.5 ${
            !selectedDivision
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/30 font-semibold'
              : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white'
          }`}
        >
          <Globe className="w-3.5 h-3.5" />
          <span>{language === 'mr' ? 'सर्व महाराष्ट्र' : 'All Maharashtra'}</span>
        </button>
        {divisions.map((div) => {
          const isSelected = selectedDivision === div;
          return (
            <button
              key={div}
              onClick={() => handleDivisionChange(div)}
              className={`text-xs px-3 py-1.5 rounded-xl font-medium transition-all whitespace-nowrap ${
                isSelected
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/30 font-semibold'
                  : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {div}
            </button>
          );
        })}
      </div>

      {/* Cascading Dropdowns */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {/* 1. Division Dropdown */}
        <div>
          <label className="block text-[11px] font-medium text-gray-400 mb-1">
            {language === 'mr' ? 'प्रशासकीय विभाग' : 'Division'}
          </label>
          <select
            value={selectedDivision || ''}
            onChange={(e) => handleDivisionChange(e.target.value)}
            className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
          >
            <option value="">{language === 'mr' ? 'सर्व विभाग (६)' : 'All Divisions (6)'}</option>
            {divisions.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* 2. District Dropdown */}
        <div>
          <label className="block text-[11px] font-medium text-gray-400 mb-1">
            {language === 'mr' ? 'जिल्हा' : 'District'}
          </label>
          <select
            value={selectedDistrict || ''}
            disabled={!selectedDivision}
            onChange={(e) => handleDistrictChange(e.target.value)}
            className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-3 py-2 text-xs text-white disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:border-emerald-500"
          >
            <option value="">
              {!selectedDivision
                ? (language === 'mr' ? 'प्रथम विभाग निवडा' : 'Select Division first')
                : (language === 'mr' ? 'सर्व जिल्हे' : 'All Districts')}
            </option>
            {availableDistricts.map((dist) => (
              <option key={dist} value={dist}>
                {dist}
              </option>
            ))}
          </select>
        </div>

        {/* 3. Taluka Dropdown */}
        <div>
          <label className="block text-[11px] font-medium text-gray-400 mb-1">
            {language === 'mr' ? 'तालुका' : 'Taluka'}
          </label>
          <select
            value={selectedTaluka || ''}
            disabled={!selectedDistrict}
            onChange={(e) => handleTalukaChange(e.target.value)}
            className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-3 py-2 text-xs text-white disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:border-emerald-500"
          >
            <option value="">
              {!selectedDistrict
                ? (language === 'mr' ? 'प्रथम जिल्हा निवडा' : 'Select District first')
                : (language === 'mr' ? 'सर्व तालुके' : 'All Talukas')}
            </option>
            {availableTalukas.map((tal) => (
              <option key={tal} value={tal}>
                {tal}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* University affiliation indicator */}
      {selectedDivision && MAHARASHTRA_GEOGRAPHY[selectedDivision] && (
        <div className="mt-2.5 pt-2 border-t border-gray-700/40 flex items-center justify-between text-[11px] text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <strong className="text-gray-300">{language === 'mr' ? 'कृषी विद्यापीठ:' : 'Regional Agri University:'}</strong>{' '}
            {MAHARASHTRA_GEOGRAPHY[selectedDivision].regionalUniversity}
          </span>
          <span className="text-gray-400">
            {availableDistricts.length} {language === 'mr' ? 'जिल्हे' : 'Districts'}
          </span>
        </div>
      )}
    </div>
  );
};
