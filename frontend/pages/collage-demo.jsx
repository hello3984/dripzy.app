import React, { useState, useEffect } from 'react';
import CollageLayout from '../components/CollageLayout';

const CollageDemo = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Simulating data fetch from API
    const fetchData = async () => {
      try {
        // Sample items with transparent background product images
        const sampleItems = [
          {
            product_name: "Plaid Blazer",
            category: "Outerwear",
            brand: "Zara",
            price: 129.99,
            image_url: "https://www.pngarts.com/files/11/Blazer-for-Men-Transparent-Image.png",
            url: "https://www.zara.com/us/en/plaid-blazer-p09621458.html"
          },
          {
            product_name: "Slim Fit Jeans",
            category: "Bottoms",
            brand: "Levis",
            price: 89.50,
            image_url: "https://www.pngall.com/wp-content/uploads/5/Blue-Denim-Jeans-PNG-Image.png",
            url: "https://www.levi.com/US/en_US/apparel/clothing/bottoms/511-slim-fit-mens-jeans/p/045111994"
          },
          {
            product_name: "Leather Loafers",
            category: "Shoes",
            brand: "Cole Haan",
            price: 150.00,
            image_url: "https://www.freepnglogos.com/uploads/shoes-png/dress-shoes-png-transparent-dress-shoes-images-5.png",
            url: "https://www.colehaan.com/mens-dress-shoes"
          },
          {
            product_name: "Silver Watch",
            category: "Accessories",
            brand: "MVMT",
            price: 128.00,
            image_url: "https://www.pngall.com/wp-content/uploads/2016/04/Watch-PNG-File.png",
            url: "https://www.mvmt.com/mens-watches/classic"
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
    <div>
      <CollageLayout 
        title="Date Night Outfit Collage" 
        items={items}
      />
      
      <div style={{ textAlign: 'center', padding: '1rem', margin: '2rem auto', maxWidth: '800px' }}>
        <h2>About This Collage Layout</h2>
        <p>
          This collage layout uses absolute positioning to create a visually appealing outfit presentation.
          Each item is positioned precisely with different sizes to create a layered effect.
          Items use transparent background PNG images for the best visual presentation.
        </p>
        <p>
          <strong>Key Features:</strong>
        </p>
        <ul style={{ textAlign: 'left', display: 'inline-block' }}>
          <li>Absolute positioning for precise item placement</li>
          <li>Hover animations with scaling effect</li>
          <li>Different z-index values for layering items</li>
          <li>Responsive design that adapts to mobile devices</li>
          <li>Direct links to product pages</li>
        </ul>
        <p>
          <a href="/grid-collage" style={{ color: '#0066cc', textDecoration: 'underline' }}>
            View Grid Layout Version
          </a>
        </p>
      </div>
    </div>
  );
};

export default CollageDemo; 