import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NotificationProvider, useNotifications } from '../../src/contexts/NotificationContext';
import { notificationService } from '../../src/services/notificationService';

// Mock the notification service
vi.mock('../../src/services/notificationService', () => ({
  notificationService: {
    subscribe: vi.fn(),
    sendNotification: vi.fn(),
    updatePreferences: vi.fn(),
    getPreferences: vi.fn(),
  },
}));

// Test component that uses the notification context
const TestComponent = () => {
  const {
    notifications,
    unreadCount,
    isCenterOpen,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearNotifications,
    toggleCenter,
  } = useNotifications();

  return (
    <div>
      <div data-testid="notification-count">{notifications.length}</div>
      <div data-testid="unread-count">{unreadCount}</div>
      <div data-testid="center-open">{isCenterOpen.toString()}</div>
      
      <button onClick={() => addNotification({
        type: 'info',
        title: 'Test Notification',
        message: 'Test message',
        persistent: false,
      })}>
        Add Notification
      </button>
      
      <button onClick={() => removeNotification('test-id')}>
        Remove Notification
      </button>
      
      <button onClick={() => markAsRead('test-id')}>
        Mark as Read
      </button>
      
      <button onClick={markAllAsRead}>
        Mark All as Read
      </button>
      
      <button onClick={clearNotifications}>
        Clear All
      </button>
      
      <button onClick={toggleCenter}>
        Toggle Center
      </button>
    </div>
  );
};

describe('NotificationContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should provide default values', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
    expect(screen.getByTestId('unread-count')).toHaveTextContent('0');
    expect(screen.getByTestId('center-open')).toHaveTextContent('false');
  });

  it('should add notification when service sends one', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Simulate notification from service
    mockCallback({
      id: 'test-notification',
      type: 'info',
      title: 'Service Notification',
      message: 'From service',
      timestamp: new Date(),
      persistent: true,
    });

    await waitFor(() => {
      expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
      expect(screen.getByTestId('unread-count')).toHaveTextContent('1');
    });
  });

  it('should add notification via context method', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    fireEvent.click(screen.getByText('Add Notification'));

    expect(notificationService.sendNotification).toHaveBeenCalledWith({
      type: 'info',
      title: 'Test Notification',
      message: 'Test message',
      persistent: false,
    });
  });

  it('should remove notification', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Add a notification first
    mockCallback({
      id: 'test-id',
      type: 'info',
      title: 'Test',
      message: 'Test message',
      timestamp: new Date(),
      persistent: true,
    });

    await waitFor(() => {
      expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
    });

    // Remove it
    fireEvent.click(screen.getByText('Remove Notification'));

    await waitFor(() => {
      expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
      expect(screen.getByTestId('unread-count')).toHaveTextContent('0');
    });
  });

  it('should mark notification as read', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Add a persistent notification
    mockCallback({
      id: 'test-id',
      type: 'info',
      title: 'Test',
      message: 'Test message',
      timestamp: new Date(),
      persistent: true,
    });

    await waitFor(() => {
      expect(screen.getByTestId('unread-count')).toHaveTextContent('1');
    });

    // Mark as read
    fireEvent.click(screen.getByText('Mark as Read'));

    await waitFor(() => {
      expect(screen.getByTestId('unread-count')).toHaveTextContent('0');
    });
  });

  it('should mark all notifications as read', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Add multiple persistent notifications
    mockCallback({
      id: 'test-1',
      type: 'info',
      title: 'Test 1',
      message: 'Test message 1',
      timestamp: new Date(),
      persistent: true,
    });

    mockCallback({
      id: 'test-2',
      type: 'warning',
      title: 'Test 2',
      message: 'Test message 2',
      timestamp: new Date(),
      persistent: true,
    });

    await waitFor(() => {
      expect(screen.getByTestId('unread-count')).toHaveTextContent('2');
    });

    // Mark all as read
    fireEvent.click(screen.getByText('Mark All as Read'));

    await waitFor(() => {
      expect(screen.getByTestId('unread-count')).toHaveTextContent('0');
    });
  });

  it('should clear all notifications', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Add notifications
    mockCallback({
      id: 'test-1',
      type: 'info',
      title: 'Test 1',
      message: 'Test message 1',
      timestamp: new Date(),
      persistent: true,
    });

    await waitFor(() => {
      expect(screen.getByTestId('notification-count')).toHaveTextContent('1');
    });

    // Clear all
    fireEvent.click(screen.getByText('Clear All'));

    await waitFor(() => {
      expect(screen.getByTestId('notification-count')).toHaveTextContent('0');
      expect(screen.getByTestId('unread-count')).toHaveTextContent('0');
    });
  });

  it('should toggle notification center', () => {
    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    expect(screen.getByTestId('center-open')).toHaveTextContent('false');

    fireEvent.click(screen.getByText('Toggle Center'));

    expect(screen.getByTestId('center-open')).toHaveTextContent('true');

    fireEvent.click(screen.getByText('Toggle Center'));

    expect(screen.getByTestId('center-open')).toHaveTextContent('false');
  });

  it('should limit notifications based on preferences', async () => {
    const mockUnsubscribe = vi.fn();
    const mockCallback = vi.fn();

    vi.mocked(notificationService.subscribe).mockImplementation((callback) => {
      mockCallback.mockImplementation(callback);
      return mockUnsubscribe;
    });

    // Mock preferences with low limit
    vi.mocked(notificationService.getPreferences).mockReturnValue({
      enabled: true,
      categories: {},
      severity: {},
      thresholds: {
        maxNotifications: 2,
        autoDismissDelay: 5000,
        persistentThreshold: 0,
      },
      channels: {
        toast: true,
        center: true,
        sound: false,
      },
    });

    render(
      <NotificationProvider>
        <TestComponent />
      </NotificationProvider>
    );

    // Add more notifications than the limit
    for (let i = 0; i < 5; i++) {
      mockCallback({
        id: `test-${i}`,
        type: 'info',
        title: `Test ${i}`,
        message: `Test message ${i}`,
        timestamp: new Date(),
        persistent: false,
      });
    }

    await waitFor(() => {
      // Should be limited to 2 notifications
      expect(screen.getByTestId('notification-count')).toHaveTextContent('2');
    });
  });

  it('should throw error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useNotifications must be used within a NotificationProvider');

    consoleSpy.mockRestore();
  });
});
