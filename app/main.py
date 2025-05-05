"""
FastAPI main application for AutoTester - Browser Automation Testing Tool
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router
from app.serializers.models import MessageResponse, DataResponse


# Create FastAPI app
app = FastAPI(title="AutoTester API", description="API for browser automation testing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the main router
app.include_router(router)

@app.get("/", response_model=DataResponse[MessageResponse])
async def root():
    """Root endpoint that returns a welcome message"""
    return DataResponse(data=MessageResponse(message="Welcome to AutoTester API"))

if __name__ == "__main__":
    # Get port from command line or environment variable, with a default fallback
    parser = argparse.ArgumentParser(description="AutoTester API")
    parser.add_argument("--port", type=int, default=os.environ.get("PORT", 8081), 
                        help="Port to run the FastAPI server on (default: 8081 or PORT env var)")
    parser.add_argument("--host", type=str, default=os.environ.get("HOST", "0.0.0.0"),
                        help="Host to bind the server to (default: 0.0.0.0 or HOST env var)")
    args = parser.parse_args()
    
    # Log the settings
    print(f"Starting AutoTester API on {args.host}:{args.port}")
    
    # Start FastAPI with specified host and port
    uvicorn.run(app, host=args.host, port=args.port) 