# MoMo - Mouse Mover

A lightweight Windows utility to prevent system idle timeout and maintain "active" presence status in Microsoft Teams.

## Features

- 🖱️ **Idle Detection**: Monitors mouse and keyboard activity
- 🔄 **Automatic Mouse Movement**: Imperceptible mouse movement when idle threshold is exceeded
- ⏰ **Configurable Schedule**: Set active hours per day of the week
- 🚀 **Auto-Start**: Optional startup with Windows
- 🎯 **System Tray**: Non-intrusive system tray icon with visual feedback

## Requirements

- Windows 11 or later
- Python 3.10+ (for development)

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/bretstateham/momo.git
   cd momo
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

### Building Standalone Executable

To build a standalone `.exe` file:

```bash
pip install pyinstaller
pyinstaller momo.spec
```

The executable will be created in the `dist` folder.

## Usage

1. **Start MoMo**: Run the application - it will appear in your system tray
2. **Configure**: Right-click the tray icon to access settings:
   - Start/Stop monitoring
   - Configure idle threshold (default: 5 minutes)
   - Configure weekly schedule (default: Mon-Fri 8am-5pm)
   - Enable/disable auto-start with Windows
3. **Visual Feedback**: The tray icon turns green when actively moving the mouse

## Configuration

Settings are stored in `momo_settings.json` in the same directory as the executable.

### Default Settings

- **Idle Threshold**: 300 seconds (5 minutes)
- **Schedule**: Monday-Friday, 8:00 AM - 5:00 PM
- **Auto-Start**: Disabled

## Development

### Project Structure

```
momo/
├── src/
│   ├── main.py              # Entry point
│   └── momo/
│       ├── __init__.py      # Package info
│       ├── app.py           # Main application
│       ├── idle_detector.py # Idle detection
│       ├── mouse_mover.py   # Mouse movement
│       ├── settings.py      # Configuration
│       ├── schedule.py      # Schedule management
│       ├── tray_icon.py     # System tray UI
│       ├── autostart.py     # Windows auto-start
│       └── dialogs.py       # Configuration dialogs
├── requirements.txt
├── momo.spec               # PyInstaller spec
└── README.md
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License

## Author

Bret Stateham
