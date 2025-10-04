import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle } from '../../src/components/ThemeToggle';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

// Mock Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  SunIcon: ({ className }: { className: string }) => (
    <svg className={className} data-testid="sun-icon">
      <title>Sun</title>
    </svg>
  ),
  MoonIcon: ({ className }: { className: string }) => (
    <svg className={className} data-testid="moon-icon">
      <title>Moon</title>
    </svg>
  ),
  ComputerDesktopIcon: ({ className }: { className: string }) => (
    <svg className={className} data-testid="computer-icon">
      <title>Computer</title>
    </svg>
  ),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock matchMedia
const mockMatchMedia = vi.fn();
Object.defineProperty(window, 'matchMedia', {
  value: mockMatchMedia,
});

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
  });

  describe('Button variant', () => {
    it('should render toggle button by default', () => {
      renderWithTheme(<ThemeToggle />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label', 'Switch to dark theme');
    });

    it('should show sun icon for light theme', () => {
      renderWithTheme(<ThemeToggle />);
      
      expect(screen.getByTestId('sun-icon')).toBeInTheDocument();
    });

    it('should toggle theme when clicked', () => {
      renderWithTheme(<ThemeToggle />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      expect(screen.getByTestId('moon-icon')).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label', 'Switch to light theme');
    });

    it('should show label when showLabel is true', () => {
      renderWithTheme(<ThemeToggle showLabel={true} />);
      
      expect(screen.getByText('Light')).toBeInTheDocument();
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expect(screen.getByText('System')).toBeInTheDocument();
    });
  });

  describe('Select variant', () => {
    it('should render select dropdown', () => {
      renderWithTheme(<ThemeToggle variant="select" />);
      
      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
      expect(select).toHaveAttribute('aria-label', 'Select theme');
    });

    it('should have all theme options', () => {
      renderWithTheme(<ThemeToggle variant="select" />);
      
      const select = screen.getByRole('combobox');
      expect(select).toHaveValue('system');
      
      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(3);
      expect(options[0]).toHaveTextContent('Light');
      expect(options[1]).toHaveTextContent('Dark');
      expect(options[2]).toHaveTextContent('System');
    });

    it('should change theme when option is selected', () => {
      renderWithTheme(<ThemeToggle variant="select" />);
      
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: 'dark' } });
      
      expect(select).toHaveValue('dark');
    });
  });

  describe('Toggle variant', () => {
    it('should render toggle switch', () => {
      renderWithTheme(<ThemeToggle variant="toggle" />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label', 'Switch to dark theme');
    });

    it('should show toggle switch with sun icon for light theme', () => {
      renderWithTheme(<ThemeToggle variant="toggle" />);
      
      expect(screen.getByTestId('sun-icon')).toBeInTheDocument();
    });

    it('should toggle theme when clicked', () => {
      renderWithTheme(<ThemeToggle variant="toggle" />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      expect(screen.getByTestId('moon-icon')).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label', 'Switch to light theme');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderWithTheme(<ThemeToggle />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label');
    });

    it('should update ARIA label when theme changes', () => {
      renderWithTheme(<ThemeToggle />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Switch to dark theme');
      
      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-label', 'Switch to light theme');
    });
  });

  describe('Styling', () => {
    it('should apply custom className', () => {
      renderWithTheme(<ThemeToggle className="custom-class" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });
});
