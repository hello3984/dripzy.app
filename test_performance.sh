#!/bin/bash

echo "🧪 Testing API performance monitoring..."

# Base URL for the API
API_URL="http://localhost:8000"

# Function to make API requests
make_request() {
  local url=$1
  local method=${2:-GET}
  local data=${3:-""}
  
  if [ "$method" = "GET" ]; then
    curl -s -X "$method" "$url" > /dev/null
  else
    curl -s -X "$method" -H "Content-Type: application/json" -d "$data" "$url" > /dev/null
  fi
  
  echo "Made $method request to $url"
}

# Generate some healthy requests
echo "📊 Making healthy API requests..."
for i in {1..5}; do
  make_request "$API_URL/health"
  sleep 0.5
done

# Generate outfits request (potentially slow)
echo "👕 Generating outfit request (potentially slow)..."
make_request "$API_URL/outfits/trending"

# Test health check endpoint
echo "🩺 Testing health check endpoint..."
make_request "$API_URL/health"

# Test monitoring endpoints
echo "📊 Testing monitoring endpoints..."
make_request "$API_URL/monitoring/metrics"
make_request "$API_URL/monitoring/status"
make_request "$API_URL/monitoring/endpoints"
make_request "$API_URL/monitoring/slow-requests"

# Generate a POST request
echo "📝 Making POST requests..."
outfit_request='{
  "prompt": "Casual weekend outfit",
  "gender": "male",
  "budget": 300,
  "occasion": "casual"
}'
make_request "$API_URL/outfits/generate" "POST" "$outfit_request"

# Test a non-existent endpoint to generate an error
echo "❌ Testing error response..."
make_request "$API_URL/non-existent-endpoint"

# Check performance data
echo "🔍 Checking performance data..."
echo "Status:"
curl -s "$API_URL/monitoring/status" | python -m json.tool

echo ""
echo "Endpoint Performance:"
curl -s "$API_URL/monitoring/endpoints" | python -m json.tool

echo ""
echo "✅ Performance test completed" 