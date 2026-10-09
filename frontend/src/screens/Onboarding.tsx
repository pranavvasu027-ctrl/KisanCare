import React, { useState } from 'react';
import { 
  Leaf, TrendingUp, ShieldCheck, Droplets, Sprout, BarChart2, 
  Phone, Lock, EyeOff, CheckCircle2, User, Users, MapPin, 
  ArrowRight, Search, Check, Globe
} from 'lucide-react';

export default function Onboarding() {
  const [language, setLanguage] = useState('English');
  const [role, setRole] = useState('Farmer');

  return (
    <div className="flex h-screen w-full bg-[#f4f7f6] overflow-hidden text-gray-800 font-sans">
      {/* LEFT AREA: Background + Branding + Login Card */}
      <div 
        className="w-[70%] relative flex p-10"
        style={{
          backgroundImage: 'linear-gradient(to right, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.8) 40%, rgba(255, 255, 255, 0) 100%), url("https://images.unsplash.com/photo-1592982537447-6f2a6a0c5989?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80")',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        {/* Left Branding Content */}
        <div className="w-[55%] flex flex-col justify-between z-10 h-full">
          
          {/* Header / Logo */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <Leaf className="w-8 h-8 text-green-700" />
              <div>
                <h1 className="text-3xl font-bold text-green-900 tracking-tight">
                  KISAN<span className="text-amber-700 font-normal">care</span>
                </h1>
                <p className="text-xs text-gray-600 font-medium tracking-wide">Smarter Farms • Better Tomorrows</p>
              </div>
            </div>
            <div className="text-sm font-medium text-gray-700 opacity-80 italic text-right leading-tight">
              मातीशी नाते,<br/> उद्याच्या समृद्धीसाठी <Leaf className="w-3 h-3 inline text-green-600"/>
            </div>
          </div>

          {/* Hero Text & Features */}
          <div className="mt-12">
            <h2 className="text-5xl font-bold text-green-950 leading-tight mb-2">
              Your Farm.<br/>
              Smarter Decisions.<br/>
              <span className="text-amber-700">Brighter Tomorrows.</span>
            </h2>
            <p className="text-lg text-gray-700 mt-4 mb-8 max-w-md leading-relaxed">
              AI-powered insights for healthier crops, higher profits and a more resilient future.
            </p>

            <div className="grid grid-cols-2 gap-y-6 gap-x-4 max-w-lg">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><Leaf className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Personalized<br/>Crop Guidance</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><TrendingUp className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Higher<br/>Profitability</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><ShieldCheck className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Lower<br/>Risk</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><Droplets className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Better<br/>Water Use</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><Sprout className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Healthier<br/>Soil</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-lg text-green-700"><BarChart2 className="w-5 h-5"/></div>
                <span className="font-semibold text-sm">Data-Driven<br/>Decisions</span>
              </div>
            </div>
          </div>

          {/* Bottom Quote & Trust Badges */}
          <div className="mt-auto">
            <div className="bg-green-950 text-white p-5 rounded-2xl max-w-sm relative shadow-xl">
              <span className="absolute -top-4 -left-2 text-6xl text-green-700 opacity-50 font-serif">"</span>
              <p className="text-lg font-medium relative z-10">Growing today,<br/><span className="text-green-300 font-light">for a healthier tomorrow. <Leaf className="w-4 h-4 inline"/></span></p>
            </div>
            
            <div className="flex items-center gap-6 mt-6 text-xs text-white bg-green-950/80 p-3 rounded-xl max-w-md backdrop-blur-sm">
              <div className="flex items-center gap-1"><ShieldCheck className="w-4 h-4 text-green-400"/> Your data is secure</div>
              <div className="flex items-center gap-1"><Users className="w-4 h-4 text-green-400"/> Farmer-owned data</div>
              <div className="flex items-center gap-1"><Lock className="w-4 h-4 text-green-400"/> Privacy first</div>
            </div>
          </div>
        </div>

        {/* Right side of Left Area: Login Card */}
        <div className="w-[45%] flex items-center justify-center relative z-10 pl-10">
          <div className="bg-[#fcfcf9] w-[420px] rounded-[2rem] shadow-2xl p-8 flex flex-col h-full max-h-[750px] relative overflow-hidden">
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-gray-800">Welcome to</h3>
              <h2 className="text-3xl font-bold text-amber-800 tracking-tight">KISAN<span className="text-green-900">care</span></h2>
              <p className="text-gray-500 mt-2">Sign in to your account</p>
            </div>

            <div className="space-y-5 flex-1 relative z-10">
              {/* Mobile Number Input */}
              <div>
                <div className="flex items-center border border-gray-300 rounded-xl px-4 py-3 bg-white focus-within:border-green-600 focus-within:ring-1 focus-within:ring-green-600 transition-all">
                  <Phone className="w-5 h-5 text-green-700 mr-3" />
                  <span className="text-gray-800 font-medium mr-2 pr-2">+91</span>
                  <input 
                    type="text" 
                    placeholder="Enter your mobile number" 
                    className="w-full outline-none text-gray-700 bg-transparent text-sm placeholder-gray-400"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <div className="flex items-center border border-gray-300 rounded-xl px-4 py-3 bg-white focus-within:border-green-600 focus-within:ring-1 focus-within:ring-green-600 transition-all">
                  <Lock className="w-5 h-5 text-gray-400 mr-3" />
                  <input 
                    type="password" 
                    placeholder="Enter your password" 
                    className="w-full outline-none text-gray-700 bg-transparent text-sm placeholder-gray-400"
                  />
                  <EyeOff className="w-5 h-5 text-gray-400 ml-3 cursor-pointer" />
                </div>
              </div>

              {/* Remember & Forgot */}
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-gray-600 cursor-pointer">
                  <input type="checkbox" className="rounded border-gray-300 text-green-700 focus:ring-green-600 w-4 h-4 accent-green-700" />
                  Remember me
                </label>
                <a href="#" className="text-green-700 font-medium hover:underline">Forgot password?</a>
              </div>

              {/* Sign In Button */}
              <button className="w-full bg-green-950 text-white rounded-xl py-3 font-medium flex items-center justify-center gap-2 hover:bg-green-900 transition-colors shadow-lg shadow-green-900/20">
                Sign In <ArrowRight className="w-4 h-4" />
              </button>

              {/* Divider */}
              <div className="flex items-center gap-3 my-6 text-gray-400 text-sm">
                <div className="h-px bg-gray-200 flex-1"></div>
                <span className="text-xs">or continue with</span>
                <div className="h-px bg-gray-200 flex-1"></div>
              </div>

              {/* Social Logins */}
              <div className="flex gap-3">
                <button className="flex-1 flex flex-col items-center justify-center gap-2 border border-gray-200 rounded-xl py-2 px-1 bg-white hover:bg-gray-50 transition-colors">
                  <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-5 h-5" />
                  <span className="text-[11px] font-medium text-gray-600">Google</span>
                </button>
                <button className="flex-1 flex flex-col items-center justify-center gap-2 border border-gray-200 rounded-xl py-2 px-1 bg-white hover:bg-gray-50 transition-colors">
                  <img src="https://www.svgrepo.com/show/512315/apple-173.svg" alt="Apple" className="w-5 h-5 opacity-80" />
                  <span className="text-[11px] font-medium text-gray-600">Apple</span>
                </button>
                <button className="flex-1 flex flex-col items-center justify-center gap-2 border border-gray-200 rounded-xl py-2 px-1 bg-white hover:bg-gray-50 transition-colors">
                  <img src="https://www.svgrepo.com/show/475661/microsoft-color.svg" alt="Microsoft" className="w-5 h-5" />
                  <span className="text-[11px] font-medium text-gray-600">Microsoft</span>
                </button>
              </div>
            </div>

            <div className="mt-6 text-center text-sm text-gray-600 relative z-10">
              New to KISANcare? <a href="#" className="text-green-800 font-semibold hover:underline border-b border-green-800 pb-0.5">Create an account</a>
            </div>

            {/* Decorative bottom illustration (placeholder pattern) */}
            <div 
              className="absolute bottom-0 left-0 w-full h-32 opacity-30 rounded-b-[2rem] pointer-events-none"
              style={{
                backgroundImage: 'url("https://www.transparenttextures.com/patterns/black-scales.png")',
                backgroundSize: 'cover'
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* RIGHT AREA: Onboarding Sidebar */}
      <div className="w-[30%] bg-[#fafaf9] border-l border-gray-200 h-full flex flex-col overflow-y-auto z-20 shadow-[-10px_0_20px_rgba(0,0,0,0.03)] relative">
        <div className="p-8 flex-1">
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-12 relative px-2">
            <div className="absolute top-4 left-4 right-4 h-0.5 bg-gray-200 -z-10"></div>
            
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-green-800 text-white flex items-center justify-center text-sm font-bold shadow-md">1</div>
              <span className="text-[10px] font-medium text-green-900">Language</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white border border-gray-300 text-gray-400 flex items-center justify-center text-sm font-bold">2</div>
              <span className="text-[10px] font-medium text-gray-400">Farm Info</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white border border-gray-300 text-gray-400 flex items-center justify-center text-sm font-bold">3</div>
              <span className="text-[10px] font-medium text-gray-400">Preferences</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white border border-gray-300 text-gray-400 flex items-center justify-center text-sm font-bold">4</div>
              <span className="text-[10px] font-medium text-gray-400">Complete</span>
            </div>
          </div>

          {/* Section 1: Language */}
          <div className="mb-10">
            <div className="flex items-center gap-2 mb-2">
              <Sprout className="w-5 h-5 text-green-800" />
              <h3 className="text-xl font-bold text-gray-800">Choose Your Language</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4 ml-7">Select the language you are most comfortable with</p>
            
            <div className="flex gap-3 ml-7">
              {['English', 'Hindi', 'Marathi'].map((lang) => {
                const isSelected = language === lang;
                return (
                  <div 
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    className={`flex-1 flex flex-col items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all relative ${
                      isSelected 
                        ? 'border-green-700 bg-green-50 shadow-sm' 
                        : 'border-gray-200 bg-white hover:border-green-300'
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute -top-2 -right-2 bg-green-700 text-white rounded-full p-0.5 shadow-sm">
                        <Check className="w-3 h-3" />
                      </div>
                    )}
                    <span className={`text-2xl mb-2 font-serif ${isSelected ? 'text-green-800' : 'text-gray-600'}`}>
                      {lang === 'English' ? 'Aअ' : 'अ'}
                    </span>
                    <span className={`font-semibold text-sm ${isSelected ? 'text-green-900' : 'text-gray-700'}`}>
                      {lang === 'Hindi' ? 'हिंदी' : lang === 'Marathi' ? 'मराठी' : 'English'}
                    </span>
                    <span className={`text-[9px] mt-1 text-center leading-tight ${isSelected ? 'text-green-700' : 'text-gray-400'}`}>
                      {lang === 'English' && 'Continue in English'}
                      {lang === 'Hindi' && 'हिंदी में जारी रखें'}
                      {lang === 'Marathi' && 'मराठीत सुरू ठेवा'}
                    </span>
                  </div>
                )
              })}
            </div>
            <p className="text-xs text-center text-gray-400 mt-4 ml-7">You can change the language anytime in settings.</p>
          </div>

          {/* Section 2: Tell us about yourself */}
          <div className="mb-10">
            <div className="flex items-center gap-2 mb-2">
              <Sprout className="w-5 h-5 text-green-800" />
              <h3 className="text-xl font-bold text-gray-800">Tell us about yourself</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4 ml-7">This helps us personalize your experience</p>
            
            <div className="flex gap-4 ml-7">
              {[
                { id: 'Farmer', icon: User, desc: 'I grow crops on my own or family land' },
                { id: 'Agri Professional', icon: Users, desc: 'Advisor, dealer, researcher or service provider' }
              ].map((item) => {
                const isSelected = role === item.id;
                const Icon = item.icon;
                return (
                  <div 
                    key={item.id}
                    onClick={() => setRole(item.id)}
                    className={`flex-1 flex flex-col items-center justify-center p-5 rounded-xl border-2 cursor-pointer transition-all relative text-center ${
                      isSelected 
                        ? 'border-green-700 bg-green-50 shadow-sm' 
                        : 'border-gray-200 bg-white hover:border-green-300'
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute -top-2 -right-2 bg-green-700 text-white rounded-full p-0.5 shadow-sm">
                        <Check className="w-3 h-3" />
                      </div>
                    )}
                    <Icon className={`w-8 h-8 mb-3 ${isSelected ? 'text-green-800' : 'text-gray-600'}`} />
                    <span className={`font-semibold text-sm mb-1 ${isSelected ? 'text-green-900' : 'text-gray-800'}`}>
                      I am a {item.id}
                    </span>
                    <span className={`text-[10px] leading-tight ${isSelected ? 'text-green-700' : 'text-gray-500'}`}>
                      {item.desc}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Section 3: Location */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-green-800" />
              <h3 className="text-xl font-bold text-gray-800">Your Location</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4 ml-7">
              This helps us provide local weather, market prices and relevant recommendations
            </p>
            
            <div className="ml-7 flex items-center border-2 border-gray-200 rounded-xl px-4 py-3 bg-white focus-within:border-green-600 transition-colors">
              <Search className="w-5 h-5 text-gray-400 mr-3" />
              <input 
                type="text" 
                placeholder="Enter your village, city or PIN code" 
                className="w-full outline-none text-gray-700 text-sm"
              />
              <MapPin className="w-5 h-5 text-green-600 ml-3 cursor-pointer" />
            </div>
          </div>
        </div>

        {/* Footer Next Button */}
        <div className="p-8 pt-4 bg-[#fafaf9] mt-auto">
          <button className="w-full bg-green-950 text-white rounded-xl py-3.5 font-semibold text-base flex items-center justify-center gap-2 hover:bg-green-900 transition-colors shadow-lg shadow-green-900/20">
            Next <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
