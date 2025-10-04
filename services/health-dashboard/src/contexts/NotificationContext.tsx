import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { 
  Notification, 
  NotificationState, 
  NotificationContextType, 
  NotificationPreferences,
  DEFAULT_NOTIFICATION_PREFERENCES 
} from '../types/notification';
import { notificationService } from '../services/notificationService';

// Action types
type NotificationAction =
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'MARK_AS_READ'; payload: string }
  | { type: 'MARK_ALL_AS_READ' }
  | { type: 'CLEAR_NOTIFICATIONS' }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<NotificationPreferences> }
  | { type: 'TOGGLE_CENTER' }
  | { type: 'SET_UNREAD_COUNT'; payload: number };

// Initial state
const initialState: NotificationState = {
  notifications: [],
  preferences: DEFAULT_NOTIFICATION_PREFERENCES,
  unreadCount: 0,
  isCenterOpen: false,
};

// Reducer
function notificationReducer(state: NotificationState, action: NotificationAction): NotificationState {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      const newNotifications = [action.payload, ...state.notifications];
      // Limit notifications based on preferences
      const limitedNotifications = newNotifications.slice(0, state.preferences.thresholds.maxNotifications);
      
      return {
        ...state,
        notifications: limitedNotifications,
        unreadCount: state.unreadCount + 1,
      };

    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
        unreadCount: Math.max(0, state.unreadCount - 1),
      };

    case 'MARK_AS_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => 
          n.id === action.payload ? { ...n, persistent: false } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      };

    case 'MARK_ALL_AS_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => ({ ...n, persistent: false })),
        unreadCount: 0,
      };

    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        notifications: [],
        unreadCount: 0,
      };

    case 'UPDATE_PREFERENCES':
      const updatedPreferences = { ...state.preferences, ...action.payload };
      notificationService.updatePreferences(action.payload);
      return {
        ...state,
        preferences: updatedPreferences,
      };

    case 'TOGGLE_CENTER':
      return {
        ...state,
        isCenterOpen: !state.isCenterOpen,
      };

    case 'SET_UNREAD_COUNT':
      return {
        ...state,
        unreadCount: action.payload,
      };

    default:
      return state;
  }
}

// Context
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// Provider component
interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [state, dispatch] = useReducer(notificationReducer, initialState);

  // Subscribe to notification service
  useEffect(() => {
    const unsubscribe = notificationService.subscribe((notification) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
    });

    return unsubscribe;
  }, []);

  // Auto-dismiss non-persistent notifications
  useEffect(() => {
    const autoDismissDelay = state.preferences.thresholds.autoDismissDelay;
    
    const timers = state.notifications
      .filter(n => !n.persistent)
      .map(notification => {
        return setTimeout(() => {
          dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id });
        }, autoDismissDelay);
      });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [state.notifications, state.preferences.thresholds.autoDismissDelay]);

  // Context value
  const contextValue: NotificationContextType = {
    notifications: state.notifications,
    preferences: state.preferences,
    unreadCount: state.unreadCount,
    isCenterOpen: state.isCenterOpen,
    
    addNotification: (notificationData) => {
      notificationService.sendNotification(notificationData);
    },
    
    removeNotification: (id) => {
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
    },
    
    markAsRead: (id) => {
      dispatch({ type: 'MARK_AS_READ', payload: id });
    },
    
    markAllAsRead: () => {
      dispatch({ type: 'MARK_ALL_AS_READ' });
    },
    
    clearNotifications: () => {
      dispatch({ type: 'CLEAR_NOTIFICATIONS' });
    },
    
    updatePreferences: (preferences) => {
      dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
    },
    
    toggleCenter: () => {
      dispatch({ type: 'TOGGLE_CENTER' });
    },
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
}

// Hook to use notification context
export function useNotifications(): NotificationContextType {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

// Hook for notification preferences
export function useNotificationPreferences() {
  const { preferences, updatePreferences } = useNotifications();
  
  return {
    preferences,
    updatePreferences,
  };
}

// Hook for notification center
export function useNotificationCenter() {
  const { 
    notifications, 
    unreadCount, 
    isCenterOpen, 
    toggleCenter, 
    markAsRead, 
    markAllAsRead, 
    clearNotifications 
  } = useNotifications();
  
  return {
    notifications,
    unreadCount,
    isCenterOpen,
    toggleCenter,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}
