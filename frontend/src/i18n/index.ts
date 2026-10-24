import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import mr from './locales/mr.json';
import hi from './locales/hi.json';

export type SupportedLanguage = 'en' | 'mr' | 'hi';

// Determine initial language from localStorage or default to 'en'
const getInitialLanguage = (): SupportedLanguage => {
  try {
    const saved = localStorage.getItem('kisanCareLanguage');
    if (saved && (saved === 'en' || saved === 'mr' || saved === 'hi')) {
      return saved;
    }
    // Check kisancare_user_preferences as secondary source
    const userPrefs = localStorage.getItem('kisancare_user_preferences');
    if (userPrefs) {
      const parsed = JSON.parse(userPrefs);
      if (parsed.preferredLanguage && (parsed.preferredLanguage === 'en' || parsed.preferredLanguage === 'mr' || parsed.preferredLanguage === 'hi')) {
        return parsed.preferredLanguage;
      }
    }
  } catch (e) {
    console.error('Error reading saved language:', e);
  }
  return 'en';
};

const initialLang = getInitialLanguage();

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      mr: { translation: mr },
      hi: { translation: hi }
    },
    lng: initialLang,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false // React already escapes values
    },
    react: {
      useSuspense: false
    },
    returnEmptyString: false,
    returnNull: false
  });

export const changeLanguage = (lang: SupportedLanguage) => {
  i18n.changeLanguage(lang);
  try {
    localStorage.setItem('kisanCareLanguage', lang);
    // Also keep preferences sync
    const userPrefs = localStorage.getItem('kisancare_user_preferences');
    if (userPrefs) {
      const parsed = JSON.parse(userPrefs);
      parsed.preferredLanguage = lang;
      localStorage.setItem('kisancare_user_preferences', JSON.stringify(parsed));
    }
  } catch (err) {
    console.warn('Could not save language to localStorage:', err);
  }
};

export default i18n;
