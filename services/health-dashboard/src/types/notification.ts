export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  persistent: boolean;
  category?: NotificationCategory;
  source?: string;
  actions?: NotificationAction[];
  metadata?: Record<string, any>;
}

export type NotificationCategory = 
  | 'system_status'
  | 'error_alert'
  | 'performance'
  | 'maintenance'
  | 'user_action'
  | 'data_update';

export interface NotificationAction {
  id: string;
  label: string;
  action: () => void;
  type?: 'primary' | 'secondary' | 'danger';
}

export interface NotificationPreferences {
  enabled: boolean;
  categories: {
    [K in NotificationCategory]: boolean;
  };
  severity: {
    info: boolean;
    warning: boolean;
    error: boolean;
    success: boolean;
  };
  thresholds: {
    maxNotifications: number;
    autoDismissDelay: number; // in milliseconds
    persistentThreshold: number; // minimum severity for persistent notifications
  };
  channels: {
    toast: boolean;
    center: boolean;
    sound: boolean;
  };
}

export interface NotificationState {
  notifications: Notification[];
  preferences: NotificationPreferences;
  unreadCount: number;
  isCenterOpen: boolean;
}

export interface NotificationContextType {
  notifications: Notification[];
  preferences: NotificationPreferences;
  unreadCount: number;
  isCenterOpen: boolean;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
  updatePreferences: (preferences: Partial<NotificationPreferences>) => void;
  toggleCenter: () => void;
}

export interface NotificationService {
  sendNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  subscribe: (callback: (notification: Notification) => void) => () => void;
  updatePreferences: (preferences: Partial<NotificationPreferences>) => void;
  getPreferences: () => NotificationPreferences;
}

export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
  enabled: true,
  categories: {
    system_status: true,
    error_alert: true,
    performance: true,
    maintenance: true,
    user_action: false,
    data_update: false,
  },
  severity: {
    info: true,
    warning: true,
    error: true,
    success: true,
  },
  thresholds: {
    maxNotifications: 50,
    autoDismissDelay: 5000,
    persistentThreshold: 2, // warning and above
  },
  channels: {
    toast: true,
    center: true,
    sound: false,
  },
};
