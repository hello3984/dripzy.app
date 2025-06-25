import React, { useState, useEffect } from 'react';
import ThemeCollageGrid from '../components/ThemeCollageGrid';

const GridCollagePage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Simulating data fetch from API
    const fetchData = async () => {
      try {
        // Sample items with better image aspect ratios and consistent sizes
        const sampleItems = [
          {
            product_name: "Denim Jacket",
            brand: "Levi's",
            price: 89.99,
            image_url: "https://i.imgur.com/KpU8rfL.jpg",
            url: "https://www.farfetch.com/shopping/women/levis-denim-jacket-item-16124851.aspx"
          },
          {
            product_name: "Floral Print Dress",
            brand: "Zara",
            price: 49.99,
            image_url: "https://i.imgur.com/9jxaWbJ.jpg",
            url: "https://www.zara.com/us/en/floral-print-dress-p07969047.html"
          },
          {
            product_name: "Pleated Skirt",
            brand: "H&M",
            price: 29.99,
            image_url: "https://i.imgur.com/DvYCEoJ.jpg",
            url: "https://www2.hm.com/en_us/productpage.0969564001.html"
          },
          {
            product_name: "White Tank Top",
            brand: "Gap",
            price: 19.99,
            image_url: "https://i.imgur.com/QtWXSVs.jpg",
            url: "https://www.gap.com/browse/product.do?pid=5438830020000"
          },
          {
            product_name: "High-waisted Jeans",
            brand: "Madewell",
            price: 128.00,
            image_url: "https://i.imgur.com/KkgUK1u.jpg",
            url: "https://www.madewell.com/perfect-vintage-jean-in-claybrook-wash-AE188.html"
          },
          {
            product_name: "Straw Hat",
            brand: "Brixton",
            price: 55.00,
            image_url: "https://i.imgur.com/vdP1SQn.jpg",
            url: "https://www.brixton.com/collections/womens-straw-hats"
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
      <ThemeCollageGrid 
        title="Summer Style Collection" 
        items={items}
      />
      
      <div style={{ textAlign: 'center', padding: '1rem', margin: '2rem auto', maxWidth: '800px' }}>
        <h2>About This Grid Layout</h2>
        <p>
          This grid layout uses consistent proportions for all items with a fixed aspect ratio.
          Each item is clickable and opens the product page directly.
          The hover effect lifts the item and adds shadow for better interaction.
        </p>
        <p>
          <strong>Key Features:</strong>
        </p>
        <ul style={{ textAlign: 'left', display: 'inline-block' }}>
          <li>Responsive grid that works on all screen sizes</li>
          <li>Consistent image proportions (3:4 aspect ratio)</li>
          <li>Favorite button for each item</li>
          <li>Direct links to product pages</li>
          <li>Clean, modern design with subtle shadows</li>
        </ul>
      </div>
    </div>
  );
};

export default GridCollagePage; 