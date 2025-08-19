#!/usr/bin/env python3
"""Example usage of the Home Assistant event filter system.

This script demonstrates how to create and use various types of filters
to process Home Assistant events.
"""

import asyncio
from datetime import datetime

from ha_ingestor.filters import (
    AttributeFilter,
    CustomFilter,
    DomainFilter,
    EntityFilter,
    FilterChain,
    TimeFilter,
)
from ha_ingestor.models.events import Event


def create_sample_events():
    """Create sample events for testing."""
    events = [
        # Light events
        Event(
            domain="light",
            entity_id="light.living_room",
            attributes={"state": "on", "brightness": 255},
            timestamp=datetime.now(),
        ),
        Event(
            domain="light",
            entity_id="light.kitchen",
            attributes={"state": "off", "brightness": 0},
            timestamp=datetime.now(),
        ),
        # Switch events
        Event(
            domain="switch",
            entity_id="switch.coffee_maker",
            attributes={"state": "on"},
            timestamp=datetime.now(),
        ),
        # Sensor events
        Event(
            domain="sensor",
            entity_id="sensor.temperature",
            attributes={"state": "22.5", "unit_of_measurement": "°C"},
            timestamp=datetime.now(),
        ),
        Event(
            domain="sensor",
            entity_id="sensor.humidity",
            attributes={"state": "65", "unit_of_measurement": "%"},
            timestamp=datetime.now(),
        ),
        # Climate events
        Event(
            domain="climate",
            entity_id="climate.living_room",
            attributes={"state": "heat", "temperature": 21.0},
            timestamp=datetime.now(),
        ),
    ]
    return events


async def demonstrate_domain_filter():
    """Demonstrate domain filtering."""
    print("\n=== Domain Filter Example ===")

    # Create filter that only allows light and switch events
    domain_filter = DomainFilter(["light", "switch"])

    events = create_sample_events()

    print(f"Filter: {domain_filter.name}")
    print(f"Allowed domains: {domain_filter.get_allowed_domains()}")
    print()

    for event in events:
        should_process = await domain_filter.should_process(event)
        status = "ALLOWED" if should_process else "BLOCKED"
        print(
            f"{status}: {event.domain}.{event.entity_id} - {event.attributes.get('state', 'N/A')}"
        )


async def demonstrate_entity_filter():
    """Demonstrate entity ID pattern filtering."""
    print("\n=== Entity Filter Example ===")

    # Create filter that only allows living room entities
    entity_filter = EntityFilter(["*.living_room"], use_regex=False)

    events = create_sample_events()

    print(f"Filter: {entity_filter.name}")
    print(f"Patterns: {entity_filter.get_patterns()}")
    print()

    for event in events:
        should_process = await entity_filter.should_process(event)
        status = "ALLOWED" if should_process else "BLOCKED"
        print(
            f"{status}: {event.domain}.{event.entity_id} - {event.attributes.get('state', 'N/A')}"
        )


async def demonstrate_attribute_filter():
    """Demonstrate attribute-based filtering."""
    print("\n=== Attribute Filter Example ===")

    # Create filter that only allows events with state "on"
    attribute_filter = AttributeFilter("state", "on", "eq")

    events = create_sample_events()

    print(f"Filter: {attribute_filter.name}")
    print(f"Attribute: {attribute_filter.attribute}")
    print(f"Operator: {attribute_filter.operator}")
    print(f"Value: {attribute_filter.value}")
    print()

    for event in events:
        should_process = await attribute_filter.should_process(event)
        status = "ALLOWED" if should_process else "BLOCKED"
        print(
            f"{status}: {event.domain}.{event.entity_id} - {event.attributes.get('state', 'N/A')}"
        )


async def demonstrate_time_filter():
    """Demonstrate time-based filtering."""
    print("\n=== Time Filter Example ===")

    # Create filter that only allows events during business hours
    time_filter = TimeFilter(business_hours=True)

    events = create_sample_events()

    print(f"Filter: {time_filter.name}")
    print(f"Business hours: {time_filter.business_hours}")
    print(f"Time ranges: {time_filter.time_ranges}")
    print(f"Days of week: {time_filter.days_of_week}")
    print()

    for event in events:
        should_process = await time_filter.should_process(event)
        status = "ALLOWED" if should_process else "BLOCKED"
        print(f"{status}: {event.domain}.{event.entity_id} at {event.timestamp}")


async def demonstrate_custom_filter():
    """Demonstrate custom filtering."""
    print("\n=== Custom Filter Example ===")

    # Define custom filter function
    def high_value_filter(event, min_value=100):
        """Only allow events with numeric attributes above threshold."""
        if not event.attributes:
            return False

        for key, value in event.attributes.items():
            try:
                if isinstance(value, (int, float)) and value >= min_value:
                    return True
            except (TypeError, ValueError):
                continue
        return False

    # Create custom filter
    custom_filter = CustomFilter(high_value_filter, config={"min_value": 100})

    events = create_sample_events()

    print(f"Filter: {custom_filter.name}")
    print(f"Function: {custom_filter.filter_func.__name__}")
    print(f"Config: {custom_filter.config}")
    print()

    for event in events:
        should_process = await custom_filter.should_process(event)
        status = "ALLOWED" if should_process else "BLOCKED"
        print(f"{status}: {event.domain}.{event.entity_id} - {event.attributes}")


async def demonstrate_filter_chain():
    """Demonstrate filter chain processing."""
    print("\n=== Filter Chain Example ===")

    # Create a filter chain
    chain = FilterChain(name="example_chain")

    # Add filters
    chain.add_filter(DomainFilter(["light", "switch"]))
    chain.add_filter(EntityFilter(["*.living_room", "*.kitchen"]))
    chain.add_filter(AttributeFilter("state", "on", "eq"))

    print(f"Filter chain: {chain.name}")
    print(f"Total filters: {len(chain.filters)}")
    for i, filter in enumerate(chain.filters):
        print(f"  {i+1}. {filter.name}")
    print()

    events = create_sample_events()

    for event in events:
        result = await chain.process_event(event)
        if result:
            print(
                f"ALLOWED: {event.domain}.{event.entity_id} - {event.attributes.get('state', 'N/A')}"
            )
        else:
            print(
                f"BLOCKED: {event.domain}.{event.entity_id} - {event.attributes.get('state', 'N/A')}"
            )

    # Show chain statistics
    stats = chain.get_stats()
    print("\nChain Statistics:")
    print(f"  Total processed: {stats['total_processed']}")
    print(f"  Total filtered: {stats['total_filtered']}")
    print(f"  Filter rate: {stats['filter_rate']:.2%}")
    print(f"  Avg processing time: {stats['avg_processing_time_ms']:.2f}ms")


async def main():
    """Run all filter demonstrations."""
    print("Home Assistant Event Filter System Demonstration")
    print("=" * 50)

    await demonstrate_domain_filter()
    await demonstrate_entity_filter()
    await demonstrate_attribute_filter()
    await demonstrate_time_filter()
    await demonstrate_custom_filter()
    await demonstrate_filter_chain()

    print("\n" + "=" * 50)
    print("Demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
