import { useTranslation } from 'react-i18next';
import React from 'react';
import { Lightbulb, CheckCircle2, AlertTriangle, ArrowRight, ThumbsUp, ThumbsDown } from 'lucide-react';
import { translateDynamic } from '../../i18n/translateHelper';

export default function AiRecommendation() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  return (
    <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-serif font-bold text-[#103D2C]">{t('aiRecommendation.title')}</h1>
        <p className="text-[#292B26]/70 mt-1">{t('aiRecommendation.subtitle')}</p>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="bg-[#17643E] p-6 text-white flex items-start gap-4">
          <div className="bg-white/20 p-3 rounded-2xl">
            <Lightbulb className="w-8 h-8 text-white" />
          </div>
          <div>
            <span className="text-[#A8C69A] text-sm font-semibold uppercase tracking-wider mb-1 block">{t('aiRecommendation.priorityAction')}</span>
            <h2 className="text-2xl font-bold">
              {currentLang === 'mr'
                ? 'पुढील ४८ तासांत शेत २ मध्ये सिंचनाचा विचार करा'
                : currentLang === 'hi'
                ? 'अगले ४८ घंटों के भीतर खेत २ में सिंचाई पर विचार करें'
                : 'Consider Irrigation in Field 2 within 48 Hours'}
            </h2>
            <p className="text-white/80 mt-2 max-w-2xl">
              {currentLang === 'mr'
                ? 'वाढीच्या संवेदनशील टप्प्यात जमिनीतील ओलावा आवश्यक पातळीपेक्षा कमी आहे. आता सिंचन केल्यास उत्पादनातील घट टाळता येईल.'
                : currentLang === 'hi'
                ? 'विकास के महत्वपूर्ण चरण में मिट्टी की नमी आवश्यक स्तर से कम है। अभी सिंचाई करने से पैदावार में कमी से बचा जा सकता है।'
                : 'Soil moisture is below optimal levels during a critical growth stage. Irrigating now can prevent yield loss.'}
            </p>
          </div>
        </div>

        <div className="p-6 lg:p-8 space-y-8">
          <div>
            <h3 className="text-lg font-bold text-[#103D2C] mb-4 flex items-center gap-2">
              <CheckCircle2 className="text-[#17643E] w-5 h-5" /> {t('aiRecommendation.whyRecommended')}
            </h3>
            <div className="bg-[#FBF7EF] rounded-xl p-5 space-y-3 border border-[#E5DDCF]">
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm">
                  <strong className="text-[#103D2C]">{currentLang === 'mr' ? 'मातीतील ओलावा (मॉडेल २):' : currentLang === 'hi' ? 'मिट्टी की नमी (मॉडल २):' : 'Soil Moisture (Model 2):'}</strong>{' '}
                  {currentLang === 'mr' ? 'सध्या १४% वर आहे. कापूस पिकासाठी फुलधारणेच्या टप्प्यात योग्य पातळी २२-२५% आहे.' : currentLang === 'hi' ? 'वर्तमान में १४% है। फूल आने के चरण में कपास के लिए उपयुक्त स्तर २२-२५% है।' : 'Currently at 14%. Optimal for Cotton at flowering stage is 22-25%.'}
                </p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm">
                  <strong className="text-[#103D2C]">{currentLang === 'mr' ? 'हवामान अंदाज:' : currentLang === 'hi' ? 'मौसम पूर्वानुमान:' : 'Weather Forecast:'}</strong>{' '}
                  {currentLang === 'mr' ? 'पुढील ७ दिवसांत पावसाची शक्यता नाही. जास्त तापमानामुळे पाण्याचे बाष्पीभवन वाढेल.' : currentLang === 'hi' ? 'अगले ७ दिनों में बारिश की संभावना नहीं है। उच्च तापमान से वाष्पीकरण बढ़ेगा।' : 'No rain expected in the next 7 days. High temperatures will increase evaporation.'}
                </p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm">
                  <strong className="text-[#103D2C]">{currentLang === 'mr' ? 'उत्पादनावरील परिणाम:' : currentLang === 'hi' ? 'पैदावार पर प्रभाव:' : 'Yield Impact:'}</strong>{' '}
                  {currentLang === 'mr' ? 'फुलधारणेच्या वेळी पाण्याचा ताण आल्यास बोंडे गळू शकतात, ज्यामुळे उत्पादनात ८-१२% घट होऊ शकते.' : currentLang === 'hi' ? 'फूल आने के दौरान पानी का तनाव होने से डोंडे गिर सकते हैं, जिससे पैदावार में ८-१२% तक कमी हो सकती है।' : 'Stress during flowering can reduce boll retention, potentially lowering yield by 8-12%.'}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-md font-bold text-[#103D2C] mb-3">{t('aiRecommendation.expectedBenefits')}</h3>
              <div className="border border-[#A8C69A] rounded-xl p-4 bg-[#A8C69A]/10 text-sm text-[#103D2C] space-y-2">
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> {currentLang === 'mr' ? 'अपेक्षित उत्पादन सुरक्षित राहील' : currentLang === 'hi' ? 'अपेक्षित पैदावार सुरक्षित रहेगी' : 'Secure expected yield'}</div>
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> {currentLang === 'mr' ? 'रोपांची सशक्त वाढ कायम राहील' : currentLang === 'hi' ? 'पौधों का स्वास्थ्य बना रहेगा' : 'Maintain plant vigor'}</div>
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> {currentLang === 'mr' ? 'अन्नद्रव्यांचे शोषण सुरळीत होईल' : currentLang === 'hi' ? 'पोषक तत्वों का बेहतर अवशोषण' : 'Better nutrient uptake'}</div>
              </div>
            </div>
            <div>
              <h3 className="text-md font-bold text-[#103D2C] mb-3">{t('aiRecommendation.costsRisks')}</h3>
              <div className="border border-[#E5DDCF] rounded-xl p-4 bg-white text-sm text-[#292B26]/80 space-y-2">
                <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-[#B6532A]" /> {currentLang === 'mr' ? 'पंपिंग वीज खर्च' : currentLang === 'hi' ? 'पंपिंग बिजली खर्च' : 'Pumping electricity cost'}</div>
                <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-[#B6532A]" /> {currentLang === 'mr' ? 'जलस्रोताचा वापर' : currentLang === 'hi' ? 'जल संसाधन का उपयोग' : 'Water resource usage'}</div>
              </div>
            </div>
          </div>

          <div className="border-t border-[#E5DDCF] pt-6 flex justify-between items-center">
            <div className="text-sm text-[#292B26]/60">{t('aiRecommendation.helpfulFeedback')}</div>
            <div className="flex gap-2">
              <button className="p-2 border border-[#E5DDCF] rounded-lg text-[#292B26]/60 hover:text-[#17643E] hover:bg-[#FBF7EF]"><ThumbsUp size={18} /></button>
              <button className="p-2 border border-[#E5DDCF] rounded-lg text-[#292B26]/60 hover:text-[#B6532A] hover:bg-[#FBF7EF]"><ThumbsDown size={18} /></button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
