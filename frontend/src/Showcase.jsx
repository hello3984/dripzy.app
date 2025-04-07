import React from 'react';
import { Link } from 'react-router-dom';

const FeatureCard = ({ image, title, description }) => {
  return (
    <div className="card">
      <img src={image} alt={title} />
      <div className="card-content">
        <h3 className="card-title">{title}</h3>
        <p className="card-description">{description}</p>
      </div>
    </div>
  );
};

const Showcase = () => {
  // Sample feature data - replace with your actual data
  const features = [
    {
      id: 1,
      image: '/images/feature1.jpg',
      title: 'Smart Recommendations',
      description: 'AI-powered style suggestions based on your preferences.'
    },
    {
      id: 2,
      image: '/images/feature2.jpg',
      title: 'Trendy Collections',
      description: 'Stay updated with the latest fashion trends and styles.'
    },
    {
      id: 3,
      image: '/images/feature3.jpg',
      title: 'Personal Stylist',
      description: 'Your AI fashion assistant to create perfect outfits.'
    }
  ];

  return (
    <main className="main-container">
      <h1>Showcase</h1>
      <p>
        Dripzy users can leverage advanced algorithms to generate innovative fashion
        concepts, pushing the boundaries of creativity and efficiency in the design process.
      </p>
      <Link to="/signup" className="button secondary-button">Try for Free</Link>

      <div className="card-container">
        {features.map(feature => (
          <FeatureCard 
            key={feature.id}
            image={feature.image}
            title={feature.title}
            description={feature.description}
          />
        ))}
      </div>
    </main>
  );
};

export default Showcase; 