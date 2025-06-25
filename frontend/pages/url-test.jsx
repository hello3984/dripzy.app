import React from 'react';
import UrlTester from '../components/UrlTester';

const UrlTestPage = () => {
  return (
    <div className="container">
      <div className="header">
        <h1>URL Testing Suite</h1>
        <p>Test and validate product URLs for proper retailer linking</p>
      </div>
      
      <UrlTester />
      
      <div className="info-section">
        <h2>How It Works</h2>
        <p>
          This tool helps ensure that product links in your collages correctly redirect to the appropriate 
          retail product pages. It handles common issues like:
        </p>
        <ul>
          <li>Cleaning search queries by removing unwanted terms</li>
          <li>Creating optimized retailer-specific URLs</li>
          <li>Selecting the best retailer based on brand or product type</li>
          <li>Validating that URLs lead to actual product pages</li>
        </ul>
        
        <h2>Testing Workflow</h2>
        <ol>
          <li>Enter a product name and brand (required)</li>
          <li>Optionally add a direct URL or product ID if available</li>
          <li>Click "Generate URLs" to see the resulting URLs</li>
          <li>Click "Validate URLs" to check if the URLs are valid</li>
          <li>Use the "Test" links to manually check each URL in a new tab</li>
        </ol>
      </div>
      
      <style jsx>{`
        .container {
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
          max-width: 1000px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .header {
          text-align: center;
          margin-bottom: 3rem;
        }
        
        .header h1 {
          margin-bottom: 0.5rem;
          color: #333;
        }
        
        .header p {
          color: #666;
          font-size: 1.1rem;
        }
        
        .info-section {
          margin-top: 3rem;
          padding: 2rem;
          background-color: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .info-section h2 {
          margin-top: 0;
          margin-bottom: 1rem;
          color: #333;
        }
        
        .info-section p {
          color: #555;
          line-height: 1.5;
        }
        
        .info-section ul, .info-section ol {
          margin-bottom: 2rem;
          padding-left: 1.5rem;
        }
        
        .info-section li {
          margin-bottom: 0.5rem;
          line-height: 1.5;
          color: #555;
        }
      `}</style>
    </div>
  );
};

export default UrlTestPage; 