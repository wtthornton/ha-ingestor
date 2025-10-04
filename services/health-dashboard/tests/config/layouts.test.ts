import { LAYOUT_CONFIGS, DEFAULT_LAYOUT, getLayoutConfig, getAllLayouts } from '../../src/config/layouts';

describe('Layout Configurations', () => {
  test('has all required layout configurations', () => {
    expect(LAYOUT_CONFIGS).toHaveProperty('overview');
    expect(LAYOUT_CONFIGS).toHaveProperty('detailed');
    expect(LAYOUT_CONFIGS).toHaveProperty('mobile');
    expect(LAYOUT_CONFIGS).toHaveProperty('compact');
  });

  test('each layout has required properties', () => {
    Object.values(LAYOUT_CONFIGS).forEach((layout) => {
      expect(layout).toHaveProperty('id');
      expect(layout).toHaveProperty('name');
      expect(layout).toHaveProperty('description');
      expect(layout).toHaveProperty('grid');
      expect(layout).toHaveProperty('widgets');

      // Check grid properties
      expect(layout.grid).toHaveProperty('columns');
      expect(layout.grid).toHaveProperty('rows');
      expect(layout.grid).toHaveProperty('gap');
      expect(typeof layout.grid.columns).toBe('number');
      expect(typeof layout.grid.rows).toBe('number');
      expect(typeof layout.grid.gap).toBe('number');

      // Check widgets array
      expect(Array.isArray(layout.widgets)).toBe(true);
      expect(layout.widgets.length).toBeGreaterThan(0);

      // Check each widget
      layout.widgets.forEach((widget) => {
        expect(widget).toHaveProperty('id');
        expect(widget).toHaveProperty('type');
        expect(widget).toHaveProperty('position');
        expect(widget).toHaveProperty('props');

        // Check position properties
        expect(widget.position).toHaveProperty('x');
        expect(widget.position).toHaveProperty('y');
        expect(widget.position).toHaveProperty('w');
        expect(widget.position).toHaveProperty('h');
        expect(typeof widget.position.x).toBe('number');
        expect(typeof widget.position.y).toBe('number');
        expect(typeof widget.position.w).toBe('number');
        expect(typeof widget.position.h).toBe('number');
      });
    });
  });

  test('overview layout configuration', () => {
    const overview = LAYOUT_CONFIGS.overview;
    
    expect(overview.id).toBe('overview');
    expect(overview.name).toBe('Overview');
    expect(overview.description).toBe('High-level system status with key metrics');
    expect(overview.grid.columns).toBe(12);
    expect(overview.grid.rows).toBe(8);
    expect(overview.grid.gap).toBe(16);
    expect(overview.widgets).toHaveLength(3);

    // Check specific widgets
    const healthCard = overview.widgets.find(w => w.id === 'health-card');
    expect(healthCard).toBeDefined();
    expect(healthCard?.type).toBe('HealthCard');
    expect(healthCard?.position).toEqual({ x: 0, y: 0, w: 4, h: 2 });

    const eventRateChart = overview.widgets.find(w => w.id === 'event-rate-chart');
    expect(eventRateChart).toBeDefined();
    expect(eventRateChart?.type).toBe('MetricsChart');
    expect(eventRateChart?.position).toEqual({ x: 4, y: 0, w: 8, h: 2 });
  });

  test('detailed layout configuration', () => {
    const detailed = LAYOUT_CONFIGS.detailed;
    
    expect(detailed.id).toBe('detailed');
    expect(detailed.name).toBe('Detailed');
    expect(detailed.description).toBe('Comprehensive monitoring with all available data');
    expect(detailed.grid.columns).toBe(12);
    expect(detailed.grid.rows).toBe(10);
    expect(detailed.grid.gap).toBe(16);
    expect(detailed.widgets).toHaveLength(5);

    // Should have more widgets than overview
    expect(detailed.widgets.length).toBeGreaterThan(LAYOUT_CONFIGS.overview.widgets.length);
  });

  test('mobile layout configuration', () => {
    const mobile = LAYOUT_CONFIGS.mobile;
    
    expect(mobile.id).toBe('mobile');
    expect(mobile.name).toBe('Mobile');
    expect(mobile.description).toBe('Touch-optimized layout for mobile devices');
    expect(mobile.grid.columns).toBe(1);
    expect(mobile.grid.rows).toBe(12);
    expect(mobile.grid.gap).toBe(12);
    expect(mobile.widgets).toHaveLength(3);

    // All widgets should span full width (w: 1)
    mobile.widgets.forEach(widget => {
      expect(widget.position.w).toBe(1);
    });
  });

  test('compact layout configuration', () => {
    const compact = LAYOUT_CONFIGS.compact;
    
    expect(compact.id).toBe('compact');
    expect(compact.name).toBe('Compact');
    expect(compact.description).toBe('Space-efficient layout for smaller screens');
    expect(compact.grid.columns).toBe(6);
    expect(compact.grid.rows).toBe(6);
    expect(compact.grid.gap).toBe(12);
    expect(compact.widgets).toHaveLength(3);
  });

  test('widget positions are within grid bounds', () => {
    Object.values(LAYOUT_CONFIGS).forEach((layout) => {
      layout.widgets.forEach((widget) => {
        const { x, y, w, h } = widget.position;
        
        // Widget should not exceed grid boundaries
        expect(x + w).toBeLessThanOrEqual(layout.grid.columns);
        expect(y + h).toBeLessThanOrEqual(layout.grid.rows);
        
        // Position should be non-negative
        expect(x).toBeGreaterThanOrEqual(0);
        expect(y).toBeGreaterThanOrEqual(0);
        expect(w).toBeGreaterThan(0);
        expect(h).toBeGreaterThan(0);
      });
    });
  });

  test('no overlapping widgets', () => {
    Object.values(LAYOUT_CONFIGS).forEach((layout) => {
      const occupied = new Set();
      
      layout.widgets.forEach((widget) => {
        const { x, y, w, h } = widget.position;
        
        // Check each cell this widget occupies
        for (let row = y; row < y + h; row++) {
          for (let col = x; col < x + w; col++) {
            const cellKey = `${row}-${col}`;
            expect(occupied.has(cellKey)).toBe(false);
            occupied.add(cellKey);
          }
        }
      });
    });
  });

  test('getLayoutConfig returns correct layout', () => {
    expect(getLayoutConfig('overview')).toBe(LAYOUT_CONFIGS.overview);
    expect(getLayoutConfig('detailed')).toBe(LAYOUT_CONFIGS.detailed);
    expect(getLayoutConfig('mobile')).toBe(LAYOUT_CONFIGS.mobile);
    expect(getLayoutConfig('compact')).toBe(LAYOUT_CONFIGS.compact);
  });

  test('getLayoutConfig returns null for invalid layout', () => {
    expect(getLayoutConfig('invalid')).toBeNull();
    expect(getLayoutConfig('')).toBeNull();
    expect(getLayoutConfig('unknown')).toBeNull();
  });

  test('getAllLayouts returns all layouts', () => {
    const allLayouts = getAllLayouts();
    expect(allLayouts).toHaveLength(4);
    expect(allLayouts).toContain(LAYOUT_CONFIGS.overview);
    expect(allLayouts).toContain(LAYOUT_CONFIGS.detailed);
    expect(allLayouts).toContain(LAYOUT_CONFIGS.mobile);
    expect(allLayouts).toContain(LAYOUT_CONFIGS.compact);
  });

  test('DEFAULT_LAYOUT is valid', () => {
    expect(DEFAULT_LAYOUT).toBe('overview');
    expect(LAYOUT_CONFIGS[DEFAULT_LAYOUT]).toBeDefined();
  });

  test('all layouts have unique IDs', () => {
    const ids = Object.values(LAYOUT_CONFIGS).map(layout => layout.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  test('all layouts have unique names', () => {
    const names = Object.values(LAYOUT_CONFIGS).map(layout => layout.name);
    const uniqueNames = new Set(names);
    expect(uniqueNames.size).toBe(names.length);
  });
});
