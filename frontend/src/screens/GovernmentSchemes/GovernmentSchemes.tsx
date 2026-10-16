import React, { useState, useEffect } from 'react';
import {
  Landmark, Search, Filter, ExternalLink, CheckCircle,
  FileText, ShieldCheck, ChevronDown, ChevronUp, Info,
  BadgeCheck, Bookmark, RotateCcw, Sparkles
} from 'lucide-react';

export type EligibilityFilterType =
  | 'All'
  | 'Small & Marginal Farmers (< 2 Ha)'
  | 'All Landholding Farmers'
  | 'Tenants & Sharecroppers'
  | 'Irrigation Water Source Available'
  | 'FPOs, SHGs & Cooperatives';

interface SchemeItem {
  id: string;
  name: string;
  acronym: string;
  ministry: string;
  category: 'Financial Support' | 'Crop Insurance' | 'Credit & Loans' | 'Irrigation & Soil' | 'Machinery';
  eligibilityTypes: EligibilityFilterType[];
  benefitSummary: string;
  detailedBenefits: string[];
  eligibility: string[];
  requiredDocuments: string[];
  officialUrl: string;
  isVerified: boolean;
}

const SCHEMES_DIRECTORY: SchemeItem[] = [
  {
    id: 'pm-kisan',
    name: 'Pradhan Mantri Kisan Samman Nidhi',
    acronym: 'PM-KISAN',
    ministry: 'Ministry of Agriculture & Farmers Welfare, GoI',
    category: 'Financial Support',
    eligibilityTypes: [
      'All Landholding Farmers',
      'Small & Marginal Farmers (< 2 Ha)'
    ],
    benefitSummary: 'Direct income support of ₹6,000 per year transferred in 3 equal installments of ₹2,000.',
    detailedBenefits: [
      '₹6,000 per year credited directly to Aadhaar-seeded bank accounts (DBT).',
      'Disbursed every 4 months (April–July, August–November, December–March).',
      'Zero intermediary deductions or service charges.'
    ],
    eligibility: [
      'All landholding farmer families with cultivable land holdings in their name.',
      'Excludes institutional landholders, past/present constitutional post holders.',
      'Excludes serving/retired government employees and individuals who paid income tax in last assessment year.'
    ],
    requiredDocuments: [
      'Aadhaar Card (Mandatory biometric/OTP verification)',
      'Land Ownership Record (e.g. 7/12 Extract, Khatauni, RoR)',
      'Aadhaar-seeded Bank Account Passbook with IFSC',
      'Active Mobile Number linked with Aadhaar'
    ],
    officialUrl: 'https://pmkisan.gov.in',
    isVerified: true
  },
  {
    id: 'pmfby',
    name: 'Pradhan Mantri Fasal Bima Yojana',
    acronym: 'PMFBY',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    category: 'Crop Insurance',
    eligibilityTypes: [
      'All Landholding Farmers',
      'Small & Marginal Farmers (< 2 Ha)',
      'Tenants & Sharecroppers'
    ],
    benefitSummary: 'Comprehensive crop insurance against drought, floods, hailstorms, pests, and post-harvest losses.',
    detailedBenefits: [
      'Very low capped farmer premium: 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops.',
      'Government pays remaining actuarial premium subsidy equally shared between Central and State governments.',
      'Coverage from pre-sowing to post-harvest storage losses caused by localized cyclones or unseasonal rains.'
    ],
    eligibility: [
      'All farmers growing notified crops in notified insurance units/villages.',
      'Includes loanee and non-loanee farmers, sharecroppers, and tenant farmers with recorded rights.'
    ],
    requiredDocuments: [
      'Land Record Document (7/12 / Khatauni / Record of Rights)',
      'Sowing Certificate or Self-Declaration of Sown Crop',
      'Identity Proof (Aadhaar Card)',
      'Bank Account Passbook (with active branch IFSC)'
    ],
    officialUrl: 'https://pmfby.gov.in',
    isVerified: true
  },
  {
    id: 'kcc',
    name: 'Kisan Credit Card Scheme',
    acronym: 'KCC',
    ministry: 'Department of Financial Services & NABARD',
    category: 'Credit & Loans',
    eligibilityTypes: [
      'All Landholding Farmers',
      'Small & Marginal Farmers (< 2 Ha)',
      'Tenants & Sharecroppers',
      'FPOs, SHGs & Cooperatives'
    ],
    benefitSummary: 'Concessional short-term institutional credit at an effective 4% interest rate with prompt repayment.',
    detailedBenefits: [
      'Credit limit based on crop cultivation scale and land area.',
      'Benchmark interest rate is 7%, reduced to 4% p.a. through 3% Prompt Repayment Incentive (PRI).',
      'Flexible credit with debit card functionality (RuPay KCC) for ATM cash withdrawals and PoS seed/fertilizer purchases.'
    ],
    eligibility: [
      'Owner cultivators, tenant farmers, oral lessees, and sharecroppers.',
      'Self-Help Groups (SHGs) and Joint Liability Groups (JLGs) of farmers.',
      'Animal husbandry and fisheries farmers are also eligible for working capital credit.'
    ],
    requiredDocuments: [
      'Completed KCC application form from issuing bank',
      'Identity and Address Proof (Aadhaar Card / Voter ID)',
      'Land cultivation documents and crop pattern declaration',
      'No-Dues Certificate or declaration from contiguous local bank branches'
    ],
    officialUrl: 'https://www.nabard.org',
    isVerified: true
  },
  {
    id: 'soil-health-card',
    name: 'Soil Health Card Scheme',
    acronym: 'SHC',
    ministry: 'Department of Agriculture & Farmers Welfare',
    category: 'Irrigation & Soil',
    eligibilityTypes: [
      'All Landholding Farmers',
      'Small & Marginal Farmers (< 2 Ha)',
      'Tenants & Sharecroppers'
    ],
    benefitSummary: 'Customized soil test report issued every 3 years with nutrient deficiencies and dosage guidance.',
    detailedBenefits: [
      'Free testing of 12 critical parameters: N, P, K, S, Zn, Fe, Cu, Mn, Bo, pH, EC, and Organic Carbon.',
      'Specific fertilizer recommendation matrix tailored to the farmer\'s planned crop.',
      'Reduces unnecessary fertilizer costs and prevents soil degradation.'
    ],
    eligibility: [
      'All landholding and operating farmers across all agricultural zones in India.',
      'Samples collected by state agriculture extension officers directly from geo-referenced grid points.'
    ],
    requiredDocuments: [
      'Farmer Name and Contact Details',
      'Field survey number / Khasra number for sample identification'
    ],
    officialUrl: 'https://soilhealth.dac.gov.in',
    isVerified: true
  },
  {
    id: 'pmksy',
    name: 'Pradhan Mantri Krishi Sinchayee Yojana (Per Drop More Crop)',
    acronym: 'PMKSY-PDMC',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    category: 'Irrigation & Soil',
    eligibilityTypes: [
      'Small & Marginal Farmers (< 2 Ha)',
      'Irrigation Water Source Available',
      'FPOs, SHGs & Cooperatives'
    ],
    benefitSummary: 'Financial capital subsidy of 45% to 55% for installing drip and sprinkler micro-irrigation systems.',
    detailedBenefits: [
      'Up to 55% subsidy for Small and Marginal Farmers (SMF).',
      'Up to 45% subsidy for Other Farmers.',
      'Increases water use efficiency by 30-50% while boosting crop yield.'
    ],
    eligibility: [
      'Farmers possessing agricultural land with assured irrigation water source (well, borewell, or canal lifting).',
      'Members of Water User Associations or Farmer Producer Organizations (FPOs).'
    ],
    requiredDocuments: [
      'Proof of land ownership (7/12 extract / Khatauni)',
      'Aadhaar Card',
      'Proof of water availability / electricity pump connection',
      'Quotation from empanelled micro-irrigation equipment manufacturer'
    ],
    officialUrl: 'https://pmksy.gov.in',
    isVerified: true
  },
  {
    id: 'smam',
    name: 'Sub-Mission on Agricultural Mechanization',
    acronym: 'SMAM',
    ministry: 'Ministry of Agriculture & Farmers Welfare',
    category: 'Machinery',
    eligibilityTypes: [
      'All Landholding Farmers',
      'Small & Marginal Farmers (< 2 Ha)',
      'FPOs, SHGs & Cooperatives'
    ],
    benefitSummary: '40% to 50% subsidy on purchase of tractors, rotavators, power tillers, and setting up Custom Hiring Centers.',
    detailedBenefits: [
      'Direct subsidy on farm machinery: 50% for SC, ST, Small & Marginal farmers, and women farmers; 40% for others.',
      'Financial support for establishment of Farm Machinery Banks and Custom Hiring Centers (CHCs) in rural clusters.'
    ],
    eligibility: [
      'Individual farmers possessing cultivable agricultural land.',
      'Cooperative societies, registered Farmer Producer Organizations (FPOs), and village panchayats.'
    ],
    requiredDocuments: [
      'Aadhaar Card',
      'Land revenue document / record',
      'Bank passbook photocopy showing account number & IFSC',
      'Caste certificate (for SC/ST subsidy benefits)'
    ],
    officialUrl: 'https://agrimachinery.nic.in',
    isVerified: true
  }
];

const ELIGIBILITY_OPTIONS: EligibilityFilterType[] = [
  'All',
  'Small & Marginal Farmers (< 2 Ha)',
  'All Landholding Farmers',
  'Tenants & Sharecroppers',
  'Irrigation Water Source Available',
  'FPOs, SHGs & Cooperatives'
];

export default function GovernmentSchemes() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedEligibility, setSelectedEligibility] = useState<EligibilityFilterType>('All');
  const [showSavedOnly, setShowSavedOnly] = useState<boolean>(false);
  const [expandedSchemeId, setExpandedSchemeId] = useState<string | null>('pm-kisan');
  const [bookmarkedIds, setBookmarkedIds] = useState<string[]>([]);
  const [bookmarkFeedback, setBookmarkFeedback] = useState<string | null>(null);

  // Restore bookmarked schemes from localStorage on component mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('kisancare_saved_schemes');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setBookmarkedIds(parsed);
        }
      }
    } catch {
      // Local storage disabled or empty
    }
  }, []);

  const toggleBookmark = (id: string, schemeName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setBookmarkedIds((prev) => {
      const isAlreadySaved = prev.includes(id);
      const next = isAlreadySaved ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem('kisancare_saved_schemes', JSON.stringify(next));
      } catch (err) {
        console.error('Failed to save bookmarks to localStorage', err);
      }
      setBookmarkFeedback(
        isAlreadySaved
          ? `Removed "${schemeName}" from saved schemes.`
          : `Saved "${schemeName}" to local bookmarks (Stored in browser storage).`
      );
      setTimeout(() => setBookmarkFeedback(null), 4000);
      return next;
    });
  };

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedCategory('All');
    setSelectedEligibility('All');
    setShowSavedOnly(false);
  };

  const hasActiveFilters =
    Boolean(searchTerm.trim()) ||
    selectedCategory !== 'All' ||
    selectedEligibility !== 'All' ||
    showSavedOnly;

  const filteredSchemes = SCHEMES_DIRECTORY.filter((s) => {
    const term = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !term ||
      s.name.toLowerCase().includes(term) ||
      s.acronym.toLowerCase().includes(term) ||
      s.ministry.toLowerCase().includes(term) ||
      s.benefitSummary.toLowerCase().includes(term) ||
      s.detailedBenefits.some((b) => b.toLowerCase().includes(term)) ||
      s.eligibility.some((e) => e.toLowerCase().includes(term)) ||
      s.requiredDocuments.some((d) => d.toLowerCase().includes(term));

    const matchesCategory =
      selectedCategory === 'All' || s.category === selectedCategory;

    const matchesEligibility =
      selectedEligibility === 'All' ||
      s.eligibilityTypes.includes(selectedEligibility);

    const matchesBookmark =
      !showSavedOnly || bookmarkedIds.includes(s.id);

    return matchesSearch && matchesCategory && matchesEligibility && matchesBookmark;
  });

  const toggleExpand = (id: string) => {
    setExpandedSchemeId(expandedSchemeId === id ? null : id);
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Government Schemes</h1>
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
              <BadgeCheck size={13} className="text-emerald-700" />
              Verified Official Directory
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">
            Browse verified agricultural welfare schemes, subsidy programs, credit limits, and official portal links.
          </p>
        </div>

        {/* Saved Schemes Toggle Pill */}
        <button
          onClick={() => setShowSavedOnly(!showSavedOnly)}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer shadow-xs ${
            showSavedOnly
              ? 'bg-[#103D2C] text-white border-[#103D2C]'
              : 'bg-white text-[#103D2C] border-[#E5DDCF] hover:border-[#17643E]'
          }`}
          title="Toggle view of bookmarked schemes"
        >
          <Bookmark size={15} className={showSavedOnly ? 'fill-white' : ''} />
          <span>Saved Schemes</span>
          <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
            showSavedOnly ? 'bg-white/20 text-white' : 'bg-[#FBF7EF] text-[#103D2C] font-bold border border-[#E5DDCF]'
          }`}>
            {bookmarkedIds.length}
          </span>
        </button>
      </div>

      {/* Bookmark Feedback Notification */}
      {bookmarkFeedback && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-xs">
          <Bookmark size={14} className="text-emerald-700 shrink-0 fill-emerald-600" />
          <span>{bookmarkFeedback}</span>
        </div>
      )}

      {/* Official Directory Disclaimer */}
      <div className="bg-[#FBF7EF] border border-[#E5DDCF] p-4 rounded-xl text-xs text-[#292B26]/80 flex items-start gap-3">
        <Info className="w-5 h-5 text-[#103D2C] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div>
            <span className="font-bold text-[#103D2C]">Official Gazette Notice: </span>
            All listed schemes link directly to verified government domain portals (<code className="bg-white px-1 py-0.5 rounded border border-[#E5DDCF]">.gov.in</code> / <code className="bg-white px-1 py-0.5 rounded border border-[#E5DDCF]">.nic.in</code>).
            KISANcare does not charge application fees or process claims. Eligibility criteria and disbursements are subject to verification by the respective implementing departments.
          </div>
          <div className="text-[11px] text-[#292B26]/60">
            * Bookmarked schemes are stored locally in your browser storage for fast offline reference.
          </div>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] space-y-4">
        {/* Row 1: Search and Active Filter Summary */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-xl">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-[#292B26]/40" />
            <input
              type="text"
              placeholder="Search by scheme name, acronym, keyword (e.g., subsidy, drip, KCC, ₹6000)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs sm:text-sm focus:outline-none focus:border-[#17643E]"
            />
          </div>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="self-start md:self-auto text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <RotateCcw size={13} />
              <span>Reset All Filters</span>
            </button>
          )}
        </div>

        {/* Row 2: Category Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <span className="text-xs font-semibold text-[#292B26]/70 flex items-center gap-1 shrink-0">
            <Filter size={12} /> Category:
          </span>
          {['All', 'Financial Support', 'Crop Insurance', 'Credit & Loans', 'Irrigation & Soil', 'Machinery'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-[#103D2C] text-white border-[#103D2C] font-semibold shadow-xs'
                  : 'bg-[#FBF7EF] text-[#292B26]/80 border-[#E5DDCF] hover:border-[#17643E]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Row 3: Eligibility Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#E5DDCF]/60">
          <span className="text-xs font-semibold text-[#292B26]/70 flex items-center gap-1 shrink-0">
            <ShieldCheck size={13} className="text-[#17643E]" /> Farmer Eligibility:
          </span>
          {ELIGIBILITY_OPTIONS.map((elig) => (
            <button
              key={elig}
              onClick={() => setSelectedEligibility(elig)}
              className={`text-xs px-3 py-1 rounded-lg border transition-all whitespace-nowrap cursor-pointer ${
                selectedEligibility === elig
                  ? 'bg-[#17643E] text-white border-[#17643E] font-medium shadow-xs'
                  : 'bg-white text-[#292B26]/80 border-[#E5DDCF] hover:border-[#17643E] hover:bg-[#FBF7EF]'
              }`}
            >
              {elig}
            </button>
          ))}
        </div>
      </div>

      {/* Schemes Directory List */}
      <div className="space-y-4">
        {filteredSchemes.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] space-y-3">
            <Landmark className="w-12 h-12 text-[#A8C69A] mx-auto" />
            <h3 className="font-bold text-[#103D2C] text-base">No Matching Schemes Found</h3>
            <p className="text-xs text-[#292B26]/70 max-w-md mx-auto">
              {showSavedOnly
                ? "You haven't bookmarked any schemes yet, or none match the active search/filter criteria. Click the bookmark icon on any scheme to save it for quick reference."
                : `No government scheme matches your filter criteria (Category: "${selectedCategory}", Eligibility: "${selectedEligibility}"${searchTerm ? `, Query: "${searchTerm}"` : ''}).`}
            </p>
            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#103D2C] hover:bg-[#17643E] text-white px-4 py-2 rounded-lg transition-colors cursor-pointer mt-2"
              >
                <RotateCcw size={13} />
                <span>Clear All Active Filters</span>
              </button>
            )}
          </div>
        ) : (
          filteredSchemes.map((scheme) => {
            const isExpanded = expandedSchemeId === scheme.id;
            const isBookmarked = bookmarkedIds.includes(scheme.id);

            return (
              <div
                key={scheme.id}
                className="bg-white rounded-2xl border border-[#E5DDCF] shadow-xs overflow-hidden transition-all hover:border-[#17643E]/50"
              >
                {/* Header Row */}
                <div
                  onClick={() => toggleExpand(scheme.id)}
                  className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-11 h-11 rounded-xl bg-[#103D2C]/10 text-[#103D2C] flex items-center justify-center shrink-0">
                      <Landmark size={22} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm bg-[#FBF7EF] text-[#103D2C] px-2 py-0.5 rounded border border-[#E5DDCF]">
                          {scheme.acronym}
                        </span>
                        <h3 className="text-base font-bold text-[#103D2C]">{scheme.name}</h3>
                        <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle size={11} className="text-emerald-600" /> Verified
                        </span>
                      </div>
                      <p className="text-xs text-[#292B26]/60 mt-1">{scheme.ministry}</p>
                      <p className="text-xs font-medium text-[#292B26] mt-2">{scheme.benefitSummary}</p>

                      {/* Eligibility Tags */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        {scheme.eligibilityTypes.map((et) => (
                          <span
                            key={et}
                            className="text-[10px] bg-[#FBF7EF] text-[#103D2C]/80 border border-[#E5DDCF] px-2 py-0.5 rounded-md font-medium"
                          >
                            {et}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                    {/* Bookmark Button */}
                    <button
                      type="button"
                      onClick={(e) => toggleBookmark(scheme.id, scheme.name, e)}
                      title={isBookmarked ? 'Remove bookmark' : 'Bookmark this scheme (stored locally)'}
                      className={`p-2 rounded-lg border transition-colors cursor-pointer ${
                        isBookmarked
                          ? 'bg-amber-50 border-amber-300 text-amber-600'
                          : 'bg-[#FBF7EF] border-[#E5DDCF] text-[#292B26]/60 hover:text-[#103D2C] hover:border-[#103D2C]'
                      }`}
                    >
                      <Bookmark size={16} className={isBookmarked ? 'fill-amber-500' : ''} />
                    </button>

                    <span className="text-xs font-semibold text-[#103D2C] bg-[#FBF7EF] px-3 py-1 rounded-full border border-[#E5DDCF]">
                      {scheme.category}
                    </span>

                    <button
                      type="button"
                      className="p-1.5 text-[#103D2C] hover:bg-[#FBF7EF] rounded-lg transition-colors cursor-pointer"
                      title={isExpanded ? 'Collapse' : 'Expand Details'}
                    >
                      {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </button>
                  </div>
                </div>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div className="p-6 bg-[#FBF7EF] border-t border-[#E5DDCF] space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Benefits */}
                      <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-2">
                        <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                          <CheckCircle size={14} className="text-[#17643E]" /> Detailed Benefits
                        </h4>
                        <ul className="text-xs text-[#292B26]/80 space-y-1.5 list-disc pl-4">
                          {scheme.detailedBenefits.map((b, i) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Eligibility */}
                      <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-2">
                        <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                          <ShieldCheck size={14} className="text-[#17643E]" /> Eligibility Criteria
                        </h4>
                        <ul className="text-xs text-[#292B26]/80 space-y-1.5 list-disc pl-4">
                          {scheme.eligibility.map((e, i) => (
                            <li key={i}>{e}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Required Documents */}
                      <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-2">
                        <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                          <FileText size={14} className="text-[#17643E]" /> Required Documents
                        </h4>
                        <ul className="text-xs text-[#292B26]/80 space-y-1.5 list-disc pl-4">
                          {scheme.requiredDocuments.map((d, i) => (
                            <li key={i}>{d}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-3 border-t border-[#E5DDCF]">
                      <div className="text-[11px] text-[#292B26]/60">
                        Official Government Portal: <span className="font-mono text-[#103D2C]">{scheme.officialUrl}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={(e) => toggleBookmark(scheme.id, scheme.name, e)}
                          className={`text-xs px-3 py-2 rounded-lg font-medium flex items-center gap-1.5 border transition-colors cursor-pointer ${
                            isBookmarked
                              ? 'bg-amber-50 text-amber-800 border-amber-300'
                              : 'bg-white text-[#103D2C] border-[#E5DDCF] hover:border-[#17643E]'
                          }`}
                        >
                          <Bookmark size={13} className={isBookmarked ? 'fill-amber-500' : ''} />
                          <span>{isBookmarked ? 'Bookmarked' : 'Save Scheme'}</span>
                        </button>
                        <a
                          href={scheme.officialUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-colors shadow-xs"
                        >
                          <span>Visit Official Portal</span>
                          <ExternalLink size={13} />
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
