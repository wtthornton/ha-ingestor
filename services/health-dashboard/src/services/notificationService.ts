import { 
  Notification, 
  NotificationPreferences, 
  NotificationService,
  DEFAULT_NOTIFICATION_PREFERENCES,
  NotificationCategory 
} from '../types/notification';

class NotificationServiceImpl implements NotificationService {
  private subscribers: Set<(notification: Notification) => void> = new Set();
  private preferences: NotificationPreferences = DEFAULT_NOTIFICATION_PREFERENCES;
  private notificationQueue: Notification[] = [];
  private isOnline = true;

  constructor() {
    this.loadPreferences();
    this.setupOnlineOfflineHandlers();
  }

  private loadPreferences(): void {
    try {
      const saved = localStorage.getItem('notification-preferences');
      if (saved) {
        this.preferences = { ...DEFAULT_NOTIFICATION_PREFERENCES, ...JSON.parse(saved) };
      }
    } catch (error) {
      console.warn('Failed to load notification preferences:', error);
    }
  }

  private savePreferences(): void {
    try {
      localStorage.setItem('notification-preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.warn('Failed to save notification preferences:', error);
    }
  }

  private setupOnlineOfflineHandlers(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processQueuedNotifications();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  private processQueuedNotifications(): void {
    while (this.notificationQueue.length > 0) {
      const notification = this.notificationQueue.shift();
      if (notification) {
        this.notifySubscribers(notification);
      }
    }
  }

  private shouldShowNotification(notification: Notification): boolean {
    if (!this.preferences.enabled) return false;
    
    // Check category preferences
    if (notification.category && !this.preferences.categories[notification.category]) {
      return false;
    }

    // Check severity preferences
    if (!this.preferences.severity[notification.type]) {
      return false;
    }

    return true;
  }

  private notifySubscribers(notification: Notification): void {
    this.subscribers.forEach(callback => {
      try {
        callback(notification);
      } catch (error) {
        console.error('Error in notification subscriber:', error);
      }
    });
  }

  sendNotification(notificationData: Omit<Notification, 'id' | 'timestamp'>): void {
    const notification: Notification = {
      ...notificationData,
      id: this.generateId(),
      timestamp: new Date(),
    };

    if (!this.shouldShowNotification(notification)) {
      return;
    }

    if (this.isOnline) {
      this.notifySubscribers(notification);
    } else {
      // Queue for when we're back online
      this.notificationQueue.push(notification);
    }
  }

  subscribe(callback: (notification: Notification) => void): () => void {
    this.subscribers.add(callback);
    
    return () => {
      this.subscribers.delete(callback);
    };
  }

  updatePreferences(newPreferences: Partial<NotificationPreferences>): void {
    this.preferences = { ...this.preferences, ...newPreferences };
    this.savePreferences();
  }

  getPreferences(): NotificationPreferences {
    return { ...this.preferences };
  }

  private generateId(): string {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Integration with existing WebSocket service
  integrateWithWebSocket(websocketService: any): void {
    if (!websocketService) return;

    // Listen for system health changes
    websocketService.on('health_update', (data: any) => {
      this.handleHealthUpdate(data);
    });

    // Listen for error events
    websocketService.on('error', (error: any) => {
      this.handleError(error);
    });

    // Listen for connection status changes
    websocketService.on('connection_status', (status: any) => {
      this.handleConnectionStatus(status);
    });
  }

  private handleHealthUpdate(data: any): void {
    if (!data || !data.overall_status) return;

    const status = data.overall_status;
    if (status === 'unhealthy') {
      this.sendNotification({
        type: 'error',
        title: 'System Health Alert',
        message: 'System health has degraded to unhealthy status',
        persistent: true,
        category: 'system_status',
        source: 'health-monitor',
      });
    } else if (status === 'degraded') {
      this.sendNotification({
        type: 'warning',
        title: 'System Health Warning',
        message: 'System health has degraded',
        persistent: false,
        category: 'system_status',
        source: 'health-monitor',
      });
    }
  }

  private handleError(error: any): void {
    this.sendNotification({
      type: 'error',
      title: 'System Error',
      message: error.message || 'An unexpected error occurred',
      persistent: true,
      category: 'error_alert',
      source: 'websocket-service',
    });
  }

  private handleConnectionStatus(status: any): void {
    if (status.connected === false) {
      this.sendNotification({
        type: 'warning',
        title: 'Connection Lost',
        message: 'WebSocket connection has been lost. Attempting to reconnect...',
        persistent: false,
        category: 'system_status',
        source: 'websocket-service',
      });
    } else if (status.connected === true && status.reconnected) {
      this.sendNotification({
        type: 'success',
        title: 'Connection Restored',
        message: 'WebSocket connection has been restored',
        persistent: false,
        category: 'system_status',
        source: 'websocket-service',
      });
    }
  }

  // Performance monitoring integration
  integrateWithPerformanceMonitor(performanceMonitor: any): void {
    if (!performanceMonitor) return;

    performanceMonitor.on('threshold_breach', (data: any) => {
      this.sendNotification({
        type: 'warning',
        title: 'Performance Threshold Breached',
        message: `${data.metric} has exceeded threshold: ${data.value}`,
        persistent: false,
        category: 'performance',
        source: 'performance-monitor',
      });
    });
  }

  // Maintenance integration
  scheduleMaintenanceNotification(message: string, scheduledTime: Date): void {
    const now = new Date();
    const delay = scheduledTime.getTime() - now.getTime();

    if (delay > 0) {
      setTimeout(() => {
        this.sendNotification({
          type: 'info',
          title: 'Scheduled Maintenance',
          message,
          persistent: true,
          category: 'maintenance',
          source: 'maintenance-scheduler',
        });
      }, delay);
    }
  }
}

// Export singleton instance
export const notificationService = new NotificationServiceImpl();
export default notificationService;
