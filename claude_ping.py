#!/usr/bin/env python3
import json
import sys
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value

def send_mac_notification(title, message, sound_file=None):
    """Send macOS notification with icon"""
    print(f"Sending notification: {title} - {message}")
    
    # Get icon path relative to script
    script_dir = Path(__file__).parent
    icon_path = script_dir / "icon.png"
    
    # Use terminal-notifier if available for better icon support
    try:
        subprocess.run([
            'terminal-notifier',
            '-title', title,
            '-message', message,
            '-contentImage', str(icon_path)
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to osascript
        script = f'''
        tell application "System Events"
            display notification "{message}" with title "{title}"
        end tell
        '''
        subprocess.run(['osascript', '-e', script])

def main():
    # Read input from Claude Code
    input_data = json.loads(sys.stdin.read())
    print(json.dumps(input_data))
    
    # Check if stop_hook_active to prevent loops
    if input_data.get('stop_hook_active'):
        print(json.dumps({"decision": "approve"}))
        return
    
    # Send notifications
    time_str = datetime.now().strftime('%H:%M:%S')
    title = "Claude Code Finished"
    
    # Read transcript content if available
    transcript_content = ""
    if 'transcript_path' in input_data:
        try:
            with open(input_data['transcript_path'], 'r') as f:
                lines = f.readlines()
                
                # Get the last line (most recent entry)
                if lines:
                    last_line = lines[-1].strip()
                    try:
                        transcript_json = json.loads(last_line)
                        if 'message' in transcript_json and 'content' in transcript_json['message']:
                            for item in transcript_json['message']['content']:
                                if item.get('type') == 'text':
                                    transcript_content = item.get('text', '')
                                    break
                        if not transcript_content:
                            transcript_content = "No text content found"
                    except:
                        transcript_content = "Failed to parse transcript"
                else:
                    transcript_content = "No transcript data"
                
                
                # Limit to last 200 characters for notification
                if len(transcript_content) > 200:
                    transcript_content = "..." + transcript_content[-200:]
        except:
            transcript_content = f"Transcript at {input_data['transcript_path']}"
    
    send_mac_notification(title, transcript_content)
    
    # Let Claude continue
    print(json.dumps({"decision": "approve"}))

if __name__ == "__main__":
    main()