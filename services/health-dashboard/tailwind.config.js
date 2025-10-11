/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Design System Colors using CSS Custom Properties
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Custom color system
        'design-primary': 'var(--color-primary)',
        'design-primary-hover': 'var(--color-primary-hover)',
        'design-primary-light': 'var(--color-primary-light)',
        'design-primary-dark': 'var(--color-primary-dark)',
        
        'design-secondary': 'var(--color-secondary)',
        'design-secondary-hover': 'var(--color-secondary-hover)',
        'design-secondary-light': 'var(--color-secondary-light)',
        'design-secondary-dark': 'var(--color-secondary-dark)',
        
        'design-success': 'var(--color-success)',
        'design-success-hover': 'var(--color-success-hover)',
        'design-success-light': 'var(--color-success-light)',
        'design-success-dark': 'var(--color-success-dark)',
        
        'design-warning': 'var(--color-warning)',
        'design-warning-hover': 'var(--color-warning-hover)',
        'design-warning-light': 'var(--color-warning-light)',
        'design-warning-dark': 'var(--color-warning-dark)',
        
        'design-error': 'var(--color-error)',
        'design-error-hover': 'var(--color-error-hover)',
        'design-error-light': 'var(--color-error-light)',
        'design-error-dark': 'var(--color-error-dark)',
        
        'design-info': 'var(--color-info)',
        'design-info-hover': 'var(--color-info-hover)',
        'design-info-light': 'var(--color-info-light)',
        'design-info-dark': 'var(--color-info-dark)',
        
        // Background and surface colors
        'design-background': 'var(--color-background)',
        'design-background-secondary': 'var(--color-background-secondary)',
        'design-background-tertiary': 'var(--color-background-tertiary)',
        'design-surface': 'var(--color-surface)',
        'design-surface-hover': 'var(--color-surface-hover)',
        
        // Text colors
        'design-text': 'var(--color-text)',
        'design-text-secondary': 'var(--color-text-secondary)',
        'design-text-tertiary': 'var(--color-text-tertiary)',
        'design-text-inverse': 'var(--color-text-inverse)',
        
        // Border colors
        'design-border': 'var(--color-border)',
        'design-border-hover': 'var(--color-border-hover)',
        'design-border-focus': 'var(--color-border-focus)',
      },
      boxShadow: {
        'design-sm': 'var(--shadow-sm)',
        'design-md': 'var(--shadow-md)',
        'design-lg': 'var(--shadow-lg)',
        'design-xl': 'var(--shadow-xl)',
      },
      spacing: {
        'design-xs': 'var(--spacing-xs)',
        'design-sm': 'var(--spacing-sm)',
        'design-md': 'var(--spacing-md)',
        'design-lg': 'var(--spacing-lg)',
        'design-xl': 'var(--spacing-xl)',
        'design-2xl': 'var(--spacing-2xl)',
      },
      borderRadius: {
        'design-sm': 'var(--radius-sm)',
        'design-md': 'var(--radius-md)',
        'design-lg': 'var(--radius-lg)',
        'design-xl': 'var(--radius-xl)',
      },
      transitionDuration: {
        'design-fast': 'var(--transition-fast)',
        'design-normal': 'var(--transition-normal)',
        'design-slow': 'var(--transition-slow)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'bounce-subtle': 'bounceSubtle 0.6s ease-in-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        pulseGlow: {
          '0%, 100%': { 
            boxShadow: '0 0 5px var(--color-primary), 0 0 10px var(--color-primary), 0 0 15px var(--color-primary)' 
          },
          '50%': { 
            boxShadow: '0 0 10px var(--color-primary), 0 0 20px var(--color-primary), 0 0 30px var(--color-primary)' 
          },
        },
      },
    },
  },
  plugins: [],
}
