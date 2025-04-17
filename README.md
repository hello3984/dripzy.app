# Fashion AI - Style Explorer

A modern AI-powered fashion recommendation app that helps users discover personalized outfit suggestions based on their style preferences, moods, and occasions.

![Fashion AI App Screenshot](https://images.unsplash.com/photo-1537832816519-689ad163238b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&h=600&q=80)

## Features

- **Style Mood Selection**: Choose from various style moods like Festival, Bohemian, Edgy, Vintage, and more
- **AI-Powered Recommendations**: Get personalized outfit suggestions tailored to your selected mood
- **Complete Outfit Curation**: View full outfits with matching tops, bottoms, footwear, and accessories
- **Product Details**: See images, descriptions, and pricing for each recommended item
- **Responsive Design**: Enjoy a seamless experience across desktop and mobile devices

## Tech Stack

### Frontend
- React.js
- Next.js
- Framer Motion (for animations)
- CSS-in-JS (styled-jsx)

### Backend
- FastAPI (Python)
- Claude AI (for outfit recommendations)
- SerpAPI (for product search)
- Pydantic (for data validation)

## Getting Started

### Prerequisites
- Node.js 14+
- Python 3.8+
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/fashion-ai.git
cd fashion-ai
```

2. Install frontend dependencies
```bash
cd frontend
npm install
```

3. Install backend dependencies
```bash
cd ../backend
pip install -r requirements.txt
```

4. Set up environment variables
```bash
# Create .env file in the backend directory
cp .env.example .env
# Add your API keys and configuration
```

5. Start the development servers
```bash
# In the frontend directory
npm run dev

# In the backend directory
uvicorn app.main:app --reload
```

6. Open your browser and navigate to `http://localhost:3000`

## Usage

1. Browse the Style Explorer page
2. Select a mood that matches your style preference
3. View the recommended outfits based on your selection
4. Save outfits you like or view detailed information about specific items
5. Explore different moods to discover various style options

## Project Structure

```
fashion-ai/
├── frontend/
│   ├── components/
│   │   ├── MoodSelector.jsx       # Style mood selection component
│   │   └── ...
│   ├── pages/
│   │   ├── StyleExplorer.jsx      # Main style exploration page
│   │   └── ...
│   └── ...
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py          # Application configuration
│   │   ├── models/
│   │   │   └── outfit_models.py   # Data models for outfits
│   │   ├── routers/
│   │   │   ├── outfits.py         # Outfit recommendation endpoints
│   │   │   └── products.py        # Product search endpoints
│   │   ├── services/
│   │   │   ├── serpapi_service.py # Product search service
│   │   │   └── ...
│   │   └── main.py                # FastAPI application entry point
│   └── requirements.txt           # Python dependencies
└── README.md                      # Project documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Unsplash for providing high-quality fashion images
- Claude AI for powering the intelligent outfit recommendations
- The open-source community for the amazing tools and libraries 