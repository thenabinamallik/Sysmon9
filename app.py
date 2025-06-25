from ui import SystemMonitorUI  # Import the UI class from the ui module

def main():
    """
    Main function to start the system monitor app.
    Initializes the UI and starts the Tkinter main loop.
    """
    app = SystemMonitorUI()  # Create an instance of the main UI class
    app.run()                # Start the application loop (Tkinter mainloop)

# Only run this when the script is executed directly (not imported)
if __name__ == "__main__":
    main()
