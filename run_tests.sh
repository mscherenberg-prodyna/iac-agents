#!/bin/bash

# CI Pipeline Test Script for IAC Agents
# Runs comprehensive tests with coverage reporting

set -e # Exit on any error

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

# Check minimum coverage threshold (70%)
# Extract coverage from XML report since coverage data was consumed by pytest
if [ -f "coverage/coverage.xml" ]; then
    COVERAGE=$(python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage/coverage.xml')
    root = tree.getroot()
    line_rate = float(root.get('line-rate', 0))
    print(int(line_rate * 100))
except:
    print(0)
" 2>/dev/null)
else
    COVERAGE=0
fi
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
