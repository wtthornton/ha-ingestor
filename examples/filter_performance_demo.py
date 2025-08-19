#!/usr/bin/env python3
"""Demonstration of filter system performance optimizations.

This script showcases the performance optimizations implemented in Task 1.4:
- Filter result caching
- Regex pattern compilation optimization
- Performance metrics collection
- Filter chain profiling
- Bottleneck identification
"""

import asyncio
import random
import time

from ha_ingestor.filters import (
    AttributeFilter,
    DomainFilter,
    EntityFilter,
    FilterChain,
    TimeFilter,
)
from ha_ingestor.filters.performance import get_filter_profiler
from ha_ingestor.metrics.collector import get_metrics_collector
from ha_ingestor.models.events import Event


def create_sample_events(count: int = 1000) -> list[Event]:
    """Create sample events for testing.

    Args:
        count: Number of events to create

    Returns:
        List of sample events
    """
    domains = ["light", "switch", "sensor", "binary_sensor", "climate", "cover"]
    entity_ids = [
        "light.living_room",
        "light.kitchen",
        "light.bedroom",
        "switch.tv",
        "switch.coffee_maker",
        "switch.lamp",
        "sensor.temperature",
        "sensor.humidity",
        "sensor.motion",
        "binary_sensor.door",
        "binary_sensor.window",
        "binary_sensor.motion",
        "climate.thermostat",
        "climate.ac",
        "climate.heater",
        "cover.garage_door",
        "cover.window",
        "cover.blind",
    ]

    events = []
    for i in range(count):
        domain = random.choice(domains)
        entity_id = random.choice(entity_ids)

        event = Event(
            domain=domain,
            entity_id=entity_id,
            event_type="state_changed",
            timestamp=time.time() + i,
            attributes={
                "state": random.choice(["on", "off", "50", "75", "100"]),
                "temperature": random.uniform(18, 25),
                "humidity": random.uniform(30, 70),
                "battery": random.randint(10, 100),
            },
        )
        events.append(event)

    return events


async def demonstrate_filter_caching():
    """Demonstrate filter result caching performance."""
    print("\n" + "=" * 60)
    print("DEMONSTRATING FILTER RESULT CACHING")
    print("=" * 60)

    # Create a filter that will benefit from caching
    entity_filter = EntityFilter(
        patterns=["light.*", "switch.*", "sensor.*"], name="demo_entity_filter"
    )

    # Create sample events with many duplicates
    events = create_sample_events(1000)

    # First pass - no caching benefits
    print("First pass (no caching benefits):")
    start_time = time.time()

    for event in events[:100]:  # Test with first 100 events
        result = await entity_filter.process(event)

    first_pass_time = (time.time() - start_time) * 1000
    print(f"  Time: {first_pass_time:.2f}ms")
    print(f"  Cache hits: {entity_filter._cache_hits}")
    print(
        f"  Cache misses: {entity_filter._total_processed - entity_filter._cache_hits}"
    )

    # Second pass - should benefit from caching
    print("\nSecond pass (with caching benefits):")
    start_time = time.time()

    for event in events[:100]:  # Same events again
        result = await entity_filter.process(event)

    second_pass_time = (time.time() - start_time) * 1000
    print(f"  Time: {second_pass_time:.2f}ms")
    print(f"  Cache hits: {entity_filter._cache_hits}")
    print(
        f"  Cache misses: {entity_filter._total_processed - entity_filter._cache_hits}"
    )

    # Calculate improvement
    if first_pass_time > 0:
        improvement = ((first_pass_time - second_pass_time) / first_pass_time) * 100
        print(f"\nPerformance improvement: {improvement:.1f}%")

    # Show cache statistics
    stats = entity_filter.get_stats()
    print("\nCache statistics:")
    print(f"  Cache size: {stats['cache_size']}")
    print(f"  Cache hit rate: {stats['cache_hit_rate']:.2%}")


async def demonstrate_regex_optimization():
    """Demonstrate regex pattern compilation optimization."""
    print("\n" + "=" * 60)
    print("DEMONSTRATING REGEX PATTERN COMPILATION OPTIMIZATION")
    print("=" * 60)

    # Create filters with different pattern complexities
    simple_patterns = ["light.*", "switch.*", "sensor.*"]
    complex_patterns = [
        r"^light\.(living_room|kitchen|bedroom|bathroom|office)$",
        r"^switch\.(tv|coffee_maker|lamp|fan|heater)$",
        r"^sensor\.(temperature|humidity|motion|pressure|voltage)$",
    ]

    # Test simple patterns
    print("Testing simple patterns:")
    simple_filter = EntityFilter(simple_patterns, name="simple_patterns")
    start_time = time.time()

    events = create_sample_events(500)
    for event in events:
        await simple_filter.should_process(event)

    simple_time = (time.time() - start_time) * 1000
    print(f"  Simple patterns: {simple_time:.2f}ms")

    # Test complex patterns
    print("Testing complex patterns:")
    complex_filter = EntityFilter(complex_patterns, name="complex_patterns")
    start_time = time.time()

    for event in events:
        await complex_filter.should_process(event)

    complex_time = (time.time() - start_time) * 1000
    print(f"  Complex patterns: {complex_time:.2f}ms")

    # Show pattern optimization stats
    simple_stats = simple_filter.get_pattern_stats()
    complex_stats = complex_filter.get_pattern_stats()

    print("\nPattern optimization statistics:")
    print("  Simple patterns:")
    print(f"    Cache hit rate: {simple_stats['pattern_cache_hit_rate']:.2%}")
    print(f"    Pattern cache size: {simple_stats['pattern_cache_size']}")
    print("  Complex patterns:")
    print(f"    Cache hit rate: {complex_stats['pattern_cache_hit_rate']:.2%}")
    print(f"    Pattern cache size: {complex_stats['pattern_cache_size']}")


async def demonstrate_filter_chain_profiling():
    """Demonstrate filter chain profiling and bottleneck identification."""
    print("\n" + "=" * 60)
    print("DEMONSTRATING FILTER CHAIN PROFILING")
    print("=" * 60)

    # Create a complex filter chain
    chain = FilterChain(name="performance_demo_chain")

    # Add various filters
    chain.add_filter(DomainFilter(["light", "switch", "sensor"], name="domain_filter"))
    chain.add_filter(EntityFilter(["light.*", "switch.*"], name="entity_filter"))
    chain.add_filter(AttributeFilter({"state": ["on", "off"]}, name="attribute_filter"))
    chain.add_filter(
        TimeFilter(start_time="09:00", end_time="18:00", name="time_filter")
    )

    # Create events and process them
    events = create_sample_events(1000)

    print("Processing events through filter chain...")
    start_time = time.time()

    processed_count = 0
    filtered_count = 0

    for event in events:
        result = await chain.process_event(event)
        if result is None:
            filtered_count += 1
        else:
            processed_count += 1

    total_time = (time.time() - start_time) * 1000

    print("Processing complete:")
    print(f"  Total events: {len(events)}")
    print(f"  Processed: {processed_count}")
    print(f"  Filtered out: {filtered_count}")
    print(f"  Total time: {total_time:.2f}ms")
    print(f"  Average time per event: {total_time/len(events):.2f}ms")

    # Get profiling data
    profiler = get_filter_profiler()
    profile = profiler.get_chain_profile("performance_demo_chain")

    if profile:
        print("\nFilter chain profile:")
        print(f"  Total events: {profile.total_events}")
        print(f"  Filter rate: {profile.get_filter_rate():.2%}")
        print(f"  Average processing time: {profile.avg_processing_time_ms:.2f}ms")
        print(f"  95th percentile: {profile.get_percentile_time(95):.2f}ms")
        print(f"  99th percentile: {profile.get_percentile_time(99):.2f}ms")

        # Identify bottlenecks
        bottlenecks = profiler.identify_bottlenecks("performance_demo_chain")
        if bottlenecks:
            print("\nIdentified bottlenecks:")
            for bottleneck in bottlenecks:
                print(f"  - {bottleneck['type']}: {bottleneck.get('filter', 'N/A')}")
                print(f"    Recommendation: {bottleneck['recommendation']}")
        else:
            print("\nNo performance bottlenecks identified.")

    # Show filter statistics
    chain_stats = chain.get_stats()
    print("\nFilter chain statistics:")
    print(f"  Total filters: {chain_stats['total_filters']}")
    print(f"  Filter rate: {chain_stats['filter_rate']:.2%}")
    print(f"  Average processing time: {chain_stats['avg_processing_time_ms']:.2f}ms")

    # Show individual filter stats
    print("\nIndividual filter statistics:")
    for filter_stat in chain_stats["filter_stats"]:
        print(f"  {filter_stat['name']}:")
        print(f"    Cache hit rate: {filter_stat['cache_hit_rate']:.2%}")
        print(f"    Cache size: {filter_stat['cache_size']}")


async def demonstrate_metrics_collection():
    """Demonstrate performance metrics collection."""
    print("\n" + "=" * 60)
    print("DEMONSTRATING PERFORMANCE METRICS COLLECTION")
    print("=" * 60)

    # Get metrics collector
    metrics_collector = get_metrics_collector()

    # Create and use a filter to generate metrics
    filter_chain = FilterChain(name="metrics_demo_chain")
    filter_chain.add_filter(
        DomainFilter(["light", "switch"], name="demo_domain_filter")
    )
    filter_chain.add_filter(EntityFilter(["light.*"], name="demo_entity_filter"))

    # Process some events
    events = create_sample_events(500)

    print("Processing events to generate metrics...")
    for event in events:
        await filter_chain.process_event(event)

    print("Metrics collection complete!")
    print("Check Prometheus metrics endpoint for detailed metrics.")

    # Show some key metrics
    print("\nKey metrics collected:")
    print("  - Filter processing duration histograms")
    print("  - Filter cache hit/miss counters")
    print("  - Filter chain performance metrics")
    print("  - Cache size gauges")
    print("  - Event processing counters")


async def demonstrate_performance_export():
    """Demonstrate performance data export capabilities."""
    print("\n" + "=" * 60)
    print("DEMONSTRATING PERFORMANCE DATA EXPORT")
    print("=" * 60)

    profiler = get_filter_profiler()

    # Export performance data
    print("Exporting performance data...")

    # JSON export
    json_data = profiler.export_profile_data("json")
    print(f"JSON export length: {len(json_data)} characters")

    # CSV export
    csv_data = profiler.export_profile_data("csv")
    print(f"CSV export length: {len(csv_data)} characters")

    # Show performance summary
    summary = profiler.get_performance_summary()
    print("\nPerformance summary:")
    print(f"  Total chains profiled: {summary.get('total_chains', 0)}")
    print(f"  Profiler uptime: {summary.get('uptime_seconds', 0):.1f} seconds")

    if "chains" in summary:
        for chain_name, chain_data in summary["chains"].items():
            print(f"  Chain '{chain_name}':")
            print(f"    Events: {chain_data['total_events']}")
            print(f"    Filter rate: {chain_data['filter_rate']:.2%}")
            print(f"    Avg time: {chain_data['avg_processing_time_ms']:.2f}ms")


async def main():
    """Main demonstration function."""
    print("FILTER SYSTEM PERFORMANCE OPTIMIZATION DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the performance optimizations implemented in Task 1.4:")
    print("1. Filter result caching")
    print("2. Regex pattern compilation optimization")
    print("3. Performance metrics collection")
    print("4. Filter chain profiling")
    print("5. Bottleneck identification")
    print("6. Performance data export")

    try:
        # Run demonstrations
        await demonstrate_filter_caching()
        await demonstrate_regex_optimization()
        await demonstrate_filter_chain_profiling()
        await demonstrate_metrics_collection()
        await demonstrate_performance_export()

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("All performance optimizations have been demonstrated.")
        print("Check the metrics and profiling data for detailed insights.")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
