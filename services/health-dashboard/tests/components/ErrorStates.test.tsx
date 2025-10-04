import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { 
  ErrorState, 
  ConnectionError, 
  ServiceError, 
  WarningState, 
  InfoState, 
  EmptyState, 
  LoadingError, 
  NetworkError, 
  AlertBanner 
} from '../../src/components/ErrorStates';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('ErrorState', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render with error severity', () => {
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
      />
    );

    expect(screen.getByText('Test Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should render with warning severity', () => {
    renderWithTheme(
      <ErrorState
        title="Test Warning"
        message="Something needs attention"
        severity="warning"
      />
    );

    expect(screen.getByText('Test Warning')).toBeInTheDocument();
    expect(screen.getByText('Something needs attention')).toBeInTheDocument();
  });

  it('should render with info severity', () => {
    renderWithTheme(
      <ErrorState
        title="Test Info"
        message="Some information"
        severity="info"
      />
    );

    expect(screen.getByText('Test Info')).toBeInTheDocument();
    expect(screen.getByText('Some information')).toBeInTheDocument();
  });

  it('should handle retry button', () => {
    const onRetry = vi.fn();
    
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
        onRetry={onRetry}
        showRetry={true}
      />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it('should handle dismiss button', () => {
    const onDismiss = vi.fn();
    
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
        onDismiss={onDismiss}
        showDismiss={true}
      />
    );

    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalled();
  });

  it('should hide retry button when showRetry is false', () => {
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
        showRetry={false}
      />
    );

    expect(screen.queryByText('Retry')).not.toBeInTheDocument();
  });

  it('should hide dismiss button when showDismiss is false', () => {
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
        showDismiss={false}
      />
    );

    expect(screen.queryByText('Dismiss')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <ErrorState
        title="Test Error"
        message="Something went wrong"
        severity="error"
        className="custom-class"
      />
    );

    const errorState = screen.getByText('Test Error').closest('div');
    expect(errorState).toHaveClass('custom-class');
  });
});

describe('ConnectionError', () => {
  it('should render with service name', () => {
    renderWithTheme(
      <ConnectionError service="Test Service" />
    );

    expect(screen.getByText('Test Service Connection Failed')).toBeInTheDocument();
    expect(screen.getByText(/Unable to connect to Test Service/)).toBeInTheDocument();
  });

  it('should handle retry', () => {
    const onRetry = vi.fn();
    
    renderWithTheme(
      <ConnectionError service="Test Service" onRetry={onRetry} />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <ConnectionError service="Test Service" className="custom-class" />
    );

    const errorState = screen.getByText('Test Service Connection Failed').closest('div');
    expect(errorState).toHaveClass('custom-class');
  });
});

describe('ServiceError', () => {
  it('should render with service name and error message', () => {
    renderWithTheme(
      <ServiceError service="Test Service" error="Connection timeout" />
    );

    expect(screen.getByText('Test Service Error')).toBeInTheDocument();
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  it('should handle retry', () => {
    const onRetry = vi.fn();
    
    renderWithTheme(
      <ServiceError service="Test Service" error="Connection timeout" onRetry={onRetry} />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <ServiceError service="Test Service" error="Connection timeout" className="custom-class" />
    );

    const errorState = screen.getByText('Test Service Error').closest('div');
    expect(errorState).toHaveClass('custom-class');
  });
});

describe('WarningState', () => {
  it('should render warning message', () => {
    renderWithTheme(
      <WarningState title="Warning" message="Something needs attention" />
    );

    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Something needs attention')).toBeInTheDocument();
  });

  it('should handle dismiss', () => {
    const onDismiss = vi.fn();
    
    renderWithTheme(
      <WarningState title="Warning" message="Something needs attention" onDismiss={onDismiss} />
    );

    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <WarningState title="Warning" message="Something needs attention" className="custom-class" />
    );

    const warningState = screen.getByText('Warning').closest('div');
    expect(warningState).toHaveClass('custom-class');
  });
});

describe('InfoState', () => {
  it('should render info message', () => {
    renderWithTheme(
      <InfoState title="Info" message="Some information" />
    );

    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText('Some information')).toBeInTheDocument();
  });

  it('should handle dismiss', () => {
    const onDismiss = vi.fn();
    
    renderWithTheme(
      <InfoState title="Info" message="Some information" onDismiss={onDismiss} />
    );

    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <InfoState title="Info" message="Some information" className="custom-class" />
    );

    const infoState = screen.getByText('Info').closest('div');
    expect(infoState).toHaveClass('custom-class');
  });
});

describe('EmptyState', () => {
  it('should render empty state', () => {
    renderWithTheme(
      <EmptyState title="No Data" message="No data available" />
    );

    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('should render with action button', () => {
    const onClick = vi.fn();
    
    renderWithTheme(
      <EmptyState 
        title="No Data" 
        message="No data available" 
        action={{ label: 'Refresh', onClick }}
      />
    );

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    expect(onClick).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <EmptyState title="No Data" message="No data available" className="custom-class" />
    );

    const emptyState = screen.getByText('No Data').closest('div');
    expect(emptyState).toHaveClass('custom-class');
  });
});

describe('LoadingError', () => {
  it('should render loading error', () => {
    renderWithTheme(
      <LoadingError />
    );

    expect(screen.getByText('Failed to Load Data')).toBeInTheDocument();
    expect(screen.getByText(/There was an error loading the data/)).toBeInTheDocument();
  });

  it('should handle retry', () => {
    const onRetry = vi.fn();
    
    renderWithTheme(
      <LoadingError onRetry={onRetry} />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <LoadingError className="custom-class" />
    );

    const loadingError = screen.getByText('Failed to Load Data').closest('div');
    expect(loadingError).toHaveClass('custom-class');
  });
});

describe('NetworkError', () => {
  it('should render network error', () => {
    renderWithTheme(
      <NetworkError />
    );

    expect(screen.getByText('Network Error')).toBeInTheDocument();
    expect(screen.getByText(/Unable to connect to the server/)).toBeInTheDocument();
  });

  it('should handle retry', () => {
    const onRetry = vi.fn();
    
    renderWithTheme(
      <NetworkError onRetry={onRetry} />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <NetworkError className="custom-class" />
    );

    const networkError = screen.getByText('Network Error').closest('div');
    expect(networkError).toHaveClass('custom-class');
  });
});

describe('AlertBanner', () => {
  it('should render error alert', () => {
    renderWithTheme(
      <AlertBanner message="Error occurred" severity="error" />
    );

    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  it('should render warning alert', () => {
    renderWithTheme(
      <AlertBanner message="Warning message" severity="warning" />
    );

    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('should render info alert', () => {
    renderWithTheme(
      <AlertBanner message="Info message" severity="info" />
    );

    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('should handle dismiss', () => {
    const onDismiss = vi.fn();
    
    renderWithTheme(
      <AlertBanner message="Error occurred" severity="error" onDismiss={onDismiss} />
    );

    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <AlertBanner message="Error occurred" severity="error" className="custom-class" />
    );

    const alertBanner = screen.getByText('Error occurred').closest('div');
    expect(alertBanner).toHaveClass('custom-class');
  });
});
