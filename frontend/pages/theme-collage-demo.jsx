import React from 'react';
import ThemeCollage from '../components/ThemeCollage';
import { createCollageLayout, getThemeBackgroundColor } from '../utils/collageHelper';

const ThemeCollageDemo = () => {
  // Sample outfit items with realistic product data
  const outfitItems = [
    {
      category: 'Top',
      product_name: 'Cotton Oxford Shirt',
      brand: 'Hugo Boss',
      price: 129.99,
      image_url: 'https://cdn.imgbin.com/11/9/2/imgbin-dress-shirt-t-shirt-sleeve-clothing-dress-shirt-tWERmf5sNsRBWmKRPkX4YzqmH.jpg',
      url: 'https://www.farfetch.com/shopping/men/hugo-boss-logo-applique-cotton-shirt-item-19072931.aspx'
    },
    {
      category: 'Bottom',
      product_name: 'Slim-Fit Jeans',
      brand: 'Levis',
      price: 89.50,
      image_url: 'https://www.pngall.com/wp-content/uploads/5/Blue-Denim-Jeans-PNG-Image.png',
      url: 'https://www.nordstrom.com/s/levis-slim-fit-jeans/5023163'
    },
    {
      category: 'Outerwear',
      product_name: 'Wool Blend Blazer',
      brand: 'Zara',
      price: 169.00,
      image_url: 'https://www.pngarts.com/files/11/Blazer-for-Men-Transparent-Image.png',
      url: 'https://www.zara.com/us/en/textured-wool-blend-blazer-p09621300.html'
    },
    {
      category: 'Shoes',
      product_name: 'Leather Loafers',
      brand: 'Cole Haan',
      price: 150.00,
      image_url: 'https://www.freepnglogos.com/uploads/shoes-png/dress-shoes-png-transparent-dress-shoes-images-5.png',
      url: 'https://www.colehaan.com/mens-dress-shoes'
    },
    {
      category: 'Accessory',
      product_name: 'Leather Belt',
      brand: 'Calvin Klein',
      price: 45.00,
      image_url: 'https://www.pngall.com/wp-content/uploads/2016/04/Belt-PNG-HD.png',
      url: 'https://www.nordstrom.com/s/calvin-klein-leather-belt/5445954'
    },
    {
      category: 'Accessory',
      product_name: 'Silver-Tone Watch',
      brand: 'Mvmt',
      price: 128.00,
      image_url: 'https://www.pngall.com/wp-content/uploads/2016/04/Watch-PNG-File.png',
      url: 'https://www.mvmt.com/mens-watches/classic'
    }
  ];

  // Use our helper to create collage layout
  const collageItems = createCollageLayout(outfitItems);
  
  // Calculate total price
  const totalPrice = outfitItems.reduce((sum, item) => sum + (item.price || 0), 0);
  
  // Determine background color based on theme
  const themeColor = getThemeBackgroundColor('date night');

  return (
    <div>
      <ThemeCollage 
        title="Date Night King 👑" 
        items={collageItems}
        style={{ 
          backgroundColor: themeColor 
        }}
      />
      
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <h2>How to implement this collage layout:</h2>
        <ol style={{ lineHeight: 1.6, fontSize: '16px' }}>
          <li>Create the <code>ThemeCollage</code> component with absolute positioning for items</li>
          <li>Define the positions for each item type (top, bottom, accessories, etc.)</li>
          <li>Handle clicking on items to go to product URLs</li>
          <li>Style the collage with hover effects and animations</li>
          <li>Add product details and links in the description area</li>
        </ol>
        
        <p>
          <strong>Total items:</strong> {outfitItems.length} |
          <strong> Total price:</strong> ${totalPrice.toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export default ThemeCollageDemo; 