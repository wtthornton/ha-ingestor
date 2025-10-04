import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { notificationService } from '../../src/services/notificationService';
import { NotificationPreferences, DEFAULT_NOTIFICATION_PREFERENCES } from '../../src/types/notification';

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

// Mock window events
const mockAddEventListener = vi.fn();
const mockRemoveEventListener = vi.fn();
Object.defineProperty(window, 'addEventListener', {
  value: mockAddEventListener,
});

describe('NotificationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('sendNotification', () => {
    it('should send notification to subscribers', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      const notificationData = {
        type: 'info' as const,
        title: 'Test Notification',
        message: 'This is a test notification',
        persistent: false,
      };

      notificationService.sendNotification(notificationData);

      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          ...notificationData,
          id: expect.any(String),
          timestamp: expect.any(Date),
        })
      );

      unsubscribe();
    });

    it('should not send notification if disabled in preferences', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      // Disable notifications
      notificationService.updatePreferences({ enabled: false });

      const notificationData = {
        type: 'info' as const,
        title: 'Test Notification',
        message: 'This should not be sent',
        persistent: false,
      };

      notificationService.sendNotification(notificationData);

      expect(mockCallback).not.toHaveBeenCalled();

      unsubscribe();
    });

    it('should not send notification if category is disabled', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      // Disable system_status category
      notificationService.updatePreferences({
        categories: {
          ...DEFAULT_NOTIFICATION_PREFERENCES.categories,
          system_status: false,
        },
      });

      const notificationData = {
        type: 'info' as const,
        title: 'Test Notification',
        message: 'This should not be sent',
        persistent: false,
        category: 'system_status' as const,
      };

      notificationService.sendNotification(notificationData);

      expect(mockCallback).not.toHaveBeenCalled();

      unsubscribe();
    });

    it('should not send notification if severity is disabled', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      // Disable info severity
      notificationService.updatePreferences({
        severity: {
          ...DEFAULT_NOTIFICATION_PREFERENCES.severity,
          info: false,
        },
      });

      const notificationData = {
        type: 'info' as const,
        title: 'Test Notification',
        message: 'This should not be sent',
        persistent: false,
      };

      notificationService.sendNotification(notificationData);

      expect(mockCallback).not.toHaveBeenCalled();

      unsubscribe();
    });
  });

  describe('preferences management', () => {
    it('should load preferences from localStorage', () => {
      const savedPreferences = {
        enabled: false,
        categories: {
          ...DEFAULT_NOTIFICATION_PREFERENCES.categories,
          system_status: false,
        },
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(savedPreferences));

      // Create new instance to test loading
      const service = new (notificationService.constructor as any)();
      
      expect(service.getPreferences()).toEqual(
        expect.objectContaining(savedPreferences)
      );
    });

    it('should save preferences to localStorage', () => {
      const newPreferences = { enabled: false };
      
      notificationService.updatePreferences(newPreferences);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'notification-preferences',
        expect.stringContaining('"enabled":false')
      );
    });

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });

      // Should not throw
      expect(() => {
        notificationService.updatePreferences({ enabled: false });
      }).not.toThrow();
    });
  });

  describe('WebSocket integration', () => {
    it('should handle health updates', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      const mockWebSocketService = {
        on: vi.fn(),
      };

      notificationService.integrateWithWebSocket(mockWebSocketService);

      // Simulate health update
      const healthUpdateHandler = mockWebSocketService.on.mock.calls.find(
        call => call[0] === 'health_update'
      )?.[1];

      expect(healthUpdateHandler).toBeDefined();

      // Test unhealthy status
      healthUpdateHandler({ overall_status: 'unhealthy' });

      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'error',
          title: 'System Health Alert',
          message: 'System health has degraded to unhealthy status',
          persistent: true,
          category: 'system_status',
        })
      );

      unsubscribe();
    });

    it('should handle connection status changes', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      const mockWebSocketService = {
        on: vi.fn(),
      };

      notificationService.integrateWithWebSocket(mockWebSocketService);

      // Simulate connection lost
      const connectionHandler = mockWebSocketService.on.mock.calls.find(
        call => call[0] === 'connection_status'
      )?.[1];

      expect(connectionHandler).toBeDefined();

      connectionHandler({ connected: false });

      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'warning',
          title: 'Connection Lost',
          message: 'WebSocket connection has been lost. Attempting to reconnect...',
          category: 'system_status',
        })
      );

      unsubscribe();
    });
  });

  describe('subscription management', () => {
    it('should allow multiple subscribers', () => {
      const callback1 = vi.fn();
      const callback2 = vi.fn();

      const unsubscribe1 = notificationService.subscribe(callback1);
      const unsubscribe2 = notificationService.subscribe(callback2);

      notificationService.sendNotification({
        type: 'info',
        title: 'Test',
        message: 'Test message',
        persistent: false,
      });

      expect(callback1).toHaveBeenCalled();
      expect(callback2).toHaveBeenCalled();

      unsubscribe1();
      unsubscribe2();
    });

    it('should unsubscribe correctly', () => {
      const callback = vi.fn();
      const unsubscribe = notificationService.subscribe(callback);

      notificationService.sendNotification({
        type: 'info',
        title: 'Test',
        message: 'Test message',
        persistent: false,
      });

      expect(callback).toHaveBeenCalledTimes(1);

      unsubscribe();

      notificationService.sendNotification({
        type: 'info',
        title: 'Test 2',
        message: 'Test message 2',
        persistent: false,
      });

      expect(callback).toHaveBeenCalledTimes(1); // Should not be called again
    });
  });

  describe('offline handling', () => {
    it('should queue notifications when offline', () => {
      const mockCallback = vi.fn();
      const unsubscribe = notificationService.subscribe(mockCallback);

      // Simulate offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      notificationService.sendNotification({
        type: 'info',
        title: 'Offline Test',
        message: 'This should be queued',
        persistent: false,
      });

      expect(mockCallback).not.toHaveBeenCalled();

      // Simulate back online
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });

      // Trigger online event
      const onlineHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'online'
      )?.[1];

      if (onlineHandler) {
        onlineHandler();
        expect(mockCallback).toHaveBeenCalled();
      }

      unsubscribe();
    });
  });
});
