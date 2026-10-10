import React, { useState } from 'react';
import { Leaf, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../../services/supabase';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    setLoading(false);
    
    if (error) {
      setError(error.message);
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Image Section */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-[#103D2C] overflow-hidden">
        <img src="https://images.unsplash.com/photo-1592982537447-6f2a6a0c5989?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" alt="Indian Farm" className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-60" />
        <div className="absolute inset-0 flex flex-col justify-between p-12">
          <div className="flex items-center gap-2">
            <Leaf className="w-8 h-8 text-[#A8C69A]" />
            <div>
              <h1 className="text-2xl font-bold tracking-tight font-serif text-white">
                KISAN<span className="text-[#B6532A] font-normal">care</span>
              </h1>
            </div>
          </div>
          <div>
            <h2 className="text-4xl font-serif font-bold text-white mb-4">Smarter Farms.<br/>Better Tomorrows.</h2>
            <p className="text-[#A8C69A] text-lg max-w-md">Join the digital revolution in agriculture. Make data-driven decisions for your farm.</p>
          </div>
        </div>
      </div>

      {/* Right Login Section */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-[#FBF7EF] p-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-serif font-bold text-[#103D2C] mb-2">Welcome Back</h2>
            <p className="text-[#292B26]/60">Sign in to your KISANcare account</p>
          </div>

          {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Email Address</label>
              <input 
                type="email" 
                placeholder="Enter your email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white border border-[#E5DDCF] rounded-lg px-4 py-3 focus:outline-none focus:border-[#17643E]" 
                required 
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="block text-sm font-medium text-[#292B26]">Password</label>
                <a href="#" className="text-sm font-medium text-[#17643E] hover:underline">Forgot password?</a>
              </div>
              <input 
                type="password" 
                placeholder="Enter your password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white border border-[#E5DDCF] rounded-lg px-4 py-3 focus:outline-none focus:border-[#17643E]" 
                required 
              />
            </div>

            <button disabled={loading} type="submit" className="w-full bg-[#103D2C] text-white rounded-lg py-3 font-bold hover:bg-[#17643E] transition-colors flex justify-center items-center gap-2 disabled:opacity-50">
              {loading ? 'Signing in...' : 'Sign In'} <ArrowRight size={18} />
            </button>
          </form>

          <p className="text-center text-sm text-[#292B26]/60 mt-8">
            Don't have an account? <a href="#" className="text-[#17643E] font-bold hover:underline">Create Account</a>
          </p>

          <div className="mt-8 pt-8 border-t border-[#E5DDCF] text-center">
            <p className="text-xs text-[#292B26]/40">Language</p>
            <div className="flex justify-center gap-4 mt-2">
              <span className="text-sm font-bold text-[#103D2C] cursor-pointer">English</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
