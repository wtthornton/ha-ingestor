/**
 * Tests for API Usage Calculator
 */

import { describe, it, expect } from 'vitest';
import { calculateAPIUsage, getUsageColor, getProgressBarColor } from '../utils/apiUsageCalculator';

describe('calculateAPIUsage', () => {
  it('should calculate usage for no teams', () => {
    const result = calculateAPIUsage([], []);
    
    expect(result.daily_calls).toBe(0);
    expect(result.within_free_tier).toBe(true);
    expect(result.warning_level).toBe('safe');
  });

  it('should calculate usage for 3 NFL teams', () => {
    const result = calculateAPIUsage(['sf', 'dal', 'gb'], []);
    
    expect(result.daily_calls).toBe(36); // 3 teams × 12 calls
    expect(result.within_free_tier).toBe(true);
    expect(result.warning_level).toBe('safe');
  });

  it('should calculate usage for 5 teams total', () => {
    const result = calculateAPIUsage(['sf', 'dal'], ['bos', 'wsh', 'pit']);
    
    expect(result.daily_calls).toBe(60); // 5 teams × 12 calls
    expect(result.within_free_tier).toBe(true);
    expect(result.warning_level).toBe('safe');
  });

  it('should warn at 80+ calls (caution threshold)', () => {
    const result = calculateAPIUsage(
      ['sf', 'dal', 'gb', 'ne', 'kc', 'pit'],  // 6 teams
      ['bos']  // 1 team = 7 total × 12 = 84 calls
    );
    
    expect(result.daily_calls).toBe(84);
    expect(result.within_free_tier).toBe(true);
    expect(result.warning_level).toBe('caution');
    expect(result.recommendation).toContain('Approaching free tier limit');
  });

  it('should error at 95+ calls (danger threshold)', () => {
    const result = calculateAPIUsage(
      ['sf', 'dal', 'gb', 'ne', 'kc'],  // 5 teams
      ['bos', 'wsh', 'pit', 'chi']  // 4 teams = 9 total × 12 = 108 calls
    );
    
    expect(result.daily_calls).toBe(108);
    expect(result.within_free_tier).toBe(false);
    expect(result.warning_level).toBe('danger');
    expect(result.recommendation).toContain('upgrading to paid tier');
  });

  it('should provide recommendation for available slots', () => {
    const result = calculateAPIUsage(['sf'], []); // 12 calls
    
    expect(result.recommendation).toContain('can add');
    expect(result.recommendation).toContain('team');
  });
});

describe('getUsageColor', () => {
  it('should return green for safe level', () => {
    const color = getUsageColor('safe');
    expect(color).toContain('green');
  });

  it('should return yellow for caution level', () => {
    const color = getUsageColor('caution');
    expect(color).toContain('yellow');
  });

  it('should return red for danger level', () => {
    const color = getUsageColor('danger');
    expect(color).toContain('red');
  });
});

describe('getProgressBarColor', () => {
  it('should return correct bar colors', () => {
    expect(getProgressBarColor('safe')).toBe('bg-green-500');
    expect(getProgressBarColor('caution')).toBe('bg-yellow-500');
    expect(getProgressBarColor('danger')).toBe('bg-red-500');
  });
});

