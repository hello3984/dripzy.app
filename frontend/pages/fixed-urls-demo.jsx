import React, { useState, useEffect } from 'react';
import ThemeCollageGrid from '../components/ThemeCollageGrid';
import CollageLayout from '../components/CollageLayout';
import Link from 'next/link';

const FixedUrlsDemo = () => {
  const [activeTab, setActiveTab] = useState('grid');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Simulating data fetch from API
    const fetchData = async () => {
      try {
        // Sample items with accurate product data and proper structure
        const sampleItems = [
          {
            product_name: "Wool Blend Blazer",
            category: "Outerwear",
            brand: "Zara",
            price: 169.00,
            image_url: "https://www.pngarts.com/files/11/Blazer-for-Men-Transparent-Image.png",
            url: "https://www.zara.com/us/en/textured-wool-blend-blazer-p09621300.html",
            productId: "9621300"
          },
          {
            product_name: "Slim Fit Jeans",
            category: "Bottoms",
            brand: "Levis",
            price: 89.50,
            image_url: "https://www.pngall.com/wp-content/uploads/5/Blue-Denim-Jeans-PNG-Image.png",
            url: "https://www.levi.com/US/en_US/apparel/clothing/bottoms/511-slim-fit-mens-jeans/p/045111994",
            productId: "045111994"
          },
          {
            product_name: "Leather Loafers",
            category: "Shoes",
            brand: "Cole Haan",
            price: 150.00,
            image_url: "https://www.freepnglogos.com/uploads/shoes-png/dress-shoes-png-transparent-dress-shoes-images-5.png",
            url: "https://www.colehaan.com/mens-dress-shoes",
            productId: ""
          },
          {
            product_name: "Silver Watch",
            category: "Accessories",
            brand: "MVMT",
            price: 128.00,
            image_url: "https://www.pngall.com/wp-content/uploads/2016/04/Watch-PNG-File.png",
            url: "https://www.mvmt.com/mens-watches/classic",
            productId: ""
          }
        ];
        
        setItems(sampleItems);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching data:", error);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  if (loading) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Loading...</div>;
  }
  
  return (
    <div className="fixed-urls-demo">
      <div className="header">
        <h1>Fixed URLs Demo</h1>
        <p>Compare different layout options with proper product URLs</p>
        
        <div className="tabs">
          <button 
            className={`tab-button ${activeTab === 'grid' ? 'active' : ''}`}
            onClick={() => setActiveTab('grid')}
          >
            Grid Layout
          </button>
          <button 
            className={`tab-button ${activeTab === 'collage' ? 'active' : ''}`}
            onClick={() => setActiveTab('collage')}
          >
            Collage Layout
          </button>
        </div>
      </div>
      
      <div className="content">
        {activeTab === 'grid' ? (
          <ThemeCollageGrid 
            title="Grid Layout with Fixed URLs" 
            items={items}
          />
        ) : (
          <CollageLayout 
            title="Collage Layout with Fixed URLs" 
            items={items}
          />
        )}
      </div>
      
      <div className="actions">
        <Link href="/url-test">
          <a className="action-button">Open URL Testing Tool</a>
        </Link>
        
        <Link href="/collage-demo">
          <a className="action-link">View Original Collage</a>
        </Link>
        
        <Link href="/grid-collage">
          <a className="action-link">View Original Grid</a>
        </Link>
      </div>
      
      <div className="info-box">
        <h2>URL Improvements</h2>
        <p>
          This demo showcases our improved URL handling system that ensures all product links redirect properly.
          The key improvements include:
        </p>
        <ul>
          <li>Consistent URL structure for all retailers</li>
          <li>Proper cleaning of search terms for search-based URLs</li>
          <li>Preferential selection of direct product URLs when available</li>
          <li>Support for product IDs to ensure accurate linking</li>
          <li>Brand-aware retailer selection for optimal user experience</li>
        </ul>
        <p>
          <strong>Click on any product</strong> to see how the links properly redirect to the appropriate retailer website.
        </p>
      </div>
      
      <style jsx>{`
        .fixed-urls-demo {
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .header {
          text-align: center;
          margin-bottom: 2rem;
        }
        
        .header h1 {
          margin-bottom: 0.5rem;
          color: #333;
        }
        
        .header p {
          color: #666;
          margin-bottom: 1.5rem;
        }
        
        .tabs {
          display: flex;
          justify-content: center;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        
        .tab-button {
          background-color: #f0f0f0;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .tab-button.active {
          background-color: #4a56e2;
          color: white;
        }
        
        .content {
          margin-bottom: 3rem;
        }
        
        .actions {
          display: flex;
          justify-content: center;
          flex-wrap: wrap;
          gap: 1rem;
          margin-bottom: 3rem;
        }
        
        .action-button {
          background-color: #28a745;
          color: white;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          text-decoration: none;
          font-weight: 500;
          transition: background-color 0.2s ease;
        }
        
        .action-button:hover {
          background-color: #218838;
        }
        
        .action-link {
          color: #4a56e2;
          text-decoration: underline;
          padding: 0.75rem 1rem;
        }
        
        .info-box {
          background-color: white;
          padding: 2rem;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .info-box h2 {
          margin-top: 0;
          margin-bottom: 1rem;
          color: #333;
        }
        
        .info-box p {
          color: #555;
          line-height: 1.5;
          margin-bottom: 1rem;
        }
        
        .info-box ul {
          margin-bottom: 1.5rem;
          padding-left: 1.5rem;
        }
        
        .info-box li {
          margin-bottom: 0.5rem;
          color: #555;
          line-height: 1.5;
        }
      `}</style>
    </div>
  );
};

export default FixedUrlsDemo; 