import React, { useState } from 'react';
import { cleanSearchQuery, getFarfetchUrl, getNordstromUrl, getBestRetailUrl } from '../utils/retailUrlHelper';

const UrlTester = () => {
  const [testProduct, setTestProduct] = useState({
    product_name: '',
    brand: '',
    url: '',
    productId: '',
    category: 'Clothing'
  });
  
  const [testResults, setTestResults] = useState({
    cleanedQuery: '',
    farfetchUrl: '',
    nordstromUrl: '',
    bestUrl: '',
    urlStatus: 'Not Tested'
  });
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setTestProduct(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const testUrls = () => {
    // Generate cleaned query
    const cleanedQuery = cleanSearchQuery(testProduct.brand, testProduct.product_name);
    
    // Generate URLs
    const farfetchUrl = getFarfetchUrl(testProduct);
    const nordstromUrl = getNordstromUrl(testProduct);
    const bestUrl = getBestRetailUrl(testProduct);
    
    // Update test results
    setTestResults({
      cleanedQuery,
      farfetchUrl,
      nordstromUrl,
      bestUrl,
      urlStatus: 'Generated'
    });
  };
  
  const testUrlValidity = async () => {
    try {
      setTestResults(prev => ({ ...prev, urlStatus: 'Testing...' }));
      
      // We can't directly test URLs due to CORS, but we could simulate this
      // In a real implementation, you'd use a backend endpoint to validate URLs
      
      // Simulate a delay and success for demo purposes
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setTestResults(prev => ({ ...prev, urlStatus: 'URLs Generated Successfully' }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        urlStatus: `Error: ${error.message}` 
      }));
    }
  };
  
  return (
    <div className="url-tester">
      <h2>Retail URL Tester</h2>
      <p>Test product URLs to ensure proper linking to retailer websites.</p>
      
      <div className="test-form">
        <div className="form-group">
          <label>Product Name:</label>
          <input 
            type="text"
            name="product_name"
            placeholder="e.g. Floral Ruffle Midi Dress"
            value={testProduct.product_name}
            onChange={handleInputChange}
          />
        </div>
        
        <div className="form-group">
          <label>Brand:</label>
          <input 
            type="text"
            name="brand"
            placeholder="e.g. Zara"
            value={testProduct.brand}
            onChange={handleInputChange}
          />
        </div>
        
        <div className="form-group">
          <label>Direct URL (optional):</label>
          <input 
            type="text"
            name="url"
            placeholder="https://www.example.com/product"
            value={testProduct.url}
            onChange={handleInputChange}
          />
        </div>
        
        <div className="form-group">
          <label>Product ID (optional):</label>
          <input 
            type="text"
            name="productId"
            placeholder="12345678"
            value={testProduct.productId}
            onChange={handleInputChange}
          />
        </div>
        
        <div className="form-actions">
          <button 
            onClick={testUrls} 
            disabled={!testProduct.product_name && !testProduct.brand}
            className="test-button"
          >
            Generate URLs
          </button>
          
          <button 
            onClick={testUrlValidity}
            disabled={testResults.urlStatus === 'Not Tested'}
            className="validate-button"
          >
            Validate URLs
          </button>
        </div>
      </div>
      
      {testResults.urlStatus !== 'Not Tested' && (
        <div className="test-results">
          <h3>Test Results</h3>
          
          <div className="result-item">
            <strong>Cleaned Search Query:</strong>
            <pre>{testResults.cleanedQuery}</pre>
          </div>
          
          <div className="result-item">
            <strong>Farfetch URL:</strong>
            <div className="url-result">
              <pre>{testResults.farfetchUrl}</pre>
              <a 
                href={testResults.farfetchUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="test-link"
              >
                Test
              </a>
            </div>
          </div>
          
          <div className="result-item">
            <strong>Nordstrom URL:</strong>
            <div className="url-result">
              <pre>{testResults.nordstromUrl}</pre>
              <a 
                href={testResults.nordstromUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="test-link"
              >
                Test
              </a>
            </div>
          </div>
          
          <div className="result-item">
            <strong>Best URL:</strong>
            <div className="url-result">
              <pre>{testResults.bestUrl}</pre>
              <a 
                href={testResults.bestUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="test-link"
              >
                Test
              </a>
            </div>
          </div>
          
          <div className="result-status">
            <strong>Status:</strong>
            <span className={`status-${testResults.urlStatus === 'URLs Generated Successfully' ? 'success' : 'pending'}`}>
              {testResults.urlStatus}
            </span>
          </div>
        </div>
      )}
      
      <style jsx>{`
        .url-tester {
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
          background-color: #f9f9f9;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        h2 {
          margin-top: 0;
          margin-bottom: 0.5rem;
          color: #333;
        }
        
        p {
          margin-bottom: 2rem;
          color: #666;
        }
        
        .test-form {
          display: grid;
          grid-gap: 1rem;
          margin-bottom: 2rem;
        }
        
        .form-group {
          display: flex;
          flex-direction: column;
        }
        
        label {
          font-weight: 500;
          margin-bottom: 0.5rem;
          color: #444;
        }
        
        input {
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
        }
        
        .form-actions {
          display: flex;
          gap: 1rem;
          margin-top: 1rem;
        }
        
        button {
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }
        
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .test-button {
          background-color: #4a56e2;
          color: white;
        }
        
        .test-button:hover:not(:disabled) {
          background-color: #3a46d2;
        }
        
        .validate-button {
          background-color: #28a745;
          color: white;
        }
        
        .validate-button:hover:not(:disabled) {
          background-color: #218838;
        }
        
        .test-results {
          background-color: white;
          padding: 1.5rem;
          border-radius: 4px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .result-item {
          margin-bottom: 1rem;
        }
        
        .url-result {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        pre {
          background-color: #f5f5f5;
          padding: 0.5rem;
          border-radius: 4px;
          overflow-x: auto;
          font-size: 0.9rem;
          margin: 0.5rem 0;
          flex: 1;
        }
        
        .test-link {
          background-color: #f0f0f0;
          padding: 0.4rem 0.8rem;
          border-radius: 4px;
          text-decoration: none;
          color: #333;
          font-size: 0.9rem;
          transition: background-color 0.2s ease;
        }
        
        .test-link:hover {
          background-color: #e0e0e0;
        }
        
        .result-status {
          margin-top: 1.5rem;
          padding-top: 1rem;
          border-top: 1px solid #eee;
        }
        
        .status-success {
          color: #28a745;
          font-weight: 500;
          margin-left: 0.5rem;
        }
        
        .status-pending {
          color: #ffc107;
          font-weight: 500;
          margin-left: 0.5rem;
        }
        
        @media (max-width: 600px) {
          .form-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default UrlTester; 