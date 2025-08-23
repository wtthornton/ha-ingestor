"""Test the filter system."""

from datetime import datetime

import pytest

from ha_ingestor.filters import (
    AttributeFilter,
    CustomFilter,
    DomainFilter,
    EntityFilter,
    FilterChain,
    TimeFilter,
)
from ha_ingestor.models.mqtt_event import MQTTEvent


class TestDomainFilter:
    """Test domain filter functionality."""

    def test_domain_filter_initialization(self):
        """Test domain filter initialization."""
        filter = DomainFilter(["light", "switch"])
        assert filter.domains == ["light", "switch"]
        assert filter.name == "domain_filter_light_switch"

    def test_domain_filter_single_domain(self):
        """Test domain filter with single domain."""
        filter = DomainFilter("light")
        assert filter.domains == ["light"]

    def test_domain_filter_case_insensitive(self):
        """Test domain filter is case insensitive."""
        filter = DomainFilter(["Light", "SWITCH"])
        assert "light" in filter.domains
        assert "switch" in filter.domains

    @pytest.mark.asyncio
    async def test_domain_filter_allows_matching_domain(self):
        """Test domain filter allows matching domains."""
        filter = DomainFilter(["light", "switch"])
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_domain_filter_blocks_non_matching_domain(self):
        """Test domain filter blocks non-matching domains."""
        filter = DomainFilter(["light", "switch"])
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="25.5",
            state="25.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is False


class TestEntityFilter:
    """Test entity filter functionality."""

    def test_entity_filter_initialization(self):
        """Test entity filter initialization."""
        filter = EntityFilter(["light.*", "switch.*"])
        assert filter.patterns == ["light.*", "switch.*"]
        assert filter.use_regex is True

    def test_entity_filter_glob_mode(self):
        """Test entity filter in glob mode."""
        filter = EntityFilter(["light.*"], use_regex=False)
        assert filter.use_regex is False

    @pytest.mark.asyncio
    async def test_entity_filter_matches_pattern(self):
        """Test entity filter matches patterns."""
        filter = EntityFilter([".*"])  # Match any entity ID
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_entity_filter_blocks_non_matching_pattern(self):
        """Test entity filter blocks non-matching patterns."""
        filter = EntityFilter(["light.*"])
        event = MQTTEvent(
            topic="homeassistant/switch/main_power/state",
            payload="off",
            state="off",
            domain="switch",
            entity_id="main_power",
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is False


class TestAttributeFilter:
    """Test attribute filter functionality."""

    def test_attribute_filter_initialization(self):
        """Test attribute filter initialization."""
        filter = AttributeFilter("state", "on")
        assert filter.attribute == "state"
        assert filter.value == "on"
        assert filter.operator == "eq"

    @pytest.mark.asyncio
    async def test_attribute_filter_equals_operator(self):
        """Test attribute filter with equals operator."""
        filter = AttributeFilter("state", "on", "eq")
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            attributes={"state": "on"},
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_attribute_filter_greater_than_operator(self):
        """Test attribute filter with greater than operator."""
        filter = AttributeFilter("brightness", 100, "gt")
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="150",
            state="150",
            domain="light",
            entity_id="living_room",
            attributes={"brightness": 150},
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True


class TestTimeFilter:
    """Test time filter functionality."""

    def test_time_filter_initialization(self):
        """Test time filter initialization."""
        filter = TimeFilter()
        assert filter.time_ranges == []
        assert filter.days_of_week == []
        assert filter.business_hours is False

    def test_time_filter_business_hours(self):
        """Test time filter with business hours."""
        filter = TimeFilter(business_hours=True)
        assert filter.business_hours is True
        assert len(filter.time_ranges) == 1
        assert len(filter.days_of_week) == 5  # Mon-Fri

    @pytest.mark.asyncio
    async def test_time_filter_business_hours_allows_workday(self):
        """Test time filter allows business hours on workdays."""
        filter = TimeFilter(business_hours=True)

        # Monday at 10 AM
        event_time = datetime(2024, 1, 1, 10, 0)  # Monday
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            timestamp=event_time,
        )

        result = await filter.should_process(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_time_filter_business_hours_blocks_weekend(self):
        """Test time filter blocks business hours on weekends."""
        filter = TimeFilter(business_hours=True)

        # Saturday at 10 AM
        event_time = datetime(2024, 1, 6, 10, 0)  # Saturday
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            timestamp=event_time,
        )

        result = await filter.should_process(event)
        assert result is False


class TestFilterChain:
    """Test filter chain functionality."""

    def test_filter_chain_initialization(self):
        """Test filter chain initialization."""
        chain = FilterChain()
        assert chain.filters == []
        assert chain.name == "filter_chain"

    def test_filter_chain_add_filter(self):
        """Test adding filters to chain."""
        chain = FilterChain()
        domain_filter = DomainFilter(["light"])

        chain.add_filter(domain_filter)
        assert len(chain.filters) == 1
        assert chain.filters[0] == domain_filter

    @pytest.mark.asyncio
    async def test_filter_chain_processes_event_through_all_filters(self):
        """Test filter chain processes event through all filters."""
        chain = FilterChain()

        # Add filters
        domain_filter = DomainFilter(["light"])
        entity_filter = EntityFilter([".*"])  # Match any entity ID
        attribute_filter = AttributeFilter("state", "on")

        chain.add_filter(domain_filter)
        chain.add_filter(entity_filter)
        chain.add_filter(attribute_filter)

        # Create event that should pass all filters
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            attributes={"state": "on"},
            timestamp=datetime.now(),
        )

        result = await chain.process_event(event)
        assert result is not None
        assert result.domain == "light"
        assert result.entity_id == "living_room"

        # Create event that should be blocked by first filter
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="25.5",
            state="25.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
        )

        result = await chain.process_event(event)
        assert result is None  # Event was filtered out


class TestCustomFilter:
    """Test custom filter functionality."""

    def test_custom_filter_initialization(self):
        """Test custom filter initialization."""

        def filter_func(event):
            return event.domain == "light"

        filter = CustomFilter(filter_func)
        assert filter.filter_func == filter_func
        assert filter.transform_func is None

    @pytest.mark.asyncio
    async def test_custom_filter_uses_custom_function(self):
        """Test custom filter uses custom function."""

        def filter_func(event):
            return event.domain == "light"

        filter = CustomFilter(filter_func)
        event = MQTTEvent(
            topic="homeassistant/light/living_room/state",
            payload="on",
            state="on",
            domain="light",
            entity_id="living_room",
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_custom_filter_with_config(self):
        """Test custom filter with configuration."""

        def filter_func(event, config):
            min_value = config.get("min_value", 0)
            return event.get_attribute("value", 0) >= min_value

        filter = CustomFilter(filter_func, config={"min_value": 50})
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="75",
            state="75",
            domain="sensor",
            entity_id="temperature",
            attributes={"value": 75},
            timestamp=datetime.now(),
        )

        result = await filter.should_process(event)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
