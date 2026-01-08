# -*- coding: utf-8 -*-
"""
Real-time Cloud Detection GUI
Shows camera feed with automatic cloud detection based on user location
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import threading
import time
import os
import sys

# Add the codes directory to the path to import cloud_detection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cloud_detection import cloud_detection


class CloudDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-time Cloud Detection")
        self.root.geometry("1200x800")
        
        # Variables
        self.cap = None
        self.is_running = False
        self.latitude = None
        self.longitude = None
        self.time_zone_center_longitude = -120  # Default to PST
        self.current_frame = None
        
        # Setup GUI
        self.setup_gui()
        
        # Initialize geocoder
        self.geolocator = Nominatim(user_agent="cloud_detection_app")
        
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Location input frame
        location_frame = ttk.LabelFrame(main_frame, text="Location Settings", padding="10")
        location_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(location_frame, text="Location (City, Country or Address):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.location_entry = ttk.Entry(location_frame, width=40)
        self.location_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.location_entry.insert(0, "Stanford, CA, USA")
        
        ttk.Button(location_frame, text="Get Coordinates", command=self.get_coordinates).grid(row=0, column=2, padx=5, pady=5)
        
        # Coordinates display
        self.coords_label = ttk.Label(location_frame, text="Latitude: --, Longitude: --", foreground="gray")
        self.coords_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Camera controls frame
        control_frame = ttk.LabelFrame(main_frame, text="Camera Controls", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Camera", command=self.start_camera)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Camera selection
        ttk.Label(control_frame, text="Camera Index:").grid(row=0, column=2, padx=5, pady=5)
        self.camera_var = tk.IntVar(value=0)
        camera_spinbox = ttk.Spinbox(control_frame, from_=0, to=5, textvariable=self.camera_var, width=5)
        camera_spinbox.grid(row=0, column=3, padx=5, pady=5)
        
        # Video display frame
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed with Cloud Detection", padding="10")
        video_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Original feed
        ttk.Label(video_frame, text="Original Feed").grid(row=0, column=0, padx=5)
        self.original_label = ttk.Label(video_frame, text="No camera feed", background="black", foreground="white")
        self.original_label.grid(row=1, column=0, padx=5, pady=5)
        
        # Processed feed with cloud detection
        ttk.Label(video_frame, text="Cloud Detection Result").grid(row=0, column=1, padx=5)
        self.processed_label = ttk.Label(video_frame, text="No camera feed", background="black", foreground="white")
        self.processed_label.grid(row=1, column=1, padx=5, pady=5)
        
        # Status and info frame
        info_frame = ttk.LabelFrame(main_frame, text="Status & Information", padding="10")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(info_frame, text="Status: Ready", foreground="green")
        self.status_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.cloud_cover_label = ttk.Label(info_frame, text="Cloud Cover: --", font=("Arial", 12, "bold"))
        self.cloud_cover_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.time_label = ttk.Label(info_frame, text="Time: --")
        self.time_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        location_frame.columnconfigure(1, weight=1)
        video_frame.columnconfigure(0, weight=1)
        video_frame.columnconfigure(1, weight=1)
        
    def get_coordinates(self):
        """Get latitude and longitude from location name"""
        location_name = self.location_entry.get().strip()
        if not location_name:
            messagebox.showerror("Error", "Please enter a location")
            return
        
        self.status_label.config(text="Status: Getting coordinates...", foreground="orange")
        self.root.update()
        
        def geocode_location():
            try:
                location = self.geolocator.geocode(location_name, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                    
                    # Estimate timezone center longitude (rough approximation)
                    # For US: EST=-75, CST=-90, MST=-105, PST=-120
                    # For other regions, use a simple approximation
                    if -85 <= self.longitude <= -67:  # Eastern US
                        self.time_zone_center_longitude = -75
                    elif -102 <= self.longitude < -85:  # Central US
                        self.time_zone_center_longitude = -90
                    elif -115 <= self.longitude < -102:  # Mountain US
                        self.time_zone_center_longitude = -105
                    elif -125 <= self.longitude < -115:  # Pacific US
                        self.time_zone_center_longitude = -120
                    else:
                        # For other regions, use nearest 15-degree longitude
                        self.time_zone_center_longitude = round(self.longitude / 15) * 15
                    
                    self.coords_label.config(
                        text=f"Latitude: {self.latitude:.4f}°, Longitude: {self.longitude:.4f}°",
                        foreground="green"
                    )
                    self.status_label.config(text="Status: Coordinates obtained", foreground="green")
                else:
                    raise Exception("Location not found")
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                self.status_label.config(text="Status: Geocoding service error", foreground="red")
                messagebox.showerror("Error", f"Could not geocode location: {str(e)}")
            except Exception as e:
                self.status_label.config(text="Status: Error getting coordinates", foreground="red")
                messagebox.showerror("Error", f"Error: {str(e)}")
        
        # Run geocoding in a separate thread to avoid blocking
        threading.Thread(target=geocode_location, daemon=True).start()
        
    def start_camera(self):
        """Start camera capture and cloud detection"""
        if self.latitude is None or self.longitude is None:
            messagebox.showerror("Error", "Please get coordinates first by entering a location and clicking 'Get Coordinates'")
            return
        
        camera_index = self.camera_var.get()
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Could not open camera {camera_index}")
            return
        
        # Set camera resolution (optional, adjust as needed)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Camera running", foreground="green")
        
        # Start video processing
        self.update_frame()
        
    def stop_camera(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Camera stopped", foreground="orange")
        
        # Clear video displays
        self.original_label.config(image='', text="No camera feed")
        self.processed_label.config(image='', text="No camera feed")
        
    def update_frame(self):
        """Update camera frame and perform cloud detection"""
        if not self.is_running or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.config(text="Status: Failed to read frame", foreground="red")
            return
        
        # Resize frame to 64x64 for cloud detection algorithm
        # The algorithm expects 64x64 images
        small_frame = cv2.resize(frame, (64, 64))
        
        # Convert BGR to RGB (OpenCV uses BGR, algorithm expects RGB)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Get current time
        current_time = datetime.datetime.now()
        
        # Perform cloud detection
        try:
            cloud_cover, cloud_mask, sun_mask = cloud_detection(
                current_time,
                rgb_frame,
                latitude=self.latitude,
                longitude=self.longitude,
                time_zone_center_longitude=self.time_zone_center_longitude
            )
            
            # Create overlay visualization
            # Resize masks back to original frame size for display
            display_size = (frame.shape[1], frame.shape[0])
            cloud_mask_large = cv2.resize(cloud_mask, display_size, interpolation=cv2.INTER_NEAREST)
            sun_mask_large = cv2.resize(sun_mask, display_size, interpolation=cv2.INTER_NEAREST)
            
            # Create overlay
            overlay = frame.copy()
            
            # Add sun mask (red)
            overlay = cv2.addWeighted(overlay, 1.0, cv2.cvtColor(sun_mask_large, cv2.COLOR_RGB2BGR), 0.15, 0)
            
            # Add cloud mask (green)
            overlay = cv2.addWeighted(overlay, 1.0, cv2.cvtColor(cloud_mask_large, cv2.COLOR_RGB2BGR), 0.1, 0)
            
            # Add cloud boundaries
            kernel = np.ones((3, 3), np.uint8)
            cloud_boundary = cv2.morphologyEx(cloud_mask_large, cv2.MORPH_GRADIENT, kernel)
            overlay = cv2.addWeighted(overlay, 1.0, cv2.cvtColor(cloud_boundary, cv2.COLOR_RGB2BGR), 0.2, 0)
            
            # Add text overlay
            cv2.putText(overlay, f"Cloud Cover: {cloud_cover:.2%}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(overlay, current_time.strftime("%Y-%m-%d %H:%M:%S"), (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Update labels
            self.cloud_cover_label.config(text=f"Cloud Cover: {cloud_cover:.2%}")
            self.time_label.config(text=f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Convert frames to PhotoImage for display
            original_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            original_img = Image.fromarray(original_img)
            # Use LANCZOS resampling (compatible with older Pillow versions)
            try:
                original_img = original_img.resize((400, 300), Image.Resampling.LANCZOS)
            except AttributeError:
                original_img = original_img.resize((400, 300), Image.LANCZOS)
            original_photo = ImageTk.PhotoImage(image=original_img)
            
            processed_img = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            processed_img = Image.fromarray(processed_img)
            try:
                processed_img = processed_img.resize((400, 300), Image.Resampling.LANCZOS)
            except AttributeError:
                processed_img = processed_img.resize((400, 300), Image.LANCZOS)
            processed_photo = ImageTk.PhotoImage(image=processed_img)
            
            # Update display
            self.original_label.config(image=original_photo, text="")
            self.original_label.image = original_photo  # Keep a reference
            
            self.processed_label.config(image=processed_photo, text="")
            self.processed_label.image = processed_photo  # Keep a reference
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}", foreground="red")
            print(f"Error in cloud detection: {e}")
        
        # Schedule next update
        self.root.after(50, self.update_frame)  # ~20 FPS
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CloudDetectionGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

