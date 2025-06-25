import React, { useState } from 'react';
import ThemeCollage from '../components/ThemeCollage';

const ThemeCollagePage = () => {
  const [theme, setTheme] = useState('');
  const [submittedTheme, setSubmittedTheme] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmittedTheme(theme);
  };
  
  // Example items that would come from an API in a real application
  const mockItems = [
    {
      id: 1,
      name: 'Navy Blazer',
      image: 'https://images.unsplash.com/photo-1594938291221-94f18cbb5660?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80',
      category: 'outerwear',
      retailUrl: 'https://www.farfetch.com/shopping/men/search/items.aspx?q=navy%20blazer',
      price: 249.99,
      position: { left: '73px', top: '50px', width: '453px', height: '600px', zIndex: 1 }
    },
    {
      id: 2,
      name: 'White Button-Down Shirt',
      image: 'https://images.unsplash.com/photo-1603252109303-2751441dd157?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80',
      category: 'top',
      retailUrl: 'https://www.farfetch.com/shopping/men/search/items.aspx?q=white%20button%20down%20shirt',
      price: 79.99,
      position: { left: '200px', top: '286px', width: '306px', height: '423px', zIndex: 2 }
    },
    {
      id: 3,
      name: 'Slim Fit Jeans',
      image: 'https://images.unsplash.com/photo-1542272604-787c3835535d?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80',
      category: 'bottom',
      retailUrl: 'https://www.nordstrom.com/s/mens-slim-fit-jeans',
      price: 119.99,
      position: { left: '530px', top: '400px', width: '400px', height: '500px', zIndex: 1 }
    },
    {
      id: 4,
      name: 'Leather Belt',
      image: 'https://images.unsplash.com/photo-1614621075981-6775bc4c2e6a?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80',
      category: 'accessory',
      retailUrl: 'https://www.nordstrom.com/s/mens-leather-belt',
      price: 59.99,
      position: { left: '336px', top: '153px', width: '116px', height: '48px', zIndex: 3 }
    },
    {
      id: 5,
      name: 'Stainless Steel Watch',
      image: 'https://images.unsplash.com/photo-1523170335258-f5ed11844a49?ixlib=rb-4.0.3&auto=format&fit=crop&w=700&q=80',
      category: 'accessory',
      retailUrl: 'https://www.nordstrom.com/s/mens-stainless-steel-watch',
      price: 349.99,
      position: { left: '750px', top: '250px', width: '150px', height: '200px', zIndex: 3 }
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ 
        maxWidth: '600px', 
        margin: '0 auto 40px', 
        textAlign: 'center' 
      }}>
        <h1 style={{ marginBottom: '20px' }}>Outfit Theme Generator</h1>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            placeholder="Enter a theme (e.g. 'date night', 'casual friday')"
            style={{ 
              flex: 1, 
              padding: '12px 15px',
              fontSize: '16px',
              borderRadius: '8px',
              border: '1px solid #ddd'
            }}
          />
          <button 
            type="submit"
            style={{
              backgroundColor: '#4a56e2',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '0 20px',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            Generate
          </button>
        </form>
      </div>

      {/* Display the theme collage with example items */}
      <ThemeCollage 
        theme={submittedTheme || 'Date Night Outfit'} 
        items={mockItems} 
      />
      
      <div style={{ 
        maxWidth: '800px', 
        margin: '40px auto', 
        textAlign: 'center',
        color: '#666',
        fontSize: '14px'
      }}>
        <p>Our AI-powered outfit generator creates personalized style collages based on your theme.</p>
        <p>Click on any item to shop directly at our partner retailers.</p>
      </div>
    </div>
  );
};

export default ThemeCollagePage; 