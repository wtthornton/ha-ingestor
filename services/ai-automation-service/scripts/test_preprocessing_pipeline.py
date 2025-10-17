#!/usr/bin/env python3
"""
Test Preprocessing Pipeline
Validates the complete preprocessing pipeline with sample data
"""

import sys
import os
import time
import pandas as pd
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.preprocessing.event_preprocessor import EventPreprocessor
from src.preprocessing.processed_events import ProcessedEvents
from src.models.model_manager import get_model_manager

def test_preprocessing_pipeline():
    """Test the complete preprocessing pipeline"""
    
    print("🧪 Testing Preprocessing Pipeline")
    print("=" * 50)
    
    # Step 1: Create sample data
    print("\n1. Creating sample data...")
    from create_sample_data import create_sample_ha_events, create_sample_weather_data, create_sample_occupancy_data
    
    events_df = create_sample_ha_events(num_events=500, days_back=7)  # Smaller for testing
    weather_df = create_sample_weather_data(days_back=7)
    occupancy_df = create_sample_occupancy_data(days_back=7)
    
    print(f"   ✅ Generated {len(events_df)} events")
    print(f"   ✅ Generated {len(weather_df)} weather records")
    print(f"   ✅ Generated {len(occupancy_df)} occupancy records")
    
    # Step 2: Initialize preprocessor
    print("\n2. Initializing preprocessor...")
    model_manager = get_model_manager()
    preprocessor = EventPreprocessor(model_manager=model_manager)
    print("   ✅ Preprocessor initialized")
    
    # Step 3: Test preprocessing
    print("\n3. Running preprocessing pipeline...")
    start_time = time.time()
    
    try:
        processed_events = preprocessor.preprocess(events_df)
        processing_time = time.time() - start_time
        
        print(f"   ✅ Preprocessing completed in {processing_time:.2f}s")
        print(f"   ✅ Processed {len(processed_events.events)} events")
        
    except Exception as e:
        print(f"   ❌ Preprocessing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Validate results
    print("\n4. Validating results...")
    
    # Check basic structure
    if not processed_events.events:
        print("   ❌ No events processed")
        return False
    
    print(f"   ✅ Total events: {processed_events.total_events}")
    print(f"   ✅ Unique devices: {processed_events.unique_devices}")
    print(f"   ✅ Unique sessions: {processed_events.unique_sessions}")
    
    # Check features
    sample_event = processed_events.events[0]
    print(f"   ✅ Sample event features:")
    print(f"      - Device: {sample_event.device_name} ({sample_event.device_type})")
    print(f"      - Time: {sample_event.hour:02d}:{sample_event.minute:02d} ({sample_event.time_of_day})")
    print(f"      - Day: {sample_event.day_type} ({sample_event.season})")
    print(f"      - Session: {sample_event.session_id}")
    print(f"      - State change: {sample_event.old_state} → {sample_event.new_state}")
    
    # Check embeddings
    if sample_event.embedding is not None:
        print(f"   ✅ Embedding generated: {sample_event.embedding.shape}")
    else:
        print("   ⚠️  No embedding generated (model manager issue?)")
    
    # Step 5: Test model manager
    print("\n5. Testing model manager...")
    
    try:
        model_info = model_manager.get_model_info()
        print(f"   ✅ Model info: {model_info}")
        
        # Test embedding generation
        test_texts = ["Light turns on at 7 AM", "Coffee maker starts brewing"]
        embeddings = model_manager.generate_embeddings(test_texts)
        print(f"   ✅ Generated embeddings: {embeddings.shape}")
        
    except Exception as e:
        print(f"   ⚠️  Model manager test failed: {e}")
    
    # Step 6: Performance metrics
    print("\n6. Performance metrics...")
    
    events_per_second = len(processed_events.events) / processing_time
    print(f"   ✅ Processing speed: {events_per_second:.1f} events/second")
    
    if processing_time < 1.0:
        print("   ✅ Fast processing (< 1s)")
    else:
        print(f"   ⚠️  Slow processing ({processing_time:.2f}s)")
    
    # Step 7: Test pattern detection readiness
    print("\n7. Testing pattern detection readiness...")
    
    # Test device grouping
    device_events = processed_events.get_events_by_device('light.living_room')
    print(f"   ✅ Device grouping: {len(device_events)} events for living room light")
    
    # Test temporal grouping
    morning_events = processed_events.get_events_by_hour(7)
    print(f"   ✅ Temporal grouping: {len(morning_events)} events at 7 AM")
    
    # Test session grouping
    if processed_events.unique_sessions > 0:
        first_session = list(processed_events.session_index.keys())[0]
        session_events = processed_events.get_events_in_session(first_session)
        print(f"   ✅ Session grouping: {len(session_events)} events in first session")
    
    print("\n🎉 Preprocessing pipeline test completed successfully!")
    return True

def test_embedding_performance():
    """Test embedding generation performance"""
    
    print("\n🚀 Testing Embedding Performance")
    print("=" * 50)
    
    model_manager = get_model_manager()
    
    # Test with different batch sizes
    batch_sizes = [10, 50, 100, 500, 1000]
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        
        # Create test texts
        test_texts = [f"Device {i} turns on at {i%24:02d}:00" for i in range(batch_size)]
        
        # Time embedding generation
        start_time = time.time()
        try:
            embeddings = model_manager.generate_embeddings(test_texts)
            generation_time = time.time() - start_time
            
            events_per_second = batch_size / generation_time
            ms_per_event = (generation_time * 1000) / batch_size
            
            print(f"   ✅ Generated {batch_size} embeddings in {generation_time:.3f}s")
            print(f"   ✅ Speed: {events_per_second:.1f} events/second")
            print(f"   ✅ Latency: {ms_per_event:.1f}ms per event")
            
            # Check if we meet our 50ms target for 1000 events
            if batch_size == 1000 and ms_per_event <= 50:
                print("   🎯 TARGET MET: < 50ms per event for 1000 events")
            elif batch_size == 1000:
                print(f"   ⚠️  TARGET MISSED: {ms_per_event:.1f}ms per event (target: 50ms)")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    print("🧪 Preprocessing Pipeline Test Suite")
    print("=" * 60)
    
    # Test 1: Basic preprocessing
    success = test_preprocessing_pipeline()
    
    if success:
        # Test 2: Embedding performance
        test_embedding_performance()
        
        print("\n🎉 All tests completed!")
    else:
        print("\n❌ Tests failed - check errors above")
        sys.exit(1)
