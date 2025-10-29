import cv2
import numpy as np
from pykinect import nui
import thread # Use 'thread' in Python 2.7

print("Connecting to Kinect v1...")

# --- Global Variables ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_CHANNELS_RAW = 4 # Kinect provides BGRA data (32bpp)
FRAME_CHANNELS_DISPLAY = 3 # OpenCV imshow needs BGR data

# Thread lock for safe access to the frame buffer
frame_lock = thread.allocate_lock() 
# Buffer to hold the latest raw frame data (BGRA) from the Kinect callback
latest_frame_raw = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, FRAME_CHANNELS_RAW), dtype=np.uint8)
# Flag to signal when a new frame is available
new_frame_available = False

# --- Kinect Callback Function ---
def kinect_video_callback(frame):
    """This function runs in a separate thread whenever the Kinect has a new video frame."""
    global latest_frame_raw, new_frame_available
    
    with frame_lock:
        try:
            # Directly copy the raw BGRA pixel data into our buffer
            frame.image.copy_bits(latest_frame_raw.ctypes.data)
            new_frame_available = True
        except Exception as e:
            print("[Callback Error] Failed to copy frame data: {}".format(e))
            # Keep running even if one frame fails

# --- Main Application Logic ---
def main():
    """Initializes Kinect, opens stream, and runs the display loop."""
    global latest_frame_raw, new_frame_available

    print("Initializing Kinect Runtime...")
    try:
        kinect = nui.Runtime()
    except Exception as e:
        print("Error: Failed to initialize Kinect Runtime.")
        print("  - Ensure Kinect SDK v1.8 is installed.")
        print("  - Ensure Memory Integrity (Core Isolation) is OFF.")
        print("  - Ensure Kinect is plugged into a USB 2.0 port (or powered USB 2.0 hub).")
        print("  - Check Kinect power adapter light is SOLID GREEN.")
        print("  - Specific Error: {}".format(e))
        return # Exit if initialization fails

    print("Opening video stream (640x480 Color)...")
    try:
        # Register our callback function to receive frames
        kinect.video_frame_ready += kinect_video_callback 
        
        # Open the stream
        kinect.video_stream.open(
            nui.ImageStreamType.Video,    # Color stream
            2,                            # Number of frame buffers
            nui.ImageResolution.Resolution640x480, 
            nui.ImageType.Color)          # Request BGRA format
            
    except Exception as e:
        print("Error: Failed to open video stream: {}".format(e))
        kinect.close()
        return

    print("Kinect stream opened successfully. Displaying video...")
    cv2.namedWindow('Kinect v1 Video - Clean', cv2.WINDOW_AUTOSIZE)

    while True:
        display_frame = None # Frame to show in the window

        with frame_lock:
            if new_frame_available:
                # Convert the raw BGRA frame to BGR for OpenCV display
                display_frame = cv2.cvtColor(latest_frame_raw, cv2.COLOR_BGRA2BGR)
                new_frame_available = False # Reset the flag

        # Only display if we successfully processed a new frame
        if display_frame is not None:
            cv2.imshow('Kinect v1 Video - Clean', display_frame)

        # Check for 'q' key press to exit (waits 1ms for a key)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("'q' pressed, exiting...")
            break
            
    print("Stopping Kinect stream...")
    kinect.close()
    cv2.destroyAllWindows()
    print("Stream stopped and resources released.")

if __name__ == '__main__':
    main()