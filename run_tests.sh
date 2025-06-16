#!/bin/bash

# CI Pipeline Test Script for IAC Agents
# Runs comprehensive tests with coverage reporting

set -e  # Exit on any error

echo "🚀 Starting CI Pipeline Tests for IAC Agents"
echo "============================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Install dependencies if needed
echo "📋 Checking dependencies..."
poetry install --no-interaction

# Create coverage directory
mkdir -p coverage

echo ""
echo "🧪 Running Test Suite..."
echo "========================"

# Run tests with coverage for active modules (excluding legacy)
python -m pytest \
    --cov=src.iac_agents \
    --cov-report=html:coverage/html \
    --cov-report=term-missing \
    --cov-report=xml:coverage/coverage.xml \
    --cov-config=.coveragerc \
    --junit-xml=coverage/junit.xml \
    -v \
    tests/

echo ""
echo "📊 Test Results Summary"
echo "======================"

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests PASSED"
else
    echo "❌ Some tests FAILED"
    exit 1
fi

# Display coverage summary
echo ""
echo "📈 Coverage Report:"
echo "=================="
python -m coverage report --show-missing --skip-covered

# Check minimum coverage threshold (70%)
COVERAGE=$(python -m coverage report --format=total 2>/dev/null || echo "0")
MIN_COVERAGE=70

echo ""
echo "🎯 Coverage Analysis:"
echo "===================="
echo "Current Coverage: ${COVERAGE}%"
echo "Minimum Required: ${MIN_COVERAGE}%"

if [ "${COVERAGE}" -ge "${MIN_COVERAGE}" ]; then
    echo "✅ Coverage threshold MET (${COVERAGE}% >= ${MIN_COVERAGE}%)"
else
    echo "⚠️  Coverage threshold NOT MET (${COVERAGE}% < ${MIN_COVERAGE}%)"
    echo "   Consider adding more tests for better coverage"
fi

echo ""
echo "📁 Generated Reports:"
echo "===================="
echo "HTML Coverage Report: coverage/html/index.html"
echo "XML Coverage Report:  coverage/coverage.xml"
echo "JUnit Test Report:    coverage/junit.xml"

echo ""
echo "🎉 CI Pipeline Tests Completed Successfully!"
echo "============================================"