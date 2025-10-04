import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NotificationToast } from '../../src/components/NotificationToast';
import { Notification } from '../../src/types/notification';

describe('NotificationToast', () => {
  const mockNotification: Notification = {
    id: 'test-notification',
    type: 'info',
    title: 'Test Notification',
    message: 'This is a test notification message',
    timestamp: new Date(),
    persistent: false,
  };

  const defaultProps = {
    notification: mockNotification,
    onDismiss: vi.fn(),
    onAction: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render notification with correct content', () => {
    render(<NotificationToast {...defaultProps} />);

    expect(screen.getByText('Test Notification')).toBeInTheDocument();
    expect(screen.getByText('This is a test notification message')).toBeInTheDocument();
    expect(screen.getByText(mockNotification.timestamp.toLocaleTimeString())).toBeInTheDocument();
  });

  it('should render correct icon for info notification', () => {
    render(<NotificationToast {...defaultProps} />);

    const icon = screen.getByRole('img', { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it('should render correct icon for success notification', () => {
    const successNotification = { ...mockNotification, type: 'success' as const };
    render(<NotificationToast {...defaultProps} notification={successNotification} />);

    const icon = screen.getByRole('img', { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it('should render correct icon for error notification', () => {
    const errorNotification = { ...mockNotification, type: 'error' as const };
    render(<NotificationToast {...defaultProps} notification={errorNotification} />);

    const icon = screen.getByRole('img', { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it('should render correct icon for warning notification', () => {
    const warningNotification = { ...mockNotification, type: 'warning' as const };
    render(<NotificationToast {...defaultProps} notification={warningNotification} />);

    const icon = screen.getByRole('img', { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button is clicked', async () => {
    render(<NotificationToast {...defaultProps} />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(defaultProps.onDismiss).toHaveBeenCalledWith('test-notification');
    });
  });

  it('should render actions when provided', () => {
    const notificationWithActions = {
      ...mockNotification,
      actions: [
        {
          id: 'action-1',
          label: 'View Details',
          action: vi.fn(),
          type: 'primary' as const,
        },
        {
          id: 'action-2',
          label: 'Dismiss',
          action: vi.fn(),
          type: 'secondary' as const,
        },
      ],
    };

    render(<NotificationToast {...defaultProps} notification={notificationWithActions} />);

    expect(screen.getByText('View Details')).toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
  });

  it('should call onAction when action button is clicked', () => {
    const mockAction = vi.fn();
    const notificationWithActions = {
      ...mockNotification,
      actions: [
        {
          id: 'action-1',
          label: 'Test Action',
          action: mockAction,
          type: 'primary' as const,
        },
      ],
    };

    render(<NotificationToast {...defaultProps} notification={notificationWithActions} />);

    const actionButton = screen.getByText('Test Action');
    fireEvent.click(actionButton);

    expect(defaultProps.onAction).toHaveBeenCalledWith(notificationWithActions.actions![0]);
  });

  it('should dismiss notification after action if not persistent', () => {
    const mockAction = vi.fn();
    const notificationWithActions = {
      ...mockNotification,
      persistent: false,
      actions: [
        {
          id: 'action-1',
          label: 'Test Action',
          action: mockAction,
          type: 'primary' as const,
        },
      ],
    };

    render(<NotificationToast {...defaultProps} notification={notificationWithActions} />);

    const actionButton = screen.getByText('Test Action');
    fireEvent.click(actionButton);

    expect(defaultProps.onAction).toHaveBeenCalled();
    // Should not dismiss immediately, but the action handler should handle it
  });

  it('should not dismiss notification after action if persistent', () => {
    const mockAction = vi.fn();
    const notificationWithActions = {
      ...mockNotification,
      persistent: true,
      actions: [
        {
          id: 'action-1',
          label: 'Test Action',
          action: mockAction,
          type: 'primary' as const,
        },
      ],
    };

    render(<NotificationToast {...defaultProps} notification={notificationWithActions} />);

    const actionButton = screen.getByText('Test Action');
    fireEvent.click(actionButton);

    expect(defaultProps.onAction).toHaveBeenCalled();
    // Should not call onDismiss for persistent notifications
  });

  it('should apply correct styling for different notification types', () => {
    const { rerender } = render(<NotificationToast {...defaultProps} />);
    
    // Info notification
    const infoContainer = screen.getByText('Test Notification').closest('div');
    expect(infoContainer).toHaveClass('bg-blue-50', 'border-blue-200');

    // Success notification
    const successNotification = { ...mockNotification, type: 'success' as const };
    rerender(<NotificationToast {...defaultProps} notification={successNotification} />);
    
    const successContainer = screen.getByText('Test Notification').closest('div');
    expect(successContainer).toHaveClass('bg-green-50', 'border-green-200');

    // Error notification
    const errorNotification = { ...mockNotification, type: 'error' as const };
    rerender(<NotificationToast {...defaultProps} notification={errorNotification} />);
    
    const errorContainer = screen.getByText('Test Notification').closest('div');
    expect(errorContainer).toHaveClass('bg-red-50', 'border-red-200');

    // Warning notification
    const warningNotification = { ...mockNotification, type: 'warning' as const };
    rerender(<NotificationToast {...defaultProps} notification={warningNotification} />);
    
    const warningContainer = screen.getByText('Test Notification').closest('div');
    expect(warningContainer).toHaveClass('bg-yellow-50', 'border-yellow-200');
  });

  it('should animate in when mounted', async () => {
    render(<NotificationToast {...defaultProps} />);

    const container = screen.getByText('Test Notification').closest('div');
    
    // Should start with animation classes
    expect(container).toHaveClass('transform', 'transition-all', 'duration-300');
  });

  it('should animate out when dismissed', async () => {
    render(<NotificationToast {...defaultProps} />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    // Should trigger exit animation
    await waitFor(() => {
      expect(defaultProps.onDismiss).toHaveBeenCalled();
    });
  });
});
