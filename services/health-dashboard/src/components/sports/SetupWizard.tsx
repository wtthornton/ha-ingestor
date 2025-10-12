/**
 * SetupWizard Component
 * 
 * 3-step wizard for team selection and configuration
 */

import React, { useState, useEffect } from 'react';
import { TeamSelector } from './TeamSelector';
import type { Team } from '../../types/sports';
import { calculateAPIUsage, getUsageColor, getProgressBarColor } from '../../utils/apiUsageCalculator';

interface SetupWizardProps {
  onComplete: (nflTeams: string[], nhlTeams: string[]) => void;
  onCancel?: () => void;
  darkMode?: boolean;
}

export const SetupWizard: React.FC<SetupWizardProps> = ({
  onComplete,
  onCancel,
  darkMode = false
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [nflTeams, setNflTeams] = useState<string[]>([]);
  const [nhlTeams, setNhlTeams] = useState<string[]>([]);
  const [availableNFLTeams, setAvailableNFLTeams] = useState<Team[]>([]);
  const [availableNHLTeams, setAvailableNHLTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  const bgPrimary = darkMode ? 'bg-gray-900' : 'bg-gray-50';
  const bgCard = darkMode ? 'bg-gray-800' : 'bg-white';
  const bgSecondary = darkMode ? 'bg-gray-700' : 'bg-gray-50';
  const textPrimary = darkMode ? 'text-white' : 'text-gray-900';
  const textSecondary = darkMode ? 'text-gray-400' : 'text-gray-600';

  // Fetch available teams
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        // Fetch NFL teams
        const nflResponse = await fetch('/api/sports/teams?league=NFL');
        const nflData = await nflResponse.json();
        setAvailableNFLTeams(nflData.teams || []);

        // Fetch NHL teams
        const nhlResponse = await fetch('/api/sports/teams?league=NHL');
        const nhlData = await nhlResponse.json();
        setAvailableNHLTeams(nhlData.teams || []);
      } catch (error) {
        console.error('Error fetching teams:', error);
        // Use fallback static data if API fails
        setAvailableNFLTeams(getStaticNFLTeams());
        setAvailableNHLTeams(getStaticNHLTeams());
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  const handleNFLTeamToggle = (teamId: string) => {
    setNflTeams(prev => 
      prev.includes(teamId)
        ? prev.filter(id => id !== teamId)
        : [...prev, teamId]
    );
  };

  const handleNHLTeamToggle = (teamId: string) => {
    setNhlTeams(prev =>
      prev.includes(teamId)
        ? prev.filter(id => id !== teamId)
        : [...prev, teamId]
    );
  };

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleComplete = () => {
    onComplete(nflTeams, nhlTeams);
  };

  const canContinue = () => {
    if (currentStep === 1) {
      // Must select at least 1 NFL team
      return nflTeams.length > 0;
    }
    return true; // NHL is optional
  };

  const apiUsage = calculateAPIUsage(nflTeams, nhlTeams);

  if (loading) {
    return (
      <div className={`min-h-screen ${bgPrimary} flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className={textSecondary}>Loading teams...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${bgPrimary} py-12 px-4`}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className={`${bgCard} rounded-xl shadow-xl p-8 mb-8`}>
          <h1 className={`text-3xl font-bold ${textPrimary} mb-2`}>
            🏈🏒 Sports Integration Setup
          </h1>
          <p className={textSecondary}>
            Step {currentStep} of 3: {
              currentStep === 1 ? 'Select NFL Teams' :
              currentStep === 2 ? 'Select NHL Teams (Optional)' :
              'Review & Confirm'
            }
          </p>
          
          {/* Progress Indicators */}
          <div className="flex items-center gap-2 mt-6">
            {[1, 2, 3].map(step => (
              <div
                key={step}
                className={`flex-1 h-2 rounded-full transition-colors ${
                  step <= currentStep
                    ? 'bg-blue-500'
                    : darkMode ? 'bg-gray-700' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className={`${bgCard} rounded-xl shadow-xl p-8`}>
          {/* Step 1: NFL Teams */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className={`text-2xl font-bold ${textPrimary} mb-2`}>
                  🏈 Select Your NFL Teams
                </h2>
                <p className={textSecondary}>
                  Choose the teams you want to track. We recommend selecting 3-5 teams.
                </p>
              </div>

              <TeamSelector
                league="NFL"
                teams={availableNFLTeams}
                selectedTeams={nflTeams}
                onTeamToggle={handleNFLTeamToggle}
                darkMode={darkMode}
              />
            </div>
          )}

          {/* Step 2: NHL Teams */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className={`text-2xl font-bold ${textPrimary} mb-2`}>
                  🏒 Select Your NHL Teams (Optional)
                </h2>
                <p className={textSecondary}>
                  Add NHL teams to your dashboard, or skip this step to continue with NFL only.
                </p>
              </div>

              <TeamSelector
                league="NHL"
                teams={availableNHLTeams}
                selectedTeams={nhlTeams}
                onTeamToggle={handleNHLTeamToggle}
                darkMode={darkMode}
              />
            </div>
          )}

          {/* Step 3: Review */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className={`text-2xl font-bold ${textPrimary} mb-2`}>
                  ✅ Review Your Selections
                </h2>
                <p className={textSecondary}>
                  Confirm your team selections and estimated API usage.
                </p>
              </div>

              {/* Selected Teams Summary */}
              <div className="space-y-4">
                {/* NFL Teams */}
                {nflTeams.length > 0 && (
                  <div className={`p-4 rounded-lg ${bgSecondary}`}>
                    <h3 className={`font-semibold ${textPrimary} mb-3`}>
                      🏈 NFL Teams ({nflTeams.length}):
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {nflTeams.map(teamId => {
                        const team = availableNFLTeams.find(t => t.id === teamId);
                        return team ? (
                          <div
                            key={teamId}
                            className={`px-3 py-2 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-white'} 
                              ${textPrimary} text-sm font-medium flex items-center gap-2`}
                          >
                            🏈 {team.name}
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}

                {/* NHL Teams */}
                {nhlTeams.length > 0 && (
                  <div className={`p-4 rounded-lg ${bgSecondary}`}>
                    <h3 className={`font-semibold ${textPrimary} mb-3`}>
                      🏒 NHL Teams ({nhlTeams.length}):
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {nhlTeams.map(teamId => {
                        const team = availableNHLTeams.find(t => t.id === teamId);
                        return team ? (
                          <div
                            key={teamId}
                            className={`px-3 py-2 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-white'} 
                              ${textPrimary} text-sm font-medium flex items-center gap-2`}
                          >
                            🏒 {team.name}
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* API Usage Estimate */}
              <div className={`p-6 rounded-lg ${darkMode ? 'bg-blue-900/20 border-2 border-blue-500/30' : 'bg-blue-50 border-2 border-blue-200'}`}>
                <h3 className={`font-semibold ${textPrimary} mb-4`}>
                  📊 Estimated API Usage
                </h3>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className={textSecondary}>Daily API Calls:</span>
                    <span className={`font-bold text-xl ${getUsageColor(apiUsage.warning_level)}`}>
                      {apiUsage.daily_calls} / 100
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className={`h-3 rounded-full ${darkMode ? 'bg-gray-700' : 'bg-gray-200'} overflow-hidden`}>
                    <div
                      className={`h-full ${getProgressBarColor(apiUsage.warning_level)} transition-all duration-300`}
                      style={{ width: `${Math.min(100, (apiUsage.daily_calls / 100) * 100)}%` }}
                    />
                  </div>

                  <div className={`text-sm ${textSecondary}`}>
                    {apiUsage.recommendation}
                  </div>

                  {!apiUsage.within_free_tier && (
                    <div className="text-sm text-red-600 dark:text-red-400 font-semibold">
                      ⚠️ Exceeds free tier limit. Consider removing teams or upgrading to paid API.
                    </div>
                  )}
                </div>
              </div>

              {/* Important Notice */}
              <div className={`p-4 rounded-lg ${darkMode ? 'bg-yellow-900/20 border border-yellow-500/30' : 'bg-yellow-50 border border-yellow-200'}`}>
                <p className={`text-sm ${darkMode ? 'text-yellow-200' : 'text-yellow-800'}`}>
                  ⚠️ <strong>Important:</strong> Only these teams will be monitored. 
                  You can add or remove teams anytime in the Settings tab.
                </p>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={currentStep === 1 ? onCancel : handleBack}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
              }`}
            >
              {currentStep === 1 ? 'Cancel' : '← Back'}
            </button>

            <div className="flex gap-3">
              {/* Skip NHL button on step 2 */}
              {currentStep === 2 && (
                <button
                  onClick={handleNext}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    darkMode
                      ? 'bg-gray-700 hover:bg-gray-600 text-white'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
                  }`}
                >
                  Skip NHL →
                </button>
              )}

              {/* Continue/Complete button */}
              <button
                onClick={currentStep === 3 ? handleComplete : handleNext}
                disabled={!canContinue()}
                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                  canContinue()
                    ? darkMode
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-blue-500 hover:bg-blue-600 text-white'
                    : 'bg-gray-400 text-gray-200 cursor-not-allowed'
                }`}
              >
                {currentStep === 3 ? '✓ Confirm & Start' : 'Continue →'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Fallback static team data if API fails
function getStaticNFLTeams(): Team[] {
  return [
    { id: 'sf', name: 'San Francisco 49ers', abbreviation: 'SF', logo: '', colors: { primary: '#AA0000', secondary: '#B3995D' } },
    { id: 'dal', name: 'Dallas Cowboys', abbreviation: 'DAL', logo: '', colors: { primary: '#003594', secondary: '#869397' } },
    { id: 'gb', name: 'Green Bay Packers', abbreviation: 'GB', logo: '', colors: { primary: '#203731', secondary: '#FFB612' } },
    { id: 'ne', name: 'New England Patriots', abbreviation: 'NE', logo: '', colors: { primary: '#002244', secondary: '#C60C30' } },
    { id: 'kc', name: 'Kansas City Chiefs', abbreviation: 'KC', logo: '', colors: { primary: '#E31837', secondary: '#FFB81C' } },
    // Add more teams as needed...
  ];
}

function getStaticNHLTeams(): Team[] {
  return [
    { id: 'bos', name: 'Boston Bruins', abbreviation: 'BOS', logo: '', colors: { primary: '#FCB514', secondary: '#000000' } },
    { id: 'wsh', name: 'Washington Capitals', abbreviation: 'WSH', logo: '', colors: { primary: '#041E42', secondary: '#C8102E' } },
    { id: 'pit', name: 'Pittsburgh Penguins', abbreviation: 'PIT', logo: '', colors: { primary: '#000000', secondary: '#FCB514' } },
    { id: 'chi', name: 'Chicago Blackhawks', abbreviation: 'CHI', logo: '', colors: { primary: '#CF0A2C', secondary: '#000000' } },
    // Add more teams as needed...
  ];
}

