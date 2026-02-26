"""Unified launcher: starts FastAPI in a background thread and the Discord bot in the main thread."""

import asyncio
import threading
import os
import uvicorn


def start_api_server():
    """Run the FastAPI server in a background thread."""
    from api.main import create_app

    app = create_app()
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


async def _init_database():
    """Initialize the database and seed config from .env."""
    import db
    await db.init_db()
    await db.sync_env_to_db()


def main():
    import config
    import providers

    # Initialize database synchronously before anything else
    asyncio.run(_init_database())

    available = providers.get_available_providers()

    print("=" * 50)
    print("  SparkSage — Bot + Dashboard Launcher")
    print("=" * 50)

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    print(f"  API server starting on http://localhost:{port}")

    # Start Discord bot in main thread
    if not config.DISCORD_TOKEN:
        print("  WARNING: DISCORD_TOKEN not set — bot will not start.")
        print("  API server is running. Use the dashboard to configure the bot.")
        # Keep main thread alive for the API server
        try:
            api_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            return

    if not available:
        print("  WARNING: No AI providers configured. Add at least one API key.")
        print("  You can configure providers through the dashboard.")

    print(f"  Primary provider: {config.AI_PROVIDER}")
    print(f"  Fallback chain: {' -> '.join(available) if available else 'none'}")
    print("=" * 50)

    from bot import bot
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
