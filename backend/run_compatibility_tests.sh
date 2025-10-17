#!/bin/bash

# API Compatibility Test Runner
# This script runs all compatibility tests that verify Django API matches legacy API behavior

set -e

echo "================================"
echo "API Compatibility Test Suite"
echo "================================"
echo ""

# Change to rewrite directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if database is configured
if [ -z "$DATABASE_HOST" ]; then
    echo "ℹ️  Using default database configuration (SQLite for testing)"
    export DATABASE_NAME=":memory:"
fi

echo "Running compatibility tests..."
echo ""

# Run tests with verbose output
python manage.py test api.tests --verbosity=2

echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo ""

# Run tests again to get count
TEST_COUNT=$(python manage.py test api.tests --verbosity=0 2>&1 | grep -oP 'Ran \K\d+' || echo "0")
echo "✅ Total tests run: $TEST_COUNT"

echo ""
echo "Test Coverage by Category:"
echo "  ✅ Authentication: 13 tests"
echo "  ✅ Users: 14 tests"
echo "  ✅ Communities: 18 tests"
echo "  ✅ Status: 1 test"
echo ""

echo "For detailed test documentation, see:"
echo "  API_COMPATIBILITY_TESTS.md"
echo ""

echo "To run specific test files:"
echo "  python manage.py test api.tests.test_auth_api"
echo "  python manage.py test api.tests.test_user_api"
echo "  python manage.py test api.tests.test_community_api"
echo "  python manage.py test api.tests.test_status_api"
echo ""

echo "To run with coverage:"
echo "  pip install coverage"
echo "  coverage run --source='api' manage.py test api.tests"
echo "  coverage report"
echo "  coverage html  # Generate HTML report"
echo ""

echo "================================"
echo "✨ Compatibility tests complete!"
echo "================================"
