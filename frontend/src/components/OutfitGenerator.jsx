import React, { useState } from 'react';
import './OutfitGenerator.css';

const OutfitGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [generatedOutfit, setGeneratedOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePromptChange = (e) => {
    setPrompt(e.target.value);
  };

  const generateOutfit = async () => {
    if (!prompt.trim()) {
      setError('Please enter a style description');
      return;
    }

    setLoading(true);
    setError(null);
    
    console.log("Sending request to backend with prompt:", prompt);

    try {
      // Use the direct Render URL and add credentials
      const response = await fetch('https://dripzy-app.onrender.com/outfits/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ prompt }),
        mode: 'cors',
      });

      console.log("Response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("API error:", errorText);
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log("API response data:", data);
      setGeneratedOutfit(data.outfits[0]); // Use the first outfit from the array
    } catch (err) {
      console.error('Failed to generate outfit:', err);
      setError(`Failed to generate outfit: ${err.message}`);
      
      // For demo purposes, create mock data if API fails
      setGeneratedOutfit({
        items: [
          {
            category: 'Top',
            type: 'Crochet crop top',
            brand: 'Free People',
            image_url: 'https://images.unsplash.com/photo-1562157873-818bc0726f68?w=800&auto=format',
            product_url: 'https://www.freepeople.com',
            price: 68.00
          },
          {
            category: 'Bottom',
            type: 'High-waisted denim shorts',
            brand: 'Levi\'s',
            image_url: 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&auto=format',
            product_url: 'https://www.levi.com',
            price: 58.00
          },
          {
            category: 'Shoes',
            type: 'Western ankle boots',
            brand: 'Steve Madden',
            image_url: 'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=800&auto=format',
            product_url: 'https://www.stevemadden.com',
            price: 89.95
          },
          {
            category: 'Accessory',
            type: 'Layered necklace',
            brand: 'Madewell',
            image_url: 'https://images.unsplash.com/photo-1583292650898-7298fa6cf342?w=800&auto=format',
            product_url: 'https://www.madewell.com',
            price: 48.00
          },
          {
            category: 'Bag',
            type: 'Fringe crossbody bag',
            brand: 'Urban Outfitters',
            image_url: 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800&auto=format',
            product_url: 'https://www.urbanoutfitters.com',
            price: 59.00
          }
        ],
        prompt
      });
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalPrice = (items) => {
    return items.reduce((total, item) => total + (item.price || 0), 0).toFixed(2);
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      generateOutfit();
    }
  };

  return (
    <div className="outfit-generator">
      <div className="update-banner">
        🔥 NEW DESIGN DEPLOYED - APRIL 2024 🔥
      </div>
      <div className="generator-container">
        <h2>AI Fashion Stylist</h2>
        <p className="description">
          Describe your style goal or occasion and our AI will create a personalized outfit for you.
        </p>
        
        <div className="prompt-input">
          <input
            type="text"
            value={prompt}
            onChange={handlePromptChange}
            onKeyPress={handleKeyPress}
            placeholder="e.g., Coachella outfit, business casual, date night"
            className="prompt-field"
          />
          <button 
            onClick={generateOutfit} 
            disabled={loading}
            className="generate-button"
          >
            {loading ? 'Generating...' : 'Generate Outfit'}
          </button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        {generatedOutfit && (
          <div className="outfit-results">
            <h3>Your {prompt} Outfit</h3>
            
            <div className="total-price">
              Total Price: ${generatedOutfit.total_price ? generatedOutfit.total_price.toFixed(2) : calculateTotalPrice(generatedOutfit.items)}
            </div>
            
            <div className="outfit-items">
              {generatedOutfit.items.map((item, index) => (
                <div key={index} className="outfit-item">
                  <div className="item-image">
                    {item.image_url ? (
                      <img src={item.image_url} alt={item.product_name || item.type} />
                    ) : (
                      <div className="placeholder-image">
                        {item.category} Image
                      </div>
                    )}
                  </div>
                  <div className="item-details">
                    <h4>{item.product_name || item.type}</h4>
                    <p className="brand">{item.brand}</p>
                    <p className="category">{item.category}</p>
                    {item.price && <p className="price">${item.price.toFixed(2)}</p>}
                    {(item.url || item.product_url) && (
                      <a 
                        href={item.url || item.product_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="shop-link"
                      >
                        Shop Now
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutfitGenerator; 