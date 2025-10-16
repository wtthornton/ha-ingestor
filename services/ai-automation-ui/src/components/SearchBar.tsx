/**
 * Search Bar Component
 * Search and filter suggestions
 */

import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onCategoryFilter: (category: string | null) => void;
  onConfidenceFilter: (min: number) => void;
  selectedCategory: string | null;
  minConfidence: number;
  darkMode?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onCategoryFilter,
  onConfidenceFilter,
  selectedCategory,
  minConfidence,
  darkMode = false
}) => {
  const categories = ['energy', 'comfort', 'security', 'convenience'];

  return (
    <div className="space-y-3">
      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search by device, title, or description..."
          className={`w-full px-4 py-3 pl-12 rounded-xl border-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
            darkMode
              ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500'
              : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400'
          }`}
        />
        <div className="absolute left-4 top-3.5 text-xl">
          🔍
        </div>
        {value && (
          <button
            onClick={() => onChange('')}
            className={`absolute right-4 top-3.5 ${darkMode ? 'text-gray-400 hover:text-white' : 'text-gray-400 hover:text-gray-900'}`}
          >
            ✕
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {/* Category Filter */}
        <div className="flex gap-2 items-center">
          <span className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Category:
          </span>
          <button
            onClick={() => onCategoryFilter(null)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              selectedCategory === null
                ? darkMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-500 text-white'
                : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => onCategoryFilter(cat)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === cat
                  ? darkMode
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-500 text-white'
                  : darkMode
                  ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Confidence Filter */}
        <div className="flex gap-2 items-center ml-auto">
          <span className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Min Confidence:
          </span>
          <select
            value={minConfidence}
            onChange={(e) => onConfidenceFilter(Number(e.target.value))}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              darkMode
                ? 'bg-gray-700 text-white border-gray-600'
                : 'bg-white text-gray-900 border-gray-300'
            } border focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            <option value="0">0%</option>
            <option value="0.5">50%</option>
            <option value="0.7">70%</option>
            <option value="0.8">80%</option>
            <option value="0.9">90%</option>
          </select>
        </div>
      </div>
    </div>
  );
};

