# Dripzy - AI Fashion Styling App

Dripzy is an AI-powered fashion styling application that generates outfit recommendations based on user preferences, budget, and style. 

## Features

- AI-generated outfit recommendations
- Budget-based styling (Luxury, Premium, Mid-range, Budget)
- Trending style exploration
- Gender-specific styling
- Outfit category filtering
- Brand-aware recommendations

## Project Structure

This project consists of two main parts:

1. **Frontend**: React application
2. **Backend**: FastAPI Python application

## Setup and Installation

### Prerequisites

- Node.js (v14 or higher)
- Python 3.8+ 
- npm or yarn

### Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## API Endpoints

- `/outfits/trending` - Get trending styles
- `/outfits/generate` - Generate outfit recommendations
- `/products` - Get product information

## Technologies Used

- **Frontend**: React, CSS3, JavaScript
- **Backend**: Python, FastAPI, Uvicorn
- **Data**: Mock data with planned integration to real fashion APIs

## Development Roadmap

- [x] Basic AI outfit recommendation system
- [x] Budget-aware styling
- [x] Brand diversity
- [x] User interface implementation
- [ ] Real-time fashion API integration
- [ ] User profiles and saved outfits
- [ ] Mobile responsive design improvements

## Deployment

This application will be deployed at [dripzy.app](https://dripzy.app).

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

Project Link: [https://github.com/yourusername/dripzy-app](https://github.com/yourusername/dripzy-app) 