import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConfigurationEditor } from '../../src/components/ConfigurationEditor';
import { apiService } from '../../src/services/api';

// Mock the API service
vi.mock('../../src/services/api');
const mockApiService = apiService as any;

const mockConfiguration = {
  home_assistant_url: 'http://localhost:8123',
  home_assistant_token: 'secret-token',
  log_level: 'INFO',
  max_workers: 10,
  batch_size: 100,
  enable_weather: true,
};

describe('ConfigurationEditor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.updateConfiguration.mockResolvedValue({ success: true });
  });

  it('renders configuration editor correctly', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    expect(screen.getByText('Edit Configuration: websocket-ingestion')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
  });

  it('displays all configuration fields', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    expect(screen.getByDisplayValue('http://localhost:8123')).toBeInTheDocument();
    expect(screen.getByDisplayValue('secret-token')).toBeInTheDocument();
    expect(screen.getByDisplayValue('INFO')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByDisplayValue('100')).toBeInTheDocument();
  });

  it('handles string field updates', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: 'http://new-url:8123' } });
    
    expect(urlInput).toHaveValue('http://new-url:8123');
  });

  it('handles number field updates', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const workersInput = screen.getByDisplayValue('10');
    fireEvent.change(workersInput, { target: { value: '20' } });
    
    expect(workersInput).toHaveValue(20);
  });

  it('handles boolean field updates', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
    
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  it('validates required fields', async () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: '' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });
  });

  it('validates number fields', async () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const workersInput = screen.getByDisplayValue('10');
    fireEvent.change(workersInput, { target: { value: 'invalid' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('Value must be a number')).toBeInTheDocument();
    });
  });

  it('saves configuration changes', async () => {
    const mockOnSave = jest.fn();
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
        onSave={mockOnSave}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: 'http://new-url:8123' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockApiService.updateConfiguration).toHaveBeenCalledWith(
        'websocket-ingestion',
        [
          {
            key: 'home_assistant_url',
            value: 'http://new-url:8123',
            reason: 'Updated via configuration interface',
          },
        ]
      );
    });
    
    expect(mockOnSave).toHaveBeenCalled();
  });

  it('calls onCancel when Cancel button is clicked', () => {
    const mockOnCancel = jest.fn();
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
        onCancel={mockOnCancel}
      />
    );
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('disables Save button when no changes are made', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const saveButton = screen.getByText('Save Changes');
    expect(saveButton).toBeDisabled();
  });

  it('enables Save button when changes are made', () => {
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: 'http://new-url:8123' } });
    
    const saveButton = screen.getByText('Save Changes');
    expect(saveButton).not.toBeDisabled();
  });

  it('shows loading state during save', async () => {
    // Mock a delayed response
    mockApiService.updateConfiguration.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );
    
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: 'http://new-url:8123' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });

  it('displays error message when save fails', async () => {
    mockApiService.updateConfiguration.mockRejectedValue(new Error('Save failed'));
    
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={mockConfiguration}
      />
    );
    
    const urlInput = screen.getByDisplayValue('http://localhost:8123');
    fireEvent.change(urlInput, { target: { value: 'http://new-url:8123' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('handles JSON object fields', () => {
    const configWithObject = {
      ...mockConfiguration,
      custom_settings: { timeout: 30, retries: 3 },
    };
    
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={configWithObject}
      />
    );
    
    const jsonTextarea = screen.getByDisplayValue('{\n  "timeout": 30,\n  "retries": 3\n}');
    expect(jsonTextarea).toBeInTheDocument();
  });

  it('handles JSON array fields', () => {
    const configWithArray = {
      ...mockConfiguration,
      allowed_domains: ['sensor', 'binary_sensor', 'switch'],
    };
    
    render(
      <ConfigurationEditor
        service="websocket-ingestion"
        configuration={configWithArray}
      />
    );
    
    const jsonTextarea = screen.getByDisplayValue('[\n  "sensor",\n  "binary_sensor",\n  "switch"\n]');
    expect(jsonTextarea).toBeInTheDocument();
  });
});
