"""
Camera test for Reachy Mini.
Press 'q' to quit, 's' to save a snapshot.
"""
from reachy_mini import ReachyMini
import cv2
import time

with ReachyMini() as mini:
    print("📷 Camera test starting...")
    print("   Press 'q' to quit")
    print("   Press 's' to save a snapshot")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        # Get frame from camera
        frame = mini.media.get_frame()
        
        if frame is None:
            print("⚠️  No frame received. Is the camera connected?")
            time.sleep(0.5)
            continue
        
        frame_count += 1
        
        # Calculate FPS
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        
        # Add FPS overlay
        cv2.putText(
            frame, 
            f"FPS: {fps:.1f}", 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2
        )
        
        # Display the frame
        cv2.imshow("Reachy Mini Camera", frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("👋 Quitting...")
            break
        elif key == ord('s'):
            filename = f"snapshot_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Saved: {filename}")

cv2.destroyAllWindows()
print("✅ Camera test complete!")

