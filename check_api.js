#!/usr/bin/env node
/**
 * Script to test the API connection from the frontend to the backend
 */

const API_URL = 'http://localhost:8004';

async function testConnection() {
  console.log('Testing connection to backend API...');
  try {
    // Test root endpoint
    const rootResponse = await fetch(`${API_URL}/`);
    const rootData = await rootResponse.json();
    console.log('Root endpoint response:', rootData);
    
    // Test trending endpoint
    console.log('\nTesting trending endpoint...');
    const trendingResponse = await fetch(`${API_URL}/outfits/trending`);
    const trendingData = await trendingResponse.json();
    console.log('Trending endpoint response:', trendingData);
    
    // Test generate-test endpoint
    console.log('\nTesting generate-test endpoint...');
    const generateTestResponse = await fetch(`${API_URL}/outfits/generate-test`);
    if (generateTestResponse.ok) {
      console.log('Generate-test endpoint status:', generateTestResponse.status, generateTestResponse.statusText);
      console.log('Generate-test endpoint is working (response too large to display)');
    } else {
      console.error('Generate-test endpoint failed:', generateTestResponse.status, generateTestResponse.statusText);
    }
    
    // Test OPTIONS request
    console.log('\nTesting OPTIONS request to /outfits/generate...');
    const optionsResponse = await fetch(`${API_URL}/outfits/generate`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3006'
      }
    });
    console.log('OPTIONS response status:', optionsResponse.status, optionsResponse.statusText);
    
    // Test POST request with minimal data
    console.log('\nTesting POST request to /outfits/generate...');
    try {
      const postResponse = await fetch(`${API_URL}/outfits/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': 'http://localhost:3006'
        },
        body: JSON.stringify({
          prompt: 'Simple casual outfit',
          gender: 'male',
          budget: 200,
          style_keywords: ['casual']
        })
      });
      
      console.log('POST response status:', postResponse.status, postResponse.statusText);
      if (postResponse.ok) {
        console.log('POST request succeeded! API connection is working correctly.');
      } else {
        console.error('POST request failed, but received a response.');
        try {
          const errorData = await postResponse.json();
          console.error('Error details:', errorData);
        } catch (e) {
          console.error('Could not parse error response');
        }
      }
    } catch (error) {
      console.error('POST request failed with an exception:', error.message);
    }
    
    console.log('\nAPI connection test complete.');
  } catch (error) {
    console.error('Connection test failed:', error.message);
  }
}

testConnection(); 