"""
Browser configuration utilities for Docker/Local environment
"""
import os
from typing import Dict, Any


def is_running_in_docker() -> bool:
    """Detect if we're running inside a Docker container"""
    return os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER", "").lower() == "true"


def get_headless_mode() -> bool:
    """
    Determine headless mode:
    - If env var HEADLESS is set explicitly, use that
    - If running in Docker, default to True (headless)
    - If running locally (Mac/Linux desktop), default to False (visible browser window)
    """
    env_headless = os.environ.get("HEADLESS")
    if env_headless is not None:
        return env_headless.lower() == "true"
    return is_running_in_docker()


def get_browser_args(headless: bool) -> list:
    """Get appropriate Chrome args based on headless mode"""
    base_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--remote-debugging-port=9222",
        "--remote-debugging-address=0.0.0.0",
        "--disable-web-security",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-ipc-flooding-protection",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-sync",
        "--disable-translate",
        "--mute-audio",
        "--no-default-browser-check",
        "--no-pings",
        "--disable-component-update",
    ]

    if headless:
        # Additional GPU-disabling flags only needed for headless/Docker
        base_args += [
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
            "--disable-gpu-compositing",
            "--disable-gpu-rasterization",
            "--disable-oop-rasterization",
            "--single-process",
            "--disable-process-singleton",
            "--disable-background-mode",
            "--hide-scrollbars",
        ]

    return base_args


def get_docker_browser_config() -> Dict[str, Any]:
    """
    Get browser configuration (auto-detects headless vs visible)
    """
    headless = get_headless_mode()
    return {
        "keep_alive": True,
        "headless": headless,
        "viewport": {"width": 1280, "height": 720},
        "args": get_browser_args(headless),
    }


def update_browser_config_for_docker(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing browser config with environment-appropriate settings.
    - In Docker: headless=True, use /app/browser_profiles
    - On Local desktop: headless=False, browser window is visible
    """
    headless = get_headless_mode()

    # Profile directory: use local path when not in Docker
    if is_running_in_docker():
        profile_dir = "/app/browser_profiles/default"
    else:
        profile_dir = os.path.join(os.getcwd(), "browser_profiles", "default")

    os.makedirs(profile_dir, exist_ok=True)
    print(f"[BrowserConfig] headless={headless}, profile={profile_dir}")

    base_config = get_docker_browser_config()

    # Merge configurations
    updated_config = config.copy()
    updated_config["user_data_dir"] = profile_dir
    updated_config["headless"] = headless
    updated_config["keep_alive"] = base_config["keep_alive"]

    # Merge args, avoiding duplicates
    existing_args = set(config.get("args", []))
    base_args = set(base_config["args"])
    updated_config["args"] = list(existing_args.union(base_args))

    if "viewport" not in updated_config:
        updated_config["viewport"] = base_config["viewport"]

    return updated_config