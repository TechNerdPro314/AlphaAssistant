import os
import sys
import threading
import signal
import time
import asyncio
import subprocess
from app import create_app
from config import DevelopmentConfig

# Global variables for managing both services
web_process = None
bot_thread = None
bot_loop = None


def start_web_app():
    """Start the Flask web application in a separate process"""
    print("🌐 Starting AlphaAssistant web application...")
    print("   Web app will be available at: http://127.0.0.1:5000")

    try:
        # Create the Flask app
        app = create_app(DevelopmentConfig)

        # Run the application
        app.run(debug=False, host="127.0.0.1", port=5000)
    except Exception as e:
        print(f"❌ Failed to start the web application: {e}")


def run_web_in_subprocess():
    """Run the web app in a subprocess"""
    global web_process

    # Use the existing run.py script to start the web app
    web_process = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), "run.py")]
    )

    print("🌐 Web application started (PID: {})".format(web_process.pid))


def stop_web_app():
    """Stop the web application"""
    global web_process

    if web_process and web_process.poll() is None:
        print("🛑 Stopping web application...")
        web_process.terminate()
        try:
            web_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            web_process.kill()


def run_bot_in_thread():
    """Run the Telegram bot in a separate thread"""
    global bot_loop

    # Create a new event loop for the bot thread
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)

    try:
        # Import and run the bot
        import bot

        print("🤖 Starting Telegram bot...")
        print("   Bot username: Kait20TestAssBot")
        bot.main()
    except Exception as e:
        print(f"❌ Failed to start the Telegram bot: {e}")


def start_telegram_bot():
    """Start the Telegram bot in a separate thread"""
    global bot_thread

    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()

    print("⏳ Telegram bot thread started")
    # Give the bot a moment to start
    time.sleep(2)


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down both services...")

    # Stop the web app
    stop_web_app()

    # For the bot, we rely on the daemon thread which will be terminated when the main process exits
    print("🛑 Telegram bot will stop automatically")

    sys.exit(0)


def main():
    """Main function to start both services"""
    print("🚀 Launching AlphaAssistant (Web + Telegram Bot)...")
    print("=" * 50)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the web application
    run_web_in_subprocess()

    # Wait a moment for the web app to start
    print("⏳ Waiting for web application to start...")
    time.sleep(3)

    # Test if the web app is running
    import requests

    try:
        response = requests.get("http://127.0.0.1:5000", timeout=2)
        if response.status_code == 200:
            print("✅ Web application is running")
        else:
            print(f"⚠️  Web application returned status code: {response.status_code}")
    except:
        print("⚠️  Could not verify web application is running")

    # Start the Telegram bot
    start_telegram_bot()

    print("=" * 50)
    print("✅ Both services started successfully!")
    print("   - Web app: http://127.0.0.1:5000")
    print("   - Use Ctrl+C to stop both services")
    print("=" * 50)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
