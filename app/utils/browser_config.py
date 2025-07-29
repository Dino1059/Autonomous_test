"""
Browser configuration utilities for Docker environment
"""
import os
from typing import Dict, Any

def get_docker_browser_config() -> Dict[str, Any]:
    """
    Get browser configuration optimized for Docker environment
    """
    
    return {
        "keep_alive": True,
        "headless": True,  # Run in headless mode but enable remote debugging
        "viewport": {"width": 1280, "height": 720},
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--remote-debugging-port=9222",
            "--remote-debugging-address=0.0.0.0",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-gpu-sandbox",
            "--disable-accelerated-2d-canvas",
            "--disable-3d-apis",
            "--disable-webgl",
            "--disable-webgl2",
            "--disable-accelerated-video-decode",
            "--disable-accelerated-video-encode",
            "--disable-accelerated-mjpeg-decode",
            "--disable-accelerated-video",
            "--disable-gpu-compositing",
            "--disable-gpu-rasterization",
            "--disable-gpu-sandbox",
            "--disable-oop-rasterization",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--mute-audio",
            "--no-default-browser-check",
            "--no-pings",
            "--single-process",
            "--disable-process-singleton",
            "--disable-background-mode",
            "--disable-component-update"
        ]
    }

def update_browser_config_for_docker(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing browser config with Docker-friendly settings
    """
    # Use a single default profile directory
    profile_dir = "/app/browser_profiles/default"
    
    # Ensure the directory exists
    os.makedirs(profile_dir, exist_ok=True)
    print(f"Using default browser profile directory: {profile_dir}")
    
    docker_config = get_docker_browser_config()
    
    # Merge configurations, with Docker settings taking precedence
    updated_config = config.copy()
    
    # Always use Docker-friendly user_data_dir
    updated_config["user_data_dir"] = profile_dir
    
    # Always set headless to True for Docker environments
    updated_config["headless"] = True
    
    # Merge args, avoiding duplicates
    existing_args = set(config.get("args", []))
    docker_args = set(docker_config["args"])
    updated_config["args"] = list(existing_args.union(docker_args))
    
    # Ensure other Docker-friendly settings
    updated_config["keep_alive"] = docker_config["keep_alive"]
    if "viewport" not in updated_config:
        updated_config["viewport"] = docker_config["viewport"]
    
    return updated_config 