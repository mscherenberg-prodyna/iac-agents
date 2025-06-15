"""Simple startup script for the enhanced Infrastructure as Code AI Agent."""

import subprocess
import sys


def run_enhanced_streamlit():
    """Run the enhanced Streamlit interface."""
    print("🚀 Starting Enhanced Infrastructure as Code AI Agent")
    print("=" * 60)
    print()
    print("✨ Features:")
    print("  • Real-time agent orchestration with supervisor agent")
    print("  • Console logging showing agent activities")
    print("  • Azure cost estimation")
    print("  • Enhanced chat interface with proper scrolling")
    print("  • Live workflow progress tracking")
    print()
    print("🌐 Opening in your browser...")
    print("📊 Watch the console for real-time agent activity logs!")
    print()

    # Run streamlit
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/iac_agents/streamlit/enhanced_gui.py",
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error running demo: {e}")


def run_console_demo():
    """Run the console-only demo."""
    print("🖥️ Running Console Demo")
    print("=" * 30)

    try:
        subprocess.run([sys.executable, "test_enhanced_system.py"], check=True)
    except Exception as e:
        print(f"❌ Error running console demo: {e}")


def main():
    """Main menu for demo options."""
    print("🤖 Infrastructure as Prompts AI Agent")
    print("=" * 50)
    print()
    print("Choose demo mode:")
    print("1. 🌐 Enhanced Streamlit Interface (Recommended)")
    print("2. 🖥️ Console Demo with Logging")
    print("3. 📊 Original Streamlit Interface")
    print("0. Exit")
    print()

    choice = input("Enter your choice (0-3): ").strip()

    if choice == "1":
        run_enhanced_streamlit()
    elif choice == "2":
        run_console_demo()
    elif choice == "3":
        print("🌐 Starting Original Streamlit Interface...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "src/iac_agents/streamlit/gui.py",
                ],
                check=True,
            )
        except KeyboardInterrupt:
            print("\n👋 Demo stopped by user")
    elif choice == "0":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
