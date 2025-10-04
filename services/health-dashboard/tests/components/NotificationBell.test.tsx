import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NotificationBell } from '../../src/components/NotificationBell';
import { NotificationProvider } from '../../src/contexts/NotificationContext';

// Mock the notification service
vi.mock('../../src/services/notificationService', () => ({
  notificationService: {
    subscribe: vi.fn(() => vi.fn()),
    sendNotification: vi.fn(),
    updatePreferences: vi.fn(),
    getPreferences: vi.fn(() => ({
      enabled: true,
      categories: {},
      severity: {},
      thresholds: { maxNotifications: 50, autoDismissDelay: 5000, persistentThreshold: 0 },
      channels: { toast: true, center: true, sound: false },
    })),
  },
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <NotificationProvider>
    {children}
  </NotificationProvider>
);

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render notification bell icon', () => {
    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    
    const icon = button.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should have correct aria-label when no unread notifications', () => {
    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Notifications');
  });

  it('should show unread count badge when there are unread notifications', () => {
    // Mock the context to return unread count
    const mockUseNotificationCenter = vi.fn(() => ({
      notifications: [],
      unreadCount: 5,
      isCenterOpen: false,
      toggleCenter: vi.fn(),
      markAsRead: vi.fn(),
      markAllAsRead: vi.fn(),
      clearNotifications: vi.fn(),
    }));

    vi.doMock('../../src/contexts/NotificationContext', () => ({
      NotificationProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
      useNotificationCenter: mockUseNotificationCenter,
    }));

    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const badge = screen.getByText('5');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-red-500', 'text-white');
  });

  it('should show 99+ for counts over 99', () => {
    const mockUseNotificationCenter = vi.fn(() => ({
      notifications: [],
      unreadCount: 150,
      isCenterOpen: false,
      toggleCenter: vi.fn(),
      markAsRead: vi.fn(),
      markAllAsRead: vi.fn(),
      clearNotifications: vi.fn(),
    }));

    vi.doMock('../../src/contexts/NotificationContext', () => ({
      NotificationProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
      useNotificationCenter: mockUseNotificationCenter,
    }));

    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const badge = screen.getByText('99+');
    expect(badge).toBeInTheDocument();
  });

  it('should call toggleCenter when clicked', () => {
    const mockToggleCenter = vi.fn();
    const mockUseNotificationCenter = vi.fn(() => ({
      notifications: [],
      unreadCount: 0,
      isCenterOpen: false,
      toggleCenter: mockToggleCenter,
      markAsRead: vi.fn(),
      markAllAsRead: vi.fn(),
      clearNotifications: vi.fn(),
    }));

    vi.doMock('../../src/contexts/NotificationContext', () => ({
      NotificationProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
      useNotificationCenter: mockUseNotificationCenter,
    }));

    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(mockToggleCenter).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    render(
      <TestWrapper>
        <NotificationBell className="custom-class" />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('should have focus styles', () => {
    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500');
  });

  it('should have hover styles', () => {
    render(
      <TestWrapper>
        <NotificationBell />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('hover:text-gray-500');
  });
});
