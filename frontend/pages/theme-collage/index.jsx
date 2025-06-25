import React from 'react';
import Link from 'next/link';

const ThemeCollageIndex = () => {
  // Sample theme categories
  const themeCategories = [
    {
      title: 'Occasions',
      themes: [
        { name: 'Date Night', slug: 'date-night-king' },
        { name: 'Office Meeting', slug: 'office-formal' },
        { name: 'Weekend Casual', slug: 'casual-weekend' },
        { name: 'Beach Vacation', slug: 'beach-vacation' },
      ]
    },
    {
      title: 'Seasons',
      themes: [
        { name: 'Summer Style', slug: 'summer-style' },
        { name: 'Winter Wardrobe', slug: 'winter-wardrobe' },
        { name: 'Fall Fashion', slug: 'fall-fashion' },
        { name: 'Spring Look', slug: 'spring-look' },
      ]
    },
    {
      title: 'Styles',
      themes: [
        { name: 'Minimalist', slug: 'minimalist-style' },
        { name: 'Streetwear', slug: 'streetwear-style' },
        { name: 'Bohemian', slug: 'bohemian-style' },
        { name: 'Business Casual', slug: 'business-casual' },
      ]
    }
  ];

  return (
    <div className="theme-collage-index">
      <div className="container">
        <h1 className="page-title">Theme Collages</h1>
        <p className="page-description">
          Explore outfit collages for different occasions, seasons, and styles. 
          Click on any theme to view a perfectly curated outfit with direct links to shop each item.
        </p>
        
        <div className="categories">
          {themeCategories.map((category, index) => (
            <div key={index} className="category">
              <h2 className="category-title">{category.title}</h2>
              <div className="theme-grid">
                {category.themes.map((theme, themeIndex) => (
                  <Link href={`/theme-collage/${theme.slug}`} key={themeIndex}>
                    <a className="theme-card">
                      <div className="card-content">
                        <h3 className="theme-name">{theme.name}</h3>
                        <div className="arrow">→</div>
                      </div>
                    </a>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="featured-theme">
          <h2 className="featured-title">Featured Theme</h2>
          <Link href="/theme-collage/date-night-king">
            <a className="featured-card">
              <div className="featured-content">
                <h3 className="featured-name">Date Night King 👑</h3>
                <p className="featured-description">
                  A perfect outfit for a romantic evening, featuring a stylish blazer, crisp shirt, and premium accessories.
                </p>
                <div className="featured-button">View Outfit</div>
              </div>
            </a>
          </Link>
        </div>
      </div>

      <style jsx>{`
        .theme-collage-index {
          background-color: #f9f9f9;
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
          min-height: 100vh;
          padding: 40px 0;
        }
        
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 20px;
        }
        
        .page-title {
          font-size: 2.5rem;
          font-weight: 700;
          margin-bottom: 1rem;
          color: #333;
          text-align: center;
        }
        
        .page-description {
          text-align: center;
          color: #666;
          max-width: 800px;
          margin: 0 auto 3rem;
          line-height: 1.6;
          font-size: 1.1rem;
        }
        
        .categories {
          display: grid;
          gap: 3rem;
          margin-bottom: 3rem;
        }
        
        .category-title {
          font-size: 1.8rem;
          margin-bottom: 1.5rem;
          color: #444;
          border-bottom: 2px solid #eee;
          padding-bottom: 0.5rem;
        }
        
        .theme-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 20px;
        }
        
        .theme-card {
          background-color: white;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
          overflow: hidden;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          display: block;
          text-decoration: none;
          height: 100%;
        }
        
        .theme-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        .card-content {
          padding: 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .theme-name {
          color: #333;
          font-size: 1.3rem;
          margin: 0;
        }
        
        .arrow {
          font-size: 1.5rem;
          color: #0066cc;
        }
        
        .featured-theme {
          margin-top: 4rem;
        }
        
        .featured-title {
          font-size: 1.8rem;
          margin-bottom: 1.5rem;
          color: #444;
          text-align: center;
        }
        
        .featured-card {
          display: block;
          text-decoration: none;
          background-color: white;
          border-radius: 10px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          margin: 0 auto;
          max-width: 800px;
        }
        
        .featured-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }
        
        .featured-content {
          padding: 30px;
          text-align: center;
        }
        
        .featured-name {
          color: #333;
          font-size: 1.8rem;
          margin: 0 0 1rem;
        }
        
        .featured-description {
          color: #666;
          line-height: 1.6;
          margin-bottom: 1.5rem;
          font-size: 1.1rem;
        }
        
        .featured-button {
          display: inline-block;
          background-color: #0066cc;
          color: white;
          font-weight: 500;
          padding: 10px 20px;
          border-radius: 30px;
          text-decoration: none;
          transition: background-color 0.2s ease;
        }
        
        .featured-button:hover {
          background-color: #0055aa;
        }
        
        @media (max-width: 768px) {
          .theme-grid {
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          }
          
          .page-title {
            font-size: 2rem;
          }
          
          .page-description {
            font-size: 1rem;
          }
        }
        
        @media (max-width: 480px) {
          .theme-grid {
            grid-template-columns: 1fr;
          }
          
          .featured-content {
            padding: 20px;
          }
          
          .featured-name {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default ThemeCollageIndex; 