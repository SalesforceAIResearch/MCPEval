# MCPEval Frontend - MCP Evaluation Framework Web UI

A modern, intuitive web interface for the MCP (Model Context Protocol) evaluation framework. This React-based application provides easy access to all CLI commands through a beautiful, user-friendly interface.

## Features

### 🎯 Task Management
- **Generate Tasks**: Create evaluation tasks for MCP servers with AI models
- **Verify Tasks**: Validate generated tasks against MCP servers
- Support for multi-server configurations
- Real-time progress tracking and logging

### 🔄 Data Processing
- **Convert Data**: Transform task data to different formats (XLAM, etc.)
- **Split Data**: Create train/test/validation splits with custom ratios
- Stratified splitting and reproducible random seeds

### 📊 Model Evaluation
- **Multi-Model Evaluation**: Compare multiple models simultaneously
- **Comprehensive Configuration**: Fine-tune model parameters
- **Real-time Monitoring**: Track evaluation progress with detailed logs

### 🔍 Analysis & Reporting
- **Performance Analysis**: Compare results against ground truth
- **LLM Judging**: AI-powered evaluation of task execution
- **Visual Dashboards**: Intuitive metrics and reporting

## Technology Stack

- **Frontend**: React 18 + TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **Routing**: React Router v6
- **State Management**: React Hooks
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Code Highlighting**: React Syntax Highlighter

## Prerequisites

- Node.js 16+ and npm/yarn
- Python 3.8+ (for backend)
- MCP evaluation framework installed

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Backend API

```bash
# From the project root
cd backend
pip install flask flask-cors
python app.py
```

The backend will run on `http://localhost:22358`

### 3. Start the Frontend

```bash
cd frontend
npm start
```

The frontend will run on `http://localhost:22359`

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Header.tsx    # Navigation header
│   │   └── Sidebar.tsx   # Navigation sidebar
│   ├── pages/            # Main application pages
│   │   ├── Dashboard.tsx      # Overview dashboard
│   │   ├── TaskGenerator.tsx  # Task generation
│   │   ├── TaskVerifier.tsx   # Task verification
│   │   ├── ModelEvaluator.tsx # Model evaluation
│   │   ├── DataConverter.tsx  # Data conversion
│   │   ├── DataSplitter.tsx   # Data splitting
│   │   ├── Analyzer.tsx       # Results analysis
│   │   ├── LLMJudger.tsx      # LLM judging
│   │   └── Results.tsx        # Results viewer
│   ├── App.tsx           # Main application component
│   ├── index.tsx         # Application entry point
│   └── index.css         # Global styles
├── package.json          # Dependencies and scripts
└── README.md            # This file
```

## Usage Guide

### 1. Dashboard
- Overview of recent activities and system status
- Quick actions for common tasks
- System metrics and performance indicators

### 2. Task Generation
- Configure MCP servers (single or multiple)
- Set generation parameters (model, temperature, etc.)
- Monitor real-time progress
- Download generated tasks

### 3. Task Verification
- Validate tasks against MCP servers
- Track pass/fail rates
- Review detailed logs
- Export verified tasks

### 4. Model Evaluation
- Compare multiple models simultaneously
- Configure evaluation parameters
- Monitor progress across models
- Download comprehensive results

### 5. Data Processing
- Convert between different data formats
- Split datasets with custom ratios
- Maintain reproducible configurations

### 6. Analysis & Reporting
- Compare results against ground truth
- Generate performance metrics
- AI-powered evaluation insights
- Export detailed reports

## Configuration

### Environment Variables

Create `.env.local` for local development:

```bash
REACT_APP_API_URL=http://localhost:22358
```

### Backend Configuration

The backend API runs on port 22358 by default. Configure in `backend/app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=22358)
```

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Code Style

This project uses:
- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Material-UI design system

### Adding New Features

1. Create new components in `src/components/`
2. Add new pages in `src/pages/`
3. Update routing in `src/App.tsx`
4. Add navigation items in `src/components/Sidebar.tsx`

## Deployment

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t mcpeval-frontend .
docker run -p 22359:80 mcpeval-frontend
```

## API Integration

The frontend communicates with the backend API at `/api/*` endpoints:

- `POST /api/generate-tasks` - Generate tasks
- `POST /api/verify-tasks` - Verify tasks
- `POST /api/evaluate` - Evaluate models
- `POST /api/convert-data` - Convert data
- `POST /api/split-data` - Split data
- `POST /api/analyze` - Analyze results
- `GET /api/files/:filename` - Download files

## Troubleshooting

### Common Issues

1. **API Connection Errors**: 
   - Ensure backend is running on port 22358
   - Check CORS configuration
   - Verify API endpoints

2. **File Upload Issues**
   - Check file permissions
   - Verify upload directory exists
   - Ensure proper file formats

3. **CLI Command Failures**
   - Verify MCP framework installation
   - Check Python path configuration
   - Review command arguments

### Debugging

Enable debug mode in development:

```bash
REACT_APP_DEBUG=true npm start
```

Check browser console for detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review existing issues and discussions 