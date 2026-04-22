# Talkify

Talkify is a mobile web application that transforms photographed objects into interactive AI characters with unique personalities and voices. Using advanced AI technologies, Talkify brings any object to life for engaging conversations and musical performances.

## Features

- **Photo Analysis**: Identify objects using Google Gemini Vision API
- **AI Personalities**: Generate unique character profiles with names, traits, and backstories
- **Voice Synthesis**: Create custom voices using ElevenLabs Voice Design API
- **Real-time Conversations**: Natural voice interactions through ElevenLabs Conversational AI
- **Musical Performances**: Generate and perform songs using ElevenLabs Music API
- **Ambient Audio**: Contextual sound effects for immersive experiences

## Technology Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+) with WebSocket support
- **AI Services**: ElevenLabs APIs (Voice Design, TTS v3, Conversational AI, Sound Effects, Music)
- **Vision API**: Google Gemini Vision for object identification
- **Deployment**: Render platform

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- ElevenLabs API key
- Google Gemini API key

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd talkify
   ```

2. **Set up the backend**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your API keys
   pip install -r requirements.txt
   python main.py
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   cp .env.example .env
   # Edit .env with your API URL
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Deployment

The application is configured for deployment on Render using the included `render.yaml` configuration.

1. **Fork this repository**
2. **Connect to Render**
   - Create a new Render account
   - Connect your GitHub repository
3. **Set environment variables**
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
   - `GEMINI_API_KEY`: Your Google Gemini API key
4. **Deploy**
   - Render will automatically deploy both frontend and backend services

## API Documentation

The backend provides the following endpoints:

- `GET /health` - Health check
- `POST /api/identify` - Object identification from photos
- `POST /api/profile` - Generate object personality and voice
- `POST /api/speak` - Text-to-speech conversion
- `POST /api/sing` - Song generation
- `POST /api/ambient` - Ambient sound effects
- `WebSocket /ws/conversation` - Real-time voice conversation

## Project Structure

```
talkify/
├── frontend/          # React/TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── .kiro/            # Kiro configuration
│   ├── specs/        # Project specifications
│   ├── steering/     # Workflow guides
│   └── hooks/        # Automation hooks
├── render.yaml       # Deployment configuration
├── LICENSE           # MIT License
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support, please open an issue in the GitHub repository.