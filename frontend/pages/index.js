import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import OutfitDisplay from '../components/OutfitDisplay';
import MoodSelector from '../components/MoodSelector';
import LoadingIndicator from '../components/LoadingIndicator';

export default function Home() {
  const [mood, setMood] = useState('');
  const [outfits, setOutfits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleMoodSelect = async (selectedMood) => {
    try {
      setMood(selectedMood);
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/outfits?mood=${selectedMood}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch outfits');
      }
      
      const data = await response.json();
      setOutfits(Array.isArray(data) ? data : [data]);
    } catch (err) {
      console.error('Error fetching outfits:', err);
      setError('Failed to load outfits. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <Head>
        <title>Fashion AI - Style Explorer</title>
        <meta name="description" content="AI-powered fashion recommendations" />
        <link rel="icon" href="/favicon.ico" />
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet" />
      </Head>

      <main>
        <header>
          <h1>Fashion AI</h1>
          <p className="tagline">Curated outfits for your unique style</p>
          
          <div className="feature-links">
            <Link href="/theme-collage">
              <a className="feature-link">
                Create Theme Collages ✨
              </a>
            </Link>
          </div>
        </header>

        <MoodSelector 
          selectedMood={mood} 
          onMoodSelect={handleMoodSelect} 
        />

        {loading ? (
          <LoadingIndicator message="Creating your personalized outfit..." />
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : outfits.length > 0 ? (
          <div className="outfits-container">
            {outfits.map((outfit, index) => (
              <OutfitDisplay key={outfit.id || index} outfit={outfit} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>Select a style mood to get outfit recommendations</p>
          </div>
        )}
      </main>

      <style jsx>{`
        .container {
          min-height: 100vh;
          padding: 0 1rem;
          background: linear-gradient(to bottom, #ffffff, #f9f7fe);
        }

        main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem 0;
        }

        header {
          text-align: center;
          margin-bottom: 2rem;
        }

        h1 {
          font-family: 'Playfair Display', serif;
          font-size: 3.5rem;
          font-weight: 600;
          margin: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .tagline {
          font-size: 1.2rem;
          color: #718096;
          margin: 0.5rem 0 0;
        }
        
        .feature-links {
          margin-top: 1.5rem;
          display: flex;
          justify-content: center;
        }
        
        .feature-link {
          display: inline-block;
          background-color: white;
          color: #6c4ed9;
          border: 2px solid #6c4ed9;
          padding: 0.6rem 1.5rem;
          border-radius: 30px;
          font-weight: 500;
          text-decoration: none;
          transition: all 0.3s ease;
          box-shadow: 0 2px 10px rgba(108, 78, 217, 0.1);
        }
        
        .feature-link:hover {
          background-color: #6c4ed9;
          color: white;
          transform: translateY(-2px);
          box-shadow: 0 4px 15px rgba(108, 78, 217, 0.2);
        }

        .outfits-container {
          margin-top: 2rem;
        }

        .empty-state {
          text-align: center;
          padding: 4rem 0;
          color: #718096;
          font-size: 1.1rem;
        }

        .error-message {
          margin: 2rem auto;
          padding: 1rem;
          background-color: #fed7d7;
          color: #9b2c2c;
          border-radius: 0.5rem;
          text-align: center;
          max-width: 500px;
        }

        @media (max-width: 768px) {
          h1 {
            font-size: 2.5rem;
          }
          
          .tagline {
            font-size: 1rem;
          }
        }
      `}</style>

      <style jsx global>{`
        * {
          box-sizing: border-box;
        }
        
        html,
        body {
          padding: 0;
          margin: 0;
          font-family: 'Poppins', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
            Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
        }
      `}</style>
    </div>
  );
} 