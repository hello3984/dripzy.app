import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ThemeCollage from '../../components/ThemeCollage';
import { createCollageLayout, getThemeBackgroundColor } from '../../utils/collageHelper';

const ThemeCollagePage = () => {
  const router = useRouter();
  const { theme } = router.query;
  const [outfitData, setOutfitData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Only fetch if we have a theme parameter
    if (!theme) return;
    
    const fetchOutfitData = async () => {
      try {
        setLoading(true);
        
        // You would normally fetch from your API here
        // For demo purposes, we'll simulate a response
        const simulatedApiResponse = {
          success: true,
          outfit: {
            name: `${theme.replace(/-/g, ' ')} Outfit`,
            items: [
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
            ],
            description: `A perfectly coordinated outfit for a ${theme.replace(/-/g, ' ')} occasion, featuring premium pieces that work together harmoniously.`,
            occasion: theme.replace(/-/g, ' ')
          }
        };
        
        // Simulate API call delay
        setTimeout(() => {
          if (simulatedApiResponse.success) {
            setOutfitData(simulatedApiResponse.outfit);
          } else {
            setError('Failed to fetch outfit data');
          }
          setLoading(false);
        }, 500);
        
        // In a real app, you would fetch from your API:
        // const response = await fetch(`/api/outfits/${theme}`);
        // const data = await response.json();
        // if (data.success) {
        //   setOutfitData(data.outfit);
        // } else {
        //   setError(data.error || 'Failed to fetch outfit data');
        // }
        // setLoading(false);
        
      } catch (err) {
        setError('An error occurred while fetching outfit data');
        setLoading(false);
        console.error(err);
      }
    };
    
    fetchOutfitData();
  }, [theme]);
  
  // Process the outfit data for the collage
  const getProcessedItems = () => {
    if (!outfitData || !outfitData.items) return [];
    return createCollageLayout(outfitData.items);
  };
  
  // Get background color based on theme
  const bgColor = getThemeBackgroundColor(theme);
  
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading {theme} outfit...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'red' }}>
        <div>{error}</div>
      </div>
    );
  }
  
  if (!outfitData) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>No outfit data found for theme: {theme}</div>
      </div>
    );
  }
  
  return (
    <div>
      <ThemeCollage 
        title={`${theme.replace(/-/g, ' ')} ${theme.toLowerCase().includes('king') ? '👑' : 'Outfit'}`}
        items={getProcessedItems()}
        style={{ backgroundColor: bgColor }}
      />
      
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <p>
          <a href={`/theme-collage/casual-weekend`} style={{ marginRight: '10px', color: '#0066cc' }}>
            Casual Weekend
          </a>
          <a href={`/theme-collage/office-formal`} style={{ marginRight: '10px', color: '#0066cc' }}>
            Office Formal
          </a>
          <a href={`/theme-collage/date-night-king`} style={{ color: '#0066cc' }}>
            Date Night King
          </a>
        </p>
      </div>
    </div>
  );
};

export default ThemeCollagePage; 