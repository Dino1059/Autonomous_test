# Docker Setup for AI Agent Tester

This document explains how to run the AI Agent Tester project using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Make (optional, for using Makefile commands)

## Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# Build and run the application
make quick-start

# Or for development mode
make dev-start
```

### Option 2: Using Docker Compose directly

```bash
# Build the image
docker-compose build

# Run the application
docker-compose up -d

# View logs
docker-compose logs -f
```

## Available Services

The application consists of:

1. **FastAPI Backend** - Available at `http://localhost:8081`
2. **Gradio Frontend** - Available at `http://localhost:7860`

## Environment Variables

Create a `.env` file in the project root to configure the application:

```env
# API Keys
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_ENDPOINT=
AZURE_OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=

# Laminar API Configuration
LAMINAR_API_KEY=
LAMINAR_BASE_URL=
LAMINAR_HTTP_PORT=
LAMINAR_GRPC_PORT=

# Report Module
REPORT_FOLDER=./demo_reports

# Application Configuration
PORT=8081
HOST=0.0.0.0
```

## Running Modes

### Development Mode

Development mode includes:

- Source code mounting for live reloading
- Interactive shell access
- Debug environment variables

```bash
# Using Makefile
make run-dev

# Using Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

### Production Mode

Production mode includes:

- Optimized container setup
- Health checks

```bash
# Production mode
make run
# or
make run-prod
```

## Useful Commands

### Using Makefile

```bash
make help          # Show all available commands
make build         # Build the Docker image
make run           # Run in production mode
make run-dev       # Run in development mode
make stop          # Stop all containers
make clean         # Remove containers and images
make logs          # Show container logs
make shell         # Open shell in running container
make test          # Run tests
```

### Using Docker Compose directly

```bash
# Build and run
docker-compose up --build -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f autotester

# Execute commands in container
docker-compose exec autotester python app/main.py --help

# Access shell
docker-compose exec autotester /bin/bash
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: If ports 8081 or 7860 are already in use, modify the port mappings in `docker-compose.yml`

2. **Permission issues**: On Linux/macOS, you might need to run Docker commands with `sudo`

3. **Browser automation issues**: The container includes all necessary dependencies for Playwright browser automation

4. **Memory issues**: If you encounter memory issues, increase Docker's memory allocation in Docker Desktop settings

### Debugging

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs autotester

# Check container resources
docker stats

# Access container for debugging
docker-compose exec autotester /bin/bash
```

### Health Checks

The application includes health checks that monitor the FastAPI backend:

```bash
# Check health status
curl http://localhost:8081/health

# View health check logs
docker-compose logs autotester | grep health
```

## Volumes

The following volumes are mounted:

- `./demo_reports:/app/demo_reports` - Test reports and outputs
- `./logs:/app/logs` - Application logs
- `.:/app` - Source code (development mode only)

## Network

The application exposes:

- Port 8081: FastAPI backend
- Port 7860: Gradio frontend

## Security Considerations

1. **Environment Variables**: Never commit sensitive information like API keys to version control
2. **Port Exposure**: Only expose necessary ports
3. **User Permissions**: The container runs as root for browser automation compatibility
4. **Network Isolation**: Consider using Docker networks for production deployments

## Production Deployment

For production deployment:

1. Run the application:

   ```bash
   make run-prod
   ```

2. Configure proper environment variables
3. Set up proper logging and monitoring
4. Set up backup strategies for the `demo_reports` volume

## Customization

### Modifying the Dockerfile

The `Dockerfile` includes:

- Python 3.11 slim base image
- System dependencies for browser automation
- Playwright browser installation
- Multi-process startup script

### Modifying Docker Compose

The `docker-compose.yml` includes:

- Service definition with health checks
- Volume mounts for persistence
- Environment variable configuration

## Support

For issues related to:

- Docker setup: Check this documentation
- Application functionality: Refer to the main README.md
- Browser automation: Check Playwright documentation
