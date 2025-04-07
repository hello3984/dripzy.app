import React, { useState, useEffect, useRef } from 'react';
import { getTrendingStyles, generateOutfit } from '../services/api';
import { getAffiliateUrl } from '../services/amazon';
import TrendingStylesDisplay from './TrendingStylesDisplay';
import './HomePage.css';

const HomePage = () => {
  const [trendingStyles, setTrendingStyles] = useState({});
  const [loading, setLoading] = useState(true);
  const [prompt, setPrompt] = useState('');
  const [budget, setBudget] = useState('');
  const [selectedGender, setSelectedGender] = useState('women');
  const [selectedStyle, setSelectedStyle] = useState('');
  const [showResults, setShowResults] = useState(false); // For demo purposes
  const [generating, setGenerating] = useState(false); // Animation state
  const [apiOutfits, setApiOutfits] = useState([]); // Add state for real API outfits
  const [error, setError] = useState(null); // Add state for error handling
  const [outfits, setOutfits] = useState([]);
  const [loadingImages, setLoadingImages] = useState({});
  const [budgetTier, setBudgetTier] = useState(null);

  // New state for tracking active category tab
  const [activeCategory, setActiveCategory] = useState('all');

  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const fileInputRef = useRef(null);

  // Budget tier options
  const budgetTiers = [
    { name: 'Luxury', min: 1000, description: 'Premium designer brands' },
    { name: 'Premium', min: 400, max: 999, description: 'High-quality fashion' },
    { name: 'Mid-range', min: 150, max: 399, description: 'Quality everyday pieces' },
    { name: 'Budget', max: 149, description: 'Affordable style picks' }
  ];

  useEffect(() => {
    // Fetch trending styles when component mounts
    const fetchTrendingStyles = async () => {
      try {
        setLoading(true);
        const data = await getTrendingStyles();
        console.log('Trending styles data:', data);
        setTrendingStyles(data.styles || {});
      } catch (error) {
        console.error('Failed to fetch trending styles:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrendingStyles();
  }, []);

  const handleGenerateOutfit = async () => {
    if (!prompt.trim()) {
      setError('Please enter a style description');
      return;
    }
    
    setError(null);
    setGenerating(true);
    setShowResults(false);
    setApiOutfits([]);
    
    // Prepare request parameters
    const requestParams = {
      prompt: prompt,
      gender: selectedGender,
      budget: budget ? parseFloat(budget) : null,
      style_keywords: selectedStyle ? [selectedStyle] : []
    };
    
    console.log('Generating outfit with params:', requestParams);
    
    try {
      const result = await generateOutfit(requestParams);
      
      if (result && result.outfits && result.outfits.length > 0) {
        setApiOutfits(result.outfits);
        setShowResults(true);
        
        // Scroll to results section after a short delay
        setTimeout(() => {
          const resultsSection = document.querySelector('.outfit-results');
          if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
          }
        }, 200);
      } else {
        console.warn('No outfits returned from API');
        setApiOutfits([]);
        setShowResults(true); // Still show the section with mock data
      }
    } catch (error) {
      console.error('Error generating outfit:', error);
      setError(`Failed to generate outfit: ${error.message || 'Unknown error'}`);
      // Still show results with mock data
      setApiOutfits([]);
      setShowResults(true);
    } finally {
      setGenerating(false);
    }
  };

  const handleStyleClick = (style) => {
    console.log('Style clicked:', style);
    setSelectedStyle(style);
    
    // Auto-generation for specific styles with appropriate prompts
    const stylePrompts = {
      'Classic': 'Create a timeless classic outfit for everyday wear',
      'Coastal': 'Create a beach-inspired coastal outfit with light colors',
      'Goth': 'Create a dark gothic outfit with black elements',
      'Chic': 'Create an elegant and sophisticated chic outfit',
      'Preppy': 'Create a polished preppy outfit with classic elements',
      'Rustic': 'Create a rustic bohemian outfit with earthy tones',
      'Androgynous': 'Create a gender-neutral outfit with modern styling',
      'Romantic': 'Create a soft and feminine romantic outfit',
      'Coachella': 'Create a festival outfit for Coachella with bohemian vibes',
      'Festival': 'Create a trendy music festival outfit',
      'Business': 'Create a professional office outfit',
      'Casual': 'Create a comfortable everyday casual outfit',
      'Evening': 'Create an elegant evening outfit',
      'Streetwear': 'Create a trendy urban streetwear outfit'
    };
    
    // Set appropriate prompt based on selected style
    if (stylePrompts[style]) {
      setPrompt(stylePrompts[style]);
      
      // Scroll to the top of the style generation section
      const generatorSection = document.querySelector('.style-prompt-container');
      if (generatorSection) {
        generatorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  // Create flattened array of style keywords for easy display
  const flattenedStyles = [];
  console.log('Trending styles in state:', trendingStyles);
  
  // Make sure Coachella is included in the flattened styles
  const coachella = "Coachella";
  let hasCoachella = false;
  
  if (trendingStyles && typeof trendingStyles === 'object') {
    Object.entries(trendingStyles).forEach(([category, styles]) => {
      if (Array.isArray(styles)) {
        styles.forEach(style => {
          flattenedStyles.push(style);
          if (style === coachella) {
            hasCoachella = true;
          }
        });
      }
    });
  }
  
  // Add Coachella if it's not already in the list
  if (!hasCoachella) {
    flattenedStyles.push(coachella);
  }
  
  console.log('Flattened styles:', flattenedStyles);

  // Create enhanced Coachella-specific outfit data with guaranteed working images
  const coachellaOutfits = [
    {
      id: 'coachella1',
      name: 'Boho Festival Look',
      description: 'Perfect for Coachella with bohemian vibes',
      style: 'festival',
      total_price: 189.97,
      items: [
        {
          product_id: 'p1',
          product_name: 'Crochet Crop Top',
          brand: 'Free People',
          category: 'tops',
          price: 68.00,
          image_url: 'https://images.unsplash.com/photo-1523381294911-8d3cead13475?q=80&w=2070&auto=format&fit=crop',
          description: 'Handcrafted crochet crop top with fringe details',
          source: 'Free People'
        },
        {
          product_id: 'p2',
          product_name: 'High-Waisted Denim Shorts',
          brand: 'Levi\'s',
          category: 'bottoms',
          price: 58.00,
          image_url: 'https://images.unsplash.com/photo-1582418702059-97ebafb35d09?q=80&w=1915&auto=format&fit=crop',
          description: 'Vintage-inspired denim shorts with distressed details',
          source: 'Levi\'s'
        },
        {
          product_id: 'p3',
          product_name: 'Suede Ankle Boots',
          brand: 'Steve Madden',
          category: 'shoes',
          price: 79.97,
          image_url: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop',
          description: 'Western-inspired ankle boots with fringe detail',
          source: 'Steve Madden'
        }
      ]
    },
    {
      id: 'coachella2',
      name: 'Desert Festival Chic',
      description: 'Stylish and comfortable for long days in the sun',
      style: 'festival',
      total_price: 213.95,
      items: [
        {
          product_id: 'p4',
          product_name: 'Flowy Boho Dress',
          brand: 'Anthropologie',
          category: 'dresses',
          price: 128.00,
          image_url: 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?q=80&w=1746&auto=format&fit=crop',
          description: 'Lightweight midi dress with bohemian print',
          source: 'Anthropologie'
        },
        {
          product_id: 'p5',
          product_name: 'Fringe Crossbody Bag',
          brand: 'Urban Outfitters',
          category: 'accessories',
          price: 48.00,
          image_url: 'https://images.unsplash.com/photo-1591348278863-a8fb3887e2aa?q=80&w=1974&auto=format&fit=crop',
          description: 'Suede crossbody bag with fringe detail',
          source: 'Urban Outfitters'
        },
        {
          product_id: 'p6',
          product_name: 'Layered Necklace Set',
          brand: 'Madewell',
          category: 'jewelry',
          price: 37.95,
          image_url: 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop',
          description: 'Gold-toned layered necklace set with coin pendants',
          source: 'Madewell'
        }
      ]
    },
    {
      id: 'coachella3',
      name: 'Festival Boho Chic',
      description: 'Effortlessly cool festival-ready outfit',
      style: 'festival',
      total_price: 176.00,
      items: [
        {
          product_id: 'c1',
          product_name: 'Floral Maxi Dress',
          brand: 'Zara',
          category: 'dresses',
          price: 89.00,
          image_url: 'https://images.unsplash.com/photo-1508424897381-4fd8755e4b7a?q=80&w=1935&auto=format&fit=crop',
          description: 'Flowing floral maxi dress perfect for hot festival days',
          source: 'Zara'
        },
        {
          product_id: 'c2',
          product_name: 'Straw Hat',
          brand: 'H&M',
          category: 'accessories',
          price: 29.00,
          image_url: 'https://images.unsplash.com/photo-1530926467933-1450bd6d2338?q=80&w=1974&auto=format&fit=crop',
          description: 'Wide-brimmed straw hat for sun protection',
          source: 'H&M'
        },
        {
          product_id: 'c3',
          product_name: 'Gladiator Sandals',
          brand: 'Forever 21',
          category: 'shoes',
          price: 58.00,
          image_url: 'https://images.unsplash.com/photo-1473226064865-5cacec176076?q=80&w=1976&auto=format&fit=crop',
          description: 'Lace-up gladiator sandals with studded details',
          source: 'Forever 21'
        }
      ]
    }
  ];

  // Special Coachella styles added directly
  const coachellaStyles = [
    "Coachella",
    "Festival Style", 
    "Bohemian", 
    "Western Chic",
    "Y2K Revival"
  ];
  
  // Add Coachella styles if not in flattenedStyles
  coachellaStyles.forEach(style => {
    if (!flattenedStyles.includes(style)) {
      flattenedStyles.push(style);
    }
  });

  // Function to get the appropriate outfits - either from API, Coachella outfits, or general mock outfits
  const getDisplayOutfits = () => {
    // Use API outfits if available
    if (apiOutfits && apiOutfits.length > 0) {
      return apiOutfits;
    }
    
    // Use Coachella outfits if selected style is Coachella or prompt contains Coachella
    if (selectedStyle === 'Coachella' || prompt.toLowerCase().includes('coachella')) {
      return coachellaOutfits;
    }
    
    // Otherwise use general mock outfits
    return mockOutfits;
  };

  // Mock outfit results for demo purposes - update with reliable images
  const mockOutfits = [
    {
      id: 'outfit1',
      name: 'Boho Festival Look',
      description: 'Perfect for Coachella with bohemian vibes',
      style: 'festival',
      total_price: 189.97,
      items: [
        {
          product_id: 'p1',
          product_name: 'Crochet Crop Top',
          brand: 'Free People',
          category: 'tops',
          price: 68.00,
          image_url: 'https://images.unsplash.com/photo-1523381294911-8d3cead13475?q=80&w=2070&auto=format&fit=crop',
          description: 'Handcrafted crochet crop top with fringe details',
          source: 'Free People'
        },
        {
          product_id: 'p2',
          product_name: 'High-Waisted Denim Shorts',
          brand: 'Levi\'s',
          category: 'bottoms',
          price: 58.00,
          image_url: 'https://images.unsplash.com/photo-1582418702059-97ebafb35d09?q=80&w=1915&auto=format&fit=crop',
          description: 'Vintage-inspired denim shorts with distressed details',
          source: 'Levi\'s'
        },
        {
          product_id: 'p3',
          product_name: 'Suede Ankle Boots',
          brand: 'Steve Madden',
          category: 'shoes',
          price: 79.97,
          image_url: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop',
          description: 'Western-inspired ankle boots with fringe detail',
          source: 'Steve Madden'
        }
      ]
    },
    {
      id: 'outfit2',
      name: 'Desert Festival Chic',
      description: 'Stylish and comfortable for long days in the sun',
      style: 'festival',
      total_price: 213.95,
      items: [
        {
          product_id: 'p4',
          product_name: 'Flowy Boho Dress',
          brand: 'Anthropologie',
          category: 'dresses',
          price: 128.00,
          image_url: 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?q=80&w=1746&auto=format&fit=crop',
          description: 'Lightweight midi dress with bohemian print',
          source: 'Anthropologie'
        },
        {
          product_id: 'p5',
          product_name: 'Fringe Crossbody Bag',
          brand: 'Urban Outfitters',
          category: 'accessories',
          price: 48.00,
          image_url: 'https://images.unsplash.com/photo-1591348278863-a8fb3887e2aa?q=80&w=1974&auto=format&fit=crop',
          description: 'Suede crossbody bag with fringe detail',
          source: 'Urban Outfitters'
        },
        {
          product_id: 'p6',
          product_name: 'Layered Necklace Set',
          brand: 'Madewell',
          category: 'jewelry',
          price: 37.95,
          image_url: 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop',
          description: 'Gold-toned layered necklace set with coin pendants',
          source: 'Madewell'
        }
      ]
    }
  ];

  // Function to handle image loading errors with reliable fallbacks
  const handleImageError = (e, category) => {
    const fallbackImages = {
      'tops': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=300',
      'bottoms': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=300',
      'dresses': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=300',
      'shoes': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=300',
      'accessories': 'https://images.unsplash.com/photo-1589128777073-53d2615c9821?w=300',
      'outerwear': 'https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=300',
      'default': 'https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=300'
    };
    
    // Set the src to the appropriate fallback image based on category
    e.target.src = fallbackImages[category.toLowerCase()] || fallbackImages.default;
    e.target.classList.add('fallback-image');
  };

  // Handle budget tier selection
  const handleBudgetTierSelect = (tier) => {
    setBudgetTier(tier);
    if (tier.min && tier.max) {
      setBudget(tier.max); // Set to max of the range
    } else if (tier.min) {
      setBudget(tier.min); // For luxury, set to minimum
    } else if (tier.max) {
      setBudget(tier.max); // For budget, set to maximum
    }
  };

  // Force show the Coachella outfits if the user clicked Coachella
  useEffect(() => {
    if (selectedStyle === 'Coachella') {
      setShowResults(true);
      setApiOutfits([]);
    }
  }, [selectedStyle]);

  // The categories we want to display in our filter tabs
  const categories = ['all', 'tops', 'bottoms', 'dresses', 'shoes', 'accessories', 'outerwear'];

  // Filter items by category for the filter tabs
  const getItemsByCategory = (category) => {
    const displayOutfits = getDisplayOutfits();
    
    if (category === 'all') {
      return displayOutfits.flatMap(outfit => outfit.items);
    }
    
    return displayOutfits.flatMap(outfit => 
      outfit.items.filter(item => 
        item.category.toLowerCase() === category.toLowerCase()
      )
    );
  };

  // Add this in the render function where outfit items are displayed
  const renderOutfitItem = (item) => {
    const affiliateUrl = getAffiliateUrl(item.url, item.source);
    
    return (
      <div className="outfit-item" key={item.id}>
        <div className="outfit-item-image">
          <img src={item.image_url || 'https://via.placeholder.com/300x400'} alt={item.name} />
        </div>
        <div className="outfit-item-details">
          <h4>{item.name}</h4>
          <p className="brand">{item.brand}</p>
          <p className="price">${item.price.toFixed(2)}</p>
          <a 
            href={affiliateUrl} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="view-item-btn"
          >
            Shop Now
          </a>
        </div>
      </div>
    );
  };

  const handlePhotoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedPhoto(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="homepage">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">Showcase</h1>
          <p className="hero-subtitle">
            Generate personalized outfits in seconds using AI-driven fashion intelligence.
          </p>
          <div className="hero-cta">
            <button 
              className="try-for-free"
              onClick={() => {
                const generatorSection = document.querySelector('.style-generator');
                if (generatorSection) {
                  generatorSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              Try for Free
            </button>
          </div>
        </div>
      </section>
      
      {/* Showcase Image Gallery */}
      <section className="showcase-gallery">
        <div className="section-header">
          <h2>Fashion Inspiration</h2>
          <p>Dripzy's AI algorithms generate on-trend fashion concepts—perfect for any style, any event.</p>
        </div>
        <div className="gallery-grid">
          <div className="gallery-item">
            <img src="https://images.unsplash.com/photo-1509631179647-0177331693ae?q=80&w=1976&auto=format&fit=crop" alt="Fashion model in burgundy suit" />
          </div>
          <div className="gallery-item">
            <img src="https://images.unsplash.com/photo-1581044777550-4cfa60707c03?q=80&w=1972&auto=format&fit=crop" alt="Fashion model in pink outfit" />
          </div>
          <div className="gallery-item">
            <img src="https://images.unsplash.com/photo-1551803091-e20673f15770?q=80&w=1975&auto=format&fit=crop" alt="Fashion model in red outfit" />
          </div>
          <div className="gallery-item">
            <img src="https://images.unsplash.com/photo-1550614000-4895a10e1bfd?q=80&w=1974&auto=format&fit=crop" alt="Male fashion model in coat" />
          </div>
          <div className="gallery-item">
            <img src="https://images.unsplash.com/photo-1618522285348-559a4f369c3e?q=80&w=1972&auto=format&fit=crop" alt="Fashion model closeup" />
          </div>
        </div>
      </section>
      
      {/* Budget Tier Selection */}
      <section className="budget-tiers">
        <h2>Shop By Budget</h2>
        <div className="tier-selector">
          {budgetTiers.map((tier) => (
            <div 
              key={tier.name}
              className={`tier-card ${budgetTier?.name === tier.name ? 'active' : ''}`}
              onClick={() => handleBudgetTierSelect(tier)}
            >
              <h3>{tier.name}</h3>
              <p className="price-range">
                {tier.min && tier.max 
                  ? `$${tier.min} - $${tier.max}`
                  : tier.min 
                    ? `$${tier.min}+` 
                    : `Up to $${tier.max}`
                }
              </p>
              <p className="tier-desc">{tier.description}</p>
            </div>
          ))}
        </div>
      </section>
      
      {/* Style Generator Section - simplified to focus on generation */}
      <section className="style-generator" id="generate">
        <div className="container">
          <div className="ai-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <path d="M12 7v10"></path>
              <path d="M8 15l4 4 4-4"></path>
            </svg>
            Powered by AI
          </div>
          <h2 className="section-title">Generate Your Outfit</h2>
          
          <div className="style-prompt-container">
            <div className="prompt-input-wrapper">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what you want to generate..."
                className="prompt-input"
              />
              <button 
                className="close-button"
                onClick={() => setPrompt('')}
              >×</button>
            </div>
            
            <div className="suggestion-chips">
              <div 
                className="suggestion-chip"
                onClick={() => setPrompt('Gardening gifts for a retiree with a green thumb')}
                data-tooltip="Use this suggestion"
              >
                <span>Gardening gifts for a retiree with a green thumb</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="7" y1="17" x2="17" y2="7"></line>
                  <polyline points="7 7 17 7 17 17"></polyline>
                </svg>
              </div>
              <div 
                className="suggestion-chip"
                onClick={() => setPrompt('Birthday outfits for women')}
                data-tooltip="Use this suggestion"
              >
                <span>Birthday outfits for women</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="7" y1="17" x2="17" y2="7"></line>
                  <polyline points="7 7 17 7 17 17"></polyline>
                </svg>
              </div>
            </div>
            
            <div className="action-buttons">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handlePhotoUpload}
                accept="image/*"
                style={{ display: 'none' }}
              />
              <button 
                className="photo-upload-button"
                onClick={() => fileInputRef.current.click()}
                data-tooltip="Upload your photo for personalized styling"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                Use a photo
              </button>
              <button 
                className="generate-button"
                onClick={handleGenerateOutfit}
                disabled={generating}
                data-tooltip="Generate AI fashion outfits"
              >
                {generating ? (
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                    Generating
                  </div>
                ) : 'Generate'}
              </button>
            </div>
            
            {selectedPhoto && (
              <div className="photo-preview">
                <div className="photo-preview-wrapper">
                  <img src={selectedPhoto} alt="User uploaded" />
                  <button 
                    className="remove-photo"
                    onClick={() => setSelectedPhoto(null)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="15" y1="9" x2="9" y2="15"></line>
                      <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                  </button>
                </div>
                <p className="photo-note">We'll generate outfits that would look great on you</p>
              </div>
            )}
          </div>
          
          <div className="style-categories">
            <h3>Choose a style</h3>
            <div className="style-grid">
              <div 
                className={`style-tile ${selectedStyle === 'Classic' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Classic')}
                data-tooltip="Timeless and elegant classic style"
              >
                <div className="style-image classic-style"></div>
                <span className="style-name">Classic</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Coastal' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Coastal')}
                data-tooltip="Beach-inspired relaxed coastal look"
              >
                <div className="style-image coastal-style"></div>
                <span className="style-name">Coastal</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Goth' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Goth')}
                data-tooltip="Dark and edgy gothic fashion"
              >
                <div className="style-image goth-style"></div>
                <span className="style-name">Goth</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Chic' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Chic')}
                data-tooltip="Sophisticated and trendy chic looks"
              >
                <div className="style-image chic-style"></div>
                <span className="style-name">Chic</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Preppy' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Preppy')}
                data-tooltip="Clean and polished preppy outfits"
              >
                <div className="style-image preppy-style"></div>
                <span className="style-name">Preppy</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Rustic' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Rustic')}
                data-tooltip="Natural and earthy rustic style"
              >
                <div className="style-image rustic-style"></div>
                <span className="style-name">Rustic</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Androgynous' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Androgynous')}
                data-tooltip="Gender-neutral modern styling"
              >
                <div className="style-image androgynous-style"></div>
                <span className="style-name">Androgynous</span>
              </div>
              <div 
                className={`style-tile ${selectedStyle === 'Romantic' ? 'active' : ''}`}
                onClick={() => handleStyleClick('Romantic')}
                data-tooltip="Soft and feminine romantic fashion"
              >
                <div className="style-image romantic-style"></div>
                <span className="style-name">Romantic</span>
              </div>
            </div>
          </div>
          
          <div className="gender-preference">
            <div className="radio-group">
              <label 
                className={selectedGender === 'women' ? 'active' : ''}
                data-tooltip="Show women's fashion styles"
              >
                <input
                  type="radio"
                  name="gender"
                  value="women"
                  checked={selectedGender === 'women'}
                  onChange={(e) => setSelectedGender(e.target.value)}
                />
                Women
              </label>
              <label 
                className={selectedGender === 'men' ? 'active' : ''}
                data-tooltip="Show men's fashion styles"
              >
                <input
                  type="radio"
                  name="gender"
                  value="men"
                  checked={selectedGender === 'men'}
                  onChange={(e) => setSelectedGender(e.target.value)}
                />
                Men
              </label>
              <label 
                className={selectedGender === 'unisex' ? 'active' : ''}
                data-tooltip="Show gender-neutral fashion styles"
              >
                <input
                  type="radio"
                  name="gender"
                  value="unisex"
                  checked={selectedGender === 'unisex'}
                  onChange={(e) => setSelectedGender(e.target.value)}
                />
                Unisex
              </label>
            </div>
          </div>
        </div>
      </section>
      
      {/* Results Section - this is where we display the generated outfits */}
      {showResults && (
        <section className="outfit-results">
          <h2>Your Curated Outfits</h2>
          
          {error && (
            <div className="error-message">{error}</div>
          )}
          
          {/* Category Filters */}
          <div className="category-filters">
            {categories.map((category) => (
              <button
                key={category}
                className={`category-filter ${activeCategory === category ? 'active' : ''}`}
                onClick={() => setActiveCategory(category)}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
          
          {getDisplayOutfits().map((outfit) => (
            <div key={outfit.id} className="outfit-result">
              <div className="outfit-header">
                <div className="outfit-title">
                  <h3>{outfit.name}</h3>
                  <span className="outfit-price">${outfit.total_price.toFixed(2)}</span>
                </div>
                <p className="outfit-description">{outfit.description}</p>
                <div className="outfit-style">
                  <span className="style-badge" data-style={outfit.style}>{outfit.style}</span>
                </div>
              </div>
              
              {/* Stylist Notes Card */}
              <div className="stylist-card">
                <div className="trend-badge classic">CLASSIC</div>
                <h4>Stylist Notes</h4>
                <ul className="stylist-notes">
                  <li>This {outfit.style.toLowerCase()} outfit features classic pieces</li>
                  <li>Perfect for {outfit.style.toLowerCase()} season</li>
                </ul>
                
                <h4>Styling Tips</h4>
                <p className="styling-tip">
                  Prioritize self-expression while considering practicality for outdoor conditions.
                </p>
              </div>
              
              {/* Items Display */}
              <div className="outfit-items">
                {outfit.items
                  .filter(item => activeCategory === 'all' || item.category.toLowerCase() === activeCategory)
                  .map((item) => renderOutfitItem(item))}
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
};

export default HomePage; 