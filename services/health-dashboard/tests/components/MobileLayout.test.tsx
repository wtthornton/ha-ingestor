import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MobileLayout, MobileCard, MobileSection, MobileButton, MobileInput, MobileGrid } from '../../src/components/MobileLayout';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

// Mock the mobile detection hook
vi.mock('../../src/hooks/useMobileDetection', () => ({
  useMobileDetection: () => ({
    isMobile: true,
    isTablet: false,
    isDesktop: false,
    screenWidth: 375,
    screenHeight: 667,
    orientation: 'portrait',
    deviceType: 'mobile',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
    isTouchDevice: true,
  }),
}));

// Mock the touch gestures hook
vi.mock('../../src/hooks/useTouchGestures', () => ({
  useTouchGestures: () => ({
    touchHandlers: {
      onTouchStart: vi.fn(),
      onTouchMove: vi.fn(),
      onTouchEnd: vi.fn(),
    },
  }),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('MobileLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render mobile layout for mobile devices', () => {
    renderWithTheme(
      <MobileLayout>
        <div>Test Content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render desktop layout for desktop devices', () => {
    // Mock desktop detection
    vi.mocked(require('../../src/hooks/useMobileDetection').useMobileDetection).mockReturnValue({
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenWidth: 1024,
      screenHeight: 768,
      orientation: 'landscape',
      deviceType: 'desktop',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      isTouchDevice: false,
    });

    renderWithTheme(
      <MobileLayout>
        <div>Desktop Content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Desktop Content')).toBeInTheDocument();
  });

  it('should apply mobile-specific classes', () => {
    renderWithTheme(
      <MobileLayout className="custom-class">
        <div>Test Content</div>
      </MobileLayout>
    );

    const layout = screen.getByText('Test Content').closest('div');
    expect(layout).toHaveClass('mobile-optimized', 'mobile-scroll', 'portrait-mode');
  });
});

describe('MobileCard', () => {
  it('should render with default styling', () => {
    renderWithTheme(
      <MobileCard>
        <div>Card Content</div>
      </MobileCard>
    );

    const card = screen.getByText('Card Content').closest('div');
    expect(card).toHaveClass('mobile-card', 'gesture-feedback');
  });

  it('should handle click events', () => {
    const onClick = vi.fn();
    
    renderWithTheme(
      <MobileCard onClick={onClick}>
        <div>Clickable Card</div>
      </MobileCard>
    );

    const card = screen.getByText('Clickable Card').closest('div');
    fireEvent.click(card!);

    expect(onClick).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MobileCard className="custom-card">
        <div>Card Content</div>
      </MobileCard>
    );

    const card = screen.getByText('Card Content').closest('div');
    expect(card).toHaveClass('custom-card');
  });
});

describe('MobileSection', () => {
  it('should render with title and content', () => {
    renderWithTheme(
      <MobileSection title="Test Section">
        <div>Section Content</div>
      </MobileSection>
    );

    expect(screen.getByText('Test Section')).toBeInTheDocument();
    expect(screen.getByText('Section Content')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MobileSection title="Test Section" className="custom-section">
        <div>Section Content</div>
      </MobileSection>
    );

    const section = screen.getByText('Test Section').closest('section');
    expect(section).toHaveClass('custom-section');
  });
});

describe('MobileButton', () => {
  it('should render with primary variant by default', () => {
    renderWithTheme(
      <MobileButton onClick={() => {}}>
        Click Me
      </MobileButton>
    );

    const button = screen.getByText('Click Me');
    expect(button).toHaveClass('bg-design-primary', 'text-design-text-inverse');
  });

  it('should render with secondary variant', () => {
    renderWithTheme(
      <MobileButton variant="secondary" onClick={() => {}}>
        Secondary Button
      </MobileButton>
    );

    const button = screen.getByText('Secondary Button');
    expect(button).toHaveClass('bg-design-secondary', 'text-design-text-inverse');
  });

  it('should render with danger variant', () => {
    renderWithTheme(
      <MobileButton variant="danger" onClick={() => {}}>
        Danger Button
      </MobileButton>
    );

    const button = screen.getByText('Danger Button');
    expect(button).toHaveClass('bg-design-error', 'text-design-text-inverse');
  });

  it('should render with different sizes', () => {
    renderWithTheme(
      <MobileButton size="sm" onClick={() => {}}>
        Small Button
      </MobileButton>
    );

    const button = screen.getByText('Small Button');
    expect(button).toHaveClass('px-3', 'py-2', 'text-sm');
  });

  it('should handle click events', () => {
    const onClick = vi.fn();
    
    renderWithTheme(
      <MobileButton onClick={onClick}>
        Click Me
      </MobileButton>
    );

    fireEvent.click(screen.getByText('Click Me'));
    expect(onClick).toHaveBeenCalled();
  });

  it('should be disabled when disabled prop is true', () => {
    renderWithTheme(
      <MobileButton disabled onClick={() => {}}>
        Disabled Button
      </MobileButton>
    );

    const button = screen.getByText('Disabled Button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed');
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MobileButton className="custom-button" onClick={() => {}}>
        Custom Button
      </MobileButton>
    );

    const button = screen.getByText('Custom Button');
    expect(button).toHaveClass('custom-button');
  });
});

describe('MobileInput', () => {
  it('should render with label', () => {
    renderWithTheme(
      <MobileInput label="Test Label" />
    );

    expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
  });

  it('should render with placeholder', () => {
    renderWithTheme(
      <MobileInput placeholder="Enter text..." />
    );

    expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument();
  });

  it('should handle value changes', () => {
    const onChange = vi.fn();
    
    renderWithTheme(
      <MobileInput value="test" onChange={onChange} />
    );

    const input = screen.getByDisplayValue('test');
    fireEvent.change(input, { target: { value: 'new value' } });

    expect(onChange).toHaveBeenCalledWith('new value');
  });

  it('should render different input types', () => {
    renderWithTheme(
      <MobileInput type="email" />
    );

    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');
  });

  it('should display error message', () => {
    renderWithTheme(
      <MobileInput error="This field is required" />
    );

    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('should apply error styling when error is present', () => {
    renderWithTheme(
      <MobileInput error="Error message" />
    );

    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-design-error');
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MobileInput className="custom-input" />
    );

    const container = screen.getByRole('textbox').closest('div');
    expect(container).toHaveClass('custom-input');
  });
});

describe('MobileGrid', () => {
  it('should render single column grid by default', () => {
    renderWithTheme(
      <MobileGrid>
        <div>Item 1</div>
        <div>Item 2</div>
      </MobileGrid>
    );

    const grid = screen.getByText('Item 1').closest('div');
    expect(grid).toHaveClass('grid-cols-1');
  });

  it('should render two column grid', () => {
    renderWithTheme(
      <MobileGrid columns={2}>
        <div>Item 1</div>
        <div>Item 2</div>
      </MobileGrid>
    );

    const grid = screen.getByText('Item 1').closest('div');
    expect(grid).toHaveClass('grid-cols-2');
  });

  it('should apply different gap sizes', () => {
    renderWithTheme(
      <MobileGrid gap="lg">
        <div>Item 1</div>
        <div>Item 2</div>
      </MobileGrid>
    );

    const grid = screen.getByText('Item 1').closest('div');
    expect(grid).toHaveClass('gap-6');
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MobileGrid className="custom-grid">
        <div>Item 1</div>
        <div>Item 2</div>
      </MobileGrid>
    );

    const grid = screen.getByText('Item 1').closest('div');
    expect(grid).toHaveClass('custom-grid');
  });
});
