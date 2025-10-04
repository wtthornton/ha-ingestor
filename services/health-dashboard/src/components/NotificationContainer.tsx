import React from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { NotificationToast } from './NotificationToast';
import { NotificationCenter } from './NotificationCenter';

interface NotificationContainerProps {
  className?: string;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({ className = '' }) => {
  const { notifications, preferences } = useNotifications();

  // Filter notifications for toast display
  const toastNotifications = notifications.filter(notification => {
    // Only show recent notifications as toasts
    const isRecent = Date.now() - notification.timestamp.getTime() < 10000; // 10 seconds
    return isRecent && preferences.channels.toast;
  });

  return (
    <>
      {/* Toast Notifications */}
      <div className={`fixed top-4 right-4 z-40 space-y-2 ${className}`}>
        {toastNotifications.map((notification) => (
          <NotificationToast
            key={notification.id}
            notification={notification}
            onDismiss={(id) => {
              // Toast dismissals are handled by auto-dismiss in the context
            }}
          />
        ))}
      </div>

      {/* Notification Center */}
      <NotificationCenter />
    </>
  );
};
