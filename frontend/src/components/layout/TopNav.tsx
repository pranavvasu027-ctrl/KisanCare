import React from 'react';
import { Search, Bell, LogOut } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { changeLanguage, SupportedLanguage } from '../../i18n';

const TopNav = () => {
  const { signOut, user, role, isDemoMode } = useAuth();
  const { t, i18n } = useTranslation();

  const currentLang = (['en', 'mr', 'hi'].includes(i18n.language) ? i18n.language : 'en') as SupportedLanguage;

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value as SupportedLanguage;
    changeLanguage(selected);
  };

  return (
    <header className="h-16 bg-[#FBF7EF] border-b border-[#E5DDCF] flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center space-x-4 flex-1">
        <div className="relative w-96">
          <input
            type="text"
            placeholder={t('nav.searchPlaceholder')}
            className="w-full pl-10 pr-4 py-2 bg-white border border-[#E5DDCF] rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-[#A8C69A]"
          />
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
        </div>
      </div>

      <div className="flex items-center space-x-6">
        {isDemoMode && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            {t('nav.demoBadge')}
          </span>
        )}

        <div className="flex items-center space-x-2 border-r border-[#E5DDCF] pr-6">
          <span className="text-sm text-gray-500">{t('nav.currentFarm')}</span>
          <select className="bg-transparent text-sm font-medium focus:outline-none text-[#103D2C] cursor-pointer">
            <option>Pranav Vasu Farm (10.0 ac)</option>
          </select>
        </div>

        <div className="flex items-center space-x-2 border-r border-[#E5DDCF] pr-6">
          <select
            value={currentLang}
            onChange={handleLanguageChange}
            aria-label={t('nav.language')}
            className="bg-transparent text-sm focus:outline-none font-medium text-[#103D2C] cursor-pointer hover:text-[#17643E]"
          >
            <option value="en">English</option>
            <option value="mr">मराठी (Marathi)</option>
            <option value="hi">हिन्दी (Hindi)</option>
          </select>
        </div>

        <button className="text-gray-500 hover:text-[#103D2C] relative" aria-label={t('nav.notifications')}>
          <Bell size={20} />
          <span className="absolute -top-1 -right-1 bg-[#B6532A] w-2 h-2 rounded-full"></span>
        </button>

        <div className="flex items-center space-x-3 ml-2 border-l border-[#E5DDCF] pl-4">
          <div className="flex flex-col text-right">
            <span className="text-sm font-medium text-[#103D2C]">
              {isDemoMode ? 'Pranav Vasu (Demo)' : user?.user_metadata?.name || user?.email?.split('@')[0] || 'Pranav Vasu'}
            </span>
            <span className="text-xs text-gray-500">{role ? t(`common.${role}`, role) : t('nav.farmer')}</span>
          </div>
          <button
            onClick={signOut}
            title={isDemoMode ? t('nav.demoNotice') : t('nav.logout')}
            disabled={isDemoMode}
            className="flex items-center space-x-2 w-8 h-8 rounded-full bg-red-100 hover:bg-red-200 flex items-center justify-center text-red-700 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
