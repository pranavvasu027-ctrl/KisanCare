import React, { useState } from 'react';
import { 
  Leaf, TrendingUp, ShieldCheck, Droplets, Sprout, BarChart2, 
  Phone, Lock, EyeOff, Eye, User, Users, MapPin, 
  ArrowRight, Search, Check, Globe, Navigation, ArrowLeft, CheckCircle2
} from 'lucide-react';

export default function Onboarding({ onComplete }: { onComplete?: () => void }) {
  // Navigation State
  const [step, setStep] = useState(1);

  // Login State
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginMsg, setLoginMsg] = useState<{type: 'error' | 'info' | 'success', text: string} | null>(null);

  // Onboarding State
  const [language, setLanguage] = useState('English');
  const [role, setRole] = useState('Farmer');
  const [farmName, setFarmName] = useState('');
  const [location, setLocation] = useState('');
  const [preferences, setPreferences] = useState<string[]>([]);
  const [locationLoading, setLocationLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoginMsg(null);

    if (!mobile) {
      setLoginMsg({ type: 'error', text: 'Please enter a valid mobile number.' });
      return;
    }
    if (!password) {
      setLoginMsg({ type: 'error', text: 'Password is required.' });
      return;
    }

    setIsLoggingIn(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoggingIn(false);
      setLoginMsg({ 
        type: 'info', 
        text: 'Authentication is not yet connected to a backend service. This is a frontend demo.' 
      });
    }, 1200);
  };

  const handleSocialLogin = (provider: string) => {
    setLoginMsg({ 
      type: 'info', 
      text: `${provider} sign-in is not yet configured in this environment.` 
    });
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setLocationLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation(`${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`);
        setLocationLoading(false);
      },
      (error) => {
        console.warn(error);
        alert('Unable to retrieve your location. Please enter it manually.');
        setLocationLoading(false);
      }
    );
  };

  const togglePreference = (pref: string) => {
    setPreferences(prev => 
      prev.includes(pref) ? prev.filter(p => p !== pref) : [...prev, pref]
    );
  };

  const nextStep = () => {
    if (step === 1 && !language) {
      alert("Please select a language.");
      return;
    }
    if (step === 2 && !role) {
      alert("Please select a role.");
      return;
    }
    setStep(s => Math.min(4, s + 1));
  };
  
  const prevStep = () => setStep(s => Math.max(1, s - 1));

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      alert("Navigating to KISANcare Home Dashboard... (Integration pending)");
    }
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen w-full bg-[#FBF7EF] text-[#292B26] font-sans">
      
      {/* REGION A & B: Hero & Login Card */}
      <div className="w-full lg:w-[65%] relative flex flex-col lg:flex-row p-6 lg:p-10 min-h-[600px] bg-[#103D2C]">
        {/* Background Layer */}
        <div 
          className="absolute inset-0 bg-cover bg-center mix-blend-overlay opacity-80 lg:opacity-100"
          style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1592982537447-6f2a6a0c5989?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80")' }}
        />
        {/* Gradients to make text readable */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#FBF7EF] via-[#FBF7EF]/90 to-transparent hidden lg:block" />
        <div className="absolute inset-0 bg-[#FBF7EF]/95 lg:hidden" />

        {/* Region A: Branding Content */}
        <div className="relative z-10 w-full lg:w-[55%] flex flex-col justify-between h-full">
          
          {/* Header / Logo */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <Leaf className="w-8 h-8 text-[#164B35]" />
              <div>
                <h1 className="text-3xl font-bold text-[#103D2C] tracking-tight font-serif">
                  KISAN<span className="text-[#B6532A] font-normal">care</span>
                </h1>
                <p className="text-xs text-[#292B26] font-medium tracking-wide">Smarter Farms • Better Tomorrows</p>
              </div>
            </div>
            <div className="hidden lg:block text-sm font-medium text-[#292B26] opacity-80 italic text-right leading-tight font-serif">
              मातीशी नाते,<br/> उद्याच्या समृद्धीसाठी <Leaf className="w-3 h-3 inline text-[#164B35]"/>
            </div>
          </div>

          {/* Hero Text & Features */}
          <div className="mt-12 lg:mt-0 flex-1 flex flex-col justify-center">
            <h2 className="text-4xl lg:text-5xl font-bold text-[#103D2C] leading-tight mb-2 font-serif">
              Your Farm.<br/>
              Smarter Decisions.<br/>
              <span className="text-[#B6532A]">Brighter Tomorrows.</span>
            </h2>
            <p className="text-lg text-[#292B26] mt-4 mb-8 max-w-md leading-relaxed">
              AI-powered insights for healthier crops, higher profits and a more resilient future.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-4 max-w-lg">
              {[
                { icon: Leaf, label: "Personalized Crop Guidance" },
                { icon: TrendingUp, label: "Higher Profitability" },
                { icon: ShieldCheck, label: "Lower Risk" },
                { icon: Droplets, label: "Better Water Use" },
                { icon: Sprout, label: "Healthier Soil" },
                { icon: BarChart2, label: "Data-Driven Decisions" }
              ].map((feature, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="bg-[#A8C69A]/30 p-2 rounded-lg text-[#164B35]">
                    <feature.icon className="w-5 h-5"/>
                  </div>
                  <span className="font-semibold text-sm">{feature.label.split(' ').slice(0,-1).join(' ')}<br/>{feature.label.split(' ').slice(-1)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Quote & Trust Badges */}
          <div className="mt-12 lg:mt-auto hidden sm:block">
            <div className="bg-[#103D2C] text-white p-5 rounded-2xl max-w-sm relative shadow-xl">
              <span className="absolute -top-4 -left-2 text-6xl text-[#A8C69A] opacity-50 font-serif">"</span>
              <p className="text-lg font-medium relative z-10 font-serif">Growing today,<br/><span className="text-[#A8C69A] font-light">for a healthier tomorrow.</span></p>
            </div>
            
            <div className="flex flex-wrap items-center gap-4 lg:gap-6 mt-6 text-xs text-[#292B26] lg:text-white bg-[#FBF7EF]/80 lg:bg-[#103D2C]/90 p-3 rounded-xl max-w-md backdrop-blur-sm border border-[#E5DDCF] lg:border-transparent">
              <div className="flex items-center gap-1"><ShieldCheck className="w-4 h-4 text-[#164B35] lg:text-[#A8C69A]"/> Your data is secure</div>
              <div className="flex items-center gap-1"><Users className="w-4 h-4 text-[#164B35] lg:text-[#A8C69A]"/> Farmer-owned data</div>
              <div className="flex items-center gap-1"><Lock className="w-4 h-4 text-[#164B35] lg:text-[#A8C69A]"/> Privacy first</div>
            </div>
          </div>
        </div>

        {/* Region B: Login Card */}
        <div className="relative z-10 w-full lg:w-[45%] flex items-center justify-center lg:pl-10 mt-10 lg:mt-0">
          <div className="bg-[#FBF7EF] w-full max-w-[420px] rounded-[2rem] shadow-2xl p-6 sm:p-8 flex flex-col relative border border-[#E5DDCF]">
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-[#292B26] font-serif">Welcome to</h3>
              <h2 className="text-3xl font-bold text-[#B6532A] tracking-tight font-serif">KISAN<span className="text-[#103D2C]">care</span></h2>
              <p className="text-[#292B26]/70 mt-2 text-sm">Sign in to your account</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-5">
              {loginMsg && (
                <div className={`p-3 rounded-xl text-sm ${loginMsg.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                  {loginMsg.text}
                </div>
              )}

              {/* Mobile Number Input */}
              <div>
                <label className="sr-only">Mobile Number</label>
                <div className="flex items-center border border-[#E5DDCF] rounded-xl px-4 py-3 bg-white focus-within:border-[#164B35] focus-within:ring-1 focus-within:ring-[#164B35] transition-all shadow-sm">
                  <Phone className="w-5 h-5 text-[#164B35] mr-3" />
                  <span className="text-[#292B26] font-medium mr-2 pr-2 border-r border-[#E5DDCF]">+91</span>
                  <input 
                    type="tel" 
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    placeholder="Enter your mobile number" 
                    className="w-full outline-none text-[#292B26] bg-transparent text-sm placeholder-[#292B26]/40"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <label className="sr-only">Password</label>
                <div className="flex items-center border border-[#E5DDCF] rounded-xl px-4 py-3 bg-white focus-within:border-[#164B35] focus-within:ring-1 focus-within:ring-[#164B35] transition-all shadow-sm">
                  <Lock className="w-5 h-5 text-[#292B26]/40 mr-3" />
                  <input 
                    type={showPassword ? "text" : "password"} 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password" 
                    className="w-full outline-none text-[#292B26] bg-transparent text-sm placeholder-[#292B26]/40"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">
                    {showPassword ? <Eye className="w-5 h-5 text-[#292B26]/40 ml-3" /> : <EyeOff className="w-5 h-5 text-[#292B26]/40 ml-3" />}
                  </button>
                </div>
              </div>

              {/* Remember & Forgot */}
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-[#292B26]/80 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-[#E5DDCF] text-[#164B35] focus:ring-[#164B35] w-4 h-4 accent-[#164B35]" 
                  />
                  Remember me
                </label>
                <a href="#forgot" onClick={(e) => { e.preventDefault(); alert('Forgot password flow not implemented in this demo.'); }} className="text-[#164B35] font-medium hover:underline">Forgot password?</a>
              </div>

              {/* Sign In Button */}
              <button 
                type="submit"
                disabled={isLoggingIn}
                className="w-full bg-[#103D2C] text-white rounded-xl py-3 font-medium flex items-center justify-center gap-2 hover:bg-[#164B35] transition-colors shadow-lg shadow-[#103D2C]/20 disabled:opacity-70"
              >
                {isLoggingIn ? 'Signing in...' : (
                  <>Sign In <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-6 text-[#292B26]/40 text-sm">
              <div className="h-px bg-[#E5DDCF] flex-1"></div>
              <span className="text-xs font-medium">or continue with</span>
              <div className="h-px bg-[#E5DDCF] flex-1"></div>
            </div>

            {/* Social Logins */}
            <div className="flex gap-3">
              <button onClick={() => handleSocialLogin('Google')} className="flex-1 flex flex-col items-center justify-center gap-2 border border-[#E5DDCF] rounded-xl py-2 px-1 bg-white hover:bg-[#F2E8D5] transition-colors">
                <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-5 h-5" />
                <span className="text-[11px] font-medium text-[#292B26]/80">Google</span>
              </button>
              <button onClick={() => handleSocialLogin('Apple')} className="flex-1 flex flex-col items-center justify-center gap-2 border border-[#E5DDCF] rounded-xl py-2 px-1 bg-white hover:bg-[#F2E8D5] transition-colors">
                <img src="https://www.svgrepo.com/show/512315/apple-173.svg" alt="Apple" className="w-5 h-5 opacity-80" />
                <span className="text-[11px] font-medium text-[#292B26]/80">Apple</span>
              </button>
              <button onClick={() => handleSocialLogin('Microsoft')} className="flex-1 flex flex-col items-center justify-center gap-2 border border-[#E5DDCF] rounded-xl py-2 px-1 bg-white hover:bg-[#F2E8D5] transition-colors">
                <img src="https://www.svgrepo.com/show/475661/microsoft-color.svg" alt="Microsoft" className="w-5 h-5" />
                <span className="text-[11px] font-medium text-[#292B26]/80">Microsoft</span>
              </button>
            </div>

            <div className="mt-6 text-center text-sm text-[#292B26]/80 relative z-10">
              New to KISANcare? <a href="#create" onClick={(e) => { e.preventDefault(); setStep(1); document.getElementById('onboarding-panel')?.scrollIntoView({behavior: 'smooth'})}} className="text-[#103D2C] font-semibold hover:underline border-b border-[#103D2C] pb-0.5">Create an account</a>
            </div>
          </div>
        </div>
      </div>

      {/* REGION C: Onboarding Panel */}
      <div id="onboarding-panel" className="w-full lg:w-[35%] bg-[#FBF7EF] lg:border-l border-t lg:border-t-0 border-[#E5DDCF] flex flex-col relative z-20 shadow-[-10px_0_20px_rgba(0,0,0,0.02)] min-h-[600px]">
        <div className="p-6 lg:p-8 flex-1 flex flex-col">
          
          {/* Progress Steps Indicator */}
          <div className="flex items-center justify-between mb-10 relative px-2">
            <div className="absolute top-4 left-4 right-4 h-0.5 bg-[#E5DDCF] -z-10"></div>
            
            {[
              { num: 1, label: 'Language' },
              { num: 2, label: 'Farm Info' },
              { num: 3, label: 'Preferences' },
              { num: 4, label: 'Complete' }
            ].map(s => (
              <div key={s.num} className="flex flex-col items-center gap-2 bg-[#FBF7EF]">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-sm transition-colors ${step >= s.num ? 'bg-[#103D2C] text-white' : 'bg-white border border-[#E5DDCF] text-[#292B26]/40'}`}>
                  {step > s.num ? <Check className="w-4 h-4" /> : s.num}
                </div>
                <span className={`text-[10px] font-medium ${step >= s.num ? 'text-[#103D2C]' : 'text-[#292B26]/40'}`}>{s.label}</span>
              </div>
            ))}
          </div>

          {/* STEP CONTENT */}
          <div className="flex-1">
            {step === 1 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-5 h-5 text-[#164B35]" />
                  <h3 className="text-xl font-bold text-[#292B26] font-serif">Choose Your Language</h3>
                </div>
                <p className="text-sm text-[#292B26]/60 mb-6">Select the language you are most comfortable with.</p>
                
                <div className="space-y-3">
                  {[
                    { id: 'English', symbol: 'A', name: 'English', sub: 'Continue in English' },
                    { id: 'Hindi', symbol: 'अ', name: 'हिंदी', sub: 'हिंदी में जारी रखें' },
                    { id: 'Marathi', symbol: 'अ', name: 'मराठी', sub: 'मराठीत सुरू ठेवा' }
                  ].map((lang) => {
                    const isSelected = language === lang.id;
                    return (
                      <div 
                        key={lang.id}
                        onClick={() => setLanguage(lang.id)}
                        className={`flex items-center p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          isSelected ? 'border-[#164B35] bg-[#F2E8D5] shadow-sm' : 'border-[#E5DDCF] bg-white hover:border-[#A8C69A]'
                        }`}
                        role="button"
                        aria-pressed={isSelected}
                      >
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl font-serif mr-4 ${isSelected ? 'bg-[#103D2C] text-white' : 'bg-[#F2E8D5] text-[#292B26]'}`}>
                          {lang.symbol}
                        </div>
                        <div className="flex-1">
                          <div className={`font-semibold ${isSelected ? 'text-[#103D2C]' : 'text-[#292B26]'}`}>{lang.name}</div>
                          <div className={`text-xs ${isSelected ? 'text-[#164B35]' : 'text-[#292B26]/60'}`}>{lang.sub}</div>
                        </div>
                        {isSelected && <CheckCircle2 className="w-5 h-5 text-[#164B35]" />}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-8">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Sprout className="w-5 h-5 text-[#164B35]" />
                    <h3 className="text-xl font-bold text-[#292B26] font-serif">Tell us about yourself</h3>
                  </div>
                  <p className="text-sm text-[#292B26]/60 mb-4">This helps us personalize your experience.</p>
                  
                  <div className="grid grid-cols-2 gap-3">
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
                          className={`flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all relative ${
                            isSelected ? 'border-[#164B35] bg-[#F2E8D5] shadow-sm' : 'border-[#E5DDCF] bg-white hover:border-[#A8C69A]'
                          }`}
                          role="button"
                          aria-pressed={isSelected}
                        >
                          <Icon className={`w-6 h-6 mb-2 ${isSelected ? 'text-[#103D2C]' : 'text-[#292B26]/40'}`} />
                          <span className={`font-semibold text-sm mb-1 ${isSelected ? 'text-[#103D2C]' : 'text-[#292B26]'}`}>
                            {item.id}
                          </span>
                          <span className={`text-[10px] leading-tight ${isSelected ? 'text-[#164B35]' : 'text-[#292B26]/60'}`}>
                            {item.desc}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-[#292B26] mb-2 font-serif">Farm Name (Optional)</label>
                  <input 
                    type="text" 
                    value={farmName}
                    onChange={(e) => setFarmName(e.target.value)}
                    placeholder="e.g. Green Acres" 
                    className="w-full border border-[#E5DDCF] rounded-xl px-4 py-3 bg-white focus:border-[#164B35] focus:ring-1 focus:ring-[#164B35] outline-none text-sm text-[#292B26]"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-end mb-2">
                    <label className="block text-sm font-bold text-[#292B26] font-serif">Your Location</label>
                    <button type="button" onClick={handleGetLocation} className="text-xs text-[#164B35] flex items-center gap-1 font-medium hover:underline">
                      <Navigation className="w-3 h-3" /> Get Current
                    </button>
                  </div>
                  <div className="flex items-center border border-[#E5DDCF] rounded-xl px-4 py-3 bg-white focus-within:border-[#164B35] focus-within:ring-1 focus-within:ring-[#164B35]">
                    <Search className="w-4 h-4 text-[#292B26]/40 mr-2" />
                    <input 
                      type="text" 
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="Village, City or PIN code" 
                      className="w-full outline-none text-sm bg-transparent text-[#292B26]"
                    />
                    <MapPin className="w-4 h-4 text-[#B6532A] ml-2" />
                  </div>
                  {locationLoading && <p className="text-xs text-[#164B35] mt-1">Fetching location...</p>}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="flex items-center gap-2 mb-2">
                  <Leaf className="w-5 h-5 text-[#164B35]" />
                  <h3 className="text-xl font-bold text-[#292B26] font-serif">Preferences</h3>
                </div>
                <p className="text-sm text-[#292B26]/60 mb-6">Select topics you want updates about (Optional).</p>
                
                <div className="space-y-3">
                  {['Weather Alerts', 'Market Prices', 'Crop Disease Warnings', 'Govt Schemes'].map(pref => (
                    <label key={pref} className={`flex items-center p-4 rounded-xl border cursor-pointer transition-colors ${preferences.includes(pref) ? 'border-[#164B35] bg-[#F2E8D5]' : 'border-[#E5DDCF] bg-white hover:bg-gray-50'}`}>
                      <input 
                        type="checkbox" 
                        checked={preferences.includes(pref)}
                        onChange={() => togglePreference(pref)}
                        className="w-4 h-4 text-[#164B35] rounded border-[#E5DDCF] focus:ring-[#164B35] accent-[#164B35]"
                      />
                      <span className="ml-3 text-sm font-medium text-[#292B26]">{pref}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300 text-center py-6">
                <div className="w-16 h-16 bg-[#F2E8D5] rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8 text-[#164B35]" />
                </div>
                <h3 className="text-2xl font-bold text-[#103D2C] font-serif mb-2">You're All Set!</h3>
                <p className="text-sm text-[#292B26]/70 mb-8">We've personalized KISANcare based on your profile.</p>

                <div className="bg-white border border-[#E5DDCF] rounded-xl p-4 text-left text-sm space-y-3 shadow-sm">
                  <div className="flex justify-between border-b border-[#E5DDCF] pb-2">
                    <span className="text-[#292B26]/60">Language:</span>
                    <span className="font-medium">{language}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#E5DDCF] pb-2">
                    <span className="text-[#292B26]/60">Role:</span>
                    <span className="font-medium">{role}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#E5DDCF] pb-2">
                    <span className="text-[#292B26]/60">Location:</span>
                    <span className="font-medium truncate max-w-[150px] text-right">{location || 'Not provided'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#292B26]/60">Preferences:</span>
                    <span className="font-medium">{preferences.length} selected</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="p-6 lg:p-8 pt-4 border-t border-[#E5DDCF] flex gap-3 mt-auto bg-[#FBF7EF]">
          {step > 1 && (
            <button 
              onClick={prevStep}
              className="px-4 py-3 rounded-xl border border-[#E5DDCF] bg-white text-[#292B26] font-medium hover:bg-gray-50 transition-colors flex items-center justify-center"
              aria-label="Previous step"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          
          {step < 4 ? (
            <button 
              onClick={nextStep}
              className="flex-1 bg-[#103D2C] text-white rounded-xl py-3 font-semibold flex items-center justify-center gap-2 hover:bg-[#164B35] transition-colors shadow-lg shadow-[#103D2C]/20"
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button 
              onClick={handleComplete}
              className="flex-1 bg-[#B6532A] text-white rounded-xl py-3 font-semibold flex items-center justify-center gap-2 hover:bg-[#9c4521] transition-colors shadow-lg shadow-[#B6532A]/20"
            >
              Continue to KISANcare
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
