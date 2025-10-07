#!/usr/bin/env python3
"""
Simple script to run Nabu Casa connection test
Usage: python run_nabu_casa_test.py YOUR_NABU_CASA_TOKEN
"""

import asyncio
import sys
import os

# Add the test script to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_nabu_casa_connection import NabuCasaConnectionTest

async def main():
    # Get token from command line argument
    if len(sys.argv) != 2:
        print("Usage: python run_nabu_casa_test.py YOUR_NABU_CASA_TOKEN")
        print("Or set environment variable: export NABU_CASA_TOKEN=your_token")
        sys.exit(1)
    
    # Set the token as environment variable
    os.environ["NABU_CASA_TOKEN"] = sys.argv[1]
    
    # Run the test
    test = NabuCasaConnectionTest()
    success = await test.run_test()
    
    if success:
        print("\n🎉 SUCCESS: Nabu Casa connection is working!")
        print("You can now implement the fallback mechanism.")
    else:
        print("\n❌ FAILED: Nabu Casa connection test failed")
        print("Please check your token and network connectivity.")

if __name__ == "__main__":
    asyncio.run(main())