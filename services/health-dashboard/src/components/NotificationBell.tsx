import React from 'react';
import { useNotificationCenter } from '../contexts/NotificationContext';

interface NotificationBellProps {
  className?: string;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const { unreadCount, toggleCenter } = useNotificationCenter();

  return (
    <button
      onClick={toggleCenter}
      className={`
        relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md
        ${className}
      `}
      aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
    >
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M15 17h5l-5 5v-5zM9 7H4l5-5v5zM12 2a7 7 0 00-7 7c0 1.887.454 3.665 1.257 5.234L5.5 18.5h13l-1.257-4.266A6.97 6.97 0 0019 9a7 7 0 00-7-7z" 
        />
      </svg>
      
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-500 rounded-full">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  );
};
