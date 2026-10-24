import React, { useState } from 'react';
import {
  Wrench,
  Truck,
  Users,
  Compass,
  GraduationCap
} from 'lucide-react';

interface ListingImageProps {
  src?: string;
  alt: string;
  category: string;
  className?: string;
}

export const ListingImage: React.FC<ListingImageProps> = ({
  src,
  alt,
  category,
  className = 'w-full h-48 object-cover'
}) => {
  const [hasError, setHasError] = useState(false);

  const getCategoryTheme = (cat: string) => {
    switch (cat.toLowerCase()) {
      case 'tractor':
        return {
          icon: Compass,
          bg: 'bg-emerald-900/60',
          border: 'border-emerald-700/50',
          text: 'text-emerald-300',
          label: 'Tractor & Machinery'
        };
      case 'equipment':
        return {
          icon: Wrench,
          bg: 'bg-amber-900/60',
          border: 'border-amber-700/50',
          text: 'text-amber-300',
          label: 'Implement & Tool'
        };
      case 'transport':
        return {
          icon: Truck,
          bg: 'bg-blue-900/60',
          border: 'border-blue-700/50',
          text: 'text-blue-300',
          label: 'Farm Transport'
        };
      case 'labour':
        return {
          icon: Users,
          bg: 'bg-purple-900/60',
          border: 'border-purple-700/50',
          text: 'text-purple-300',
          label: 'Farm Labour Gang'
        };
      case 'specialist':
        return {
          icon: GraduationCap,
          bg: 'bg-teal-900/60',
          border: 'border-teal-700/50',
          text: 'text-teal-300',
          label: 'Specialist / Agro Expert'
        };
      default:
        return {
          icon: Compass,
          bg: 'bg-gray-800',
          border: 'border-gray-700',
          text: 'text-gray-300',
          label: 'Agricultural Rental'
        };
    }
  };

  const theme = getCategoryTheme(category);
  const Icon = theme.icon;

  if (!src || hasError) {
    return (
      <div
        className={`${className} ${theme.bg} ${theme.border} border flex flex-col items-center justify-center p-4 text-center select-none relative overflow-hidden`}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col items-center">
          <div className={`p-3 rounded-2xl bg-black/40 backdrop-blur-md mb-2 shadow-inner border border-white/10 ${theme.text}`}>
            <Icon className="w-8 h-8" />
          </div>
          <span className={`text-xs font-semibold uppercase tracking-wider ${theme.text}`}>
            {theme.label}
          </span>
          <p className="text-xs text-gray-300 mt-1 line-clamp-2 px-2 max-w-[200px] font-medium">
            {alt}
          </p>
        </div>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setHasError(true)}
      className={`${className} transition-transform duration-300 hover:scale-105`}
    />
  );
};
