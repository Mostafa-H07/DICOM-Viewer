from PyQt5.QtWidgets import QFileDialog, QApplication
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import Slider, Button

def load_dicom_file():
    """Opens a file dialog to load a DICOM file."""
    try:
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(
            None, "Open DICOM File", "", 
            "DICOM Files (*.dcm);;All Files (*)", 
            options=options)
        
        if not filepath:
            return None, "No file selected."
        ds = pydicom.dcmread(filepath)
        return ds, filepath
    except Exception as e:
        return None, f"Error loading file: {str(e)}"

def display_tags(ds):
    """Returns a formatted string of DICOM tags."""
    if ds is None:
        return "No DICOM file loaded"
    
    tag_list = []
    for elem in ds:
        try:
            tag_id = f"({elem.tag.group:04x},{elem.tag.element:04x})"
            tag_str = f"{tag_id} - {elem.name}: {elem.repval}"
            tag_list.append(tag_str)
        except Exception as e:
            tag_str = f"Error reading tag: {str(e)}"
            tag_list.append(tag_str)
    
    return "\n".join(tag_list)

def display_dicom(ds):
    """Displays a single DICOM image."""
    if ds is None:
        print("No file loaded.")
        return
    
    fig, ax = plt.subplots()
    ax.imshow(ds.pixel_array, cmap='gray')
    ax.set_title("DICOM Viewer")
    ax.axis('off')
    plt.show()

def display_m2d(ds):
    """Displays M2D (multi-frame) DICOM files with a slider."""
    try:
        frames = ds.pixel_array
        print(f"Frame shape: {frames.shape}")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.2)
        
        im = ax.imshow(frames[0])
        ax.set_title(f"Frame 1/{len(frames)}")
        ax.axis('off')
        
        slider_ax = plt.axes([0.1, 0.05, 0.8, 0.03])
        slider = Slider(slider_ax, 'Frame', 0, len(frames)-1, valinit=0, valstep=1)
        
        def update(val):
            frame_idx = int(slider.val)
            im.set_array(frames[frame_idx])
            ax.set_title(f"Frame {frame_idx+1}/{len(frames)}")
            fig.canvas.draw_idle()
        
        slider.on_changed(update)
        
        # Add play/pause functionality
        play_ax = plt.axes([0.1, 0.1, 0.1, 0.04])
        play_button = Button(play_ax, 'Play')
        
        is_playing = [False]
        def play(event):
            is_playing[0] = not is_playing[0]
            play_button.label.set_text('Pause' if is_playing[0] else 'Play')
            
            def animate():
                # Reset to beginning if we're at the end
                if int(slider.val) >= len(frames) - 1:
                    slider.set_val(0)
                
                current_frame = int(slider.val)
                while is_playing[0] and current_frame < len(frames) - 1:
                    current_frame += 1
                    slider.set_val(current_frame)
                    fig.canvas.draw_idle()
                    plt.pause(0.1)  # Increased from 0.05 to 0.1 for slower playback
                
                # Reset play button when reaching the end
                if current_frame >= len(frames) - 1:
                    is_playing[0] = False
                    play_button.label.set_text('Play')
            
            if is_playing[0]:
                animate()
        
        play_button.on_clicked(play)
        plt.show()
        
    except Exception as e:
        print(f"Error in display_m2d: {str(e)}")
        raise

def display_3d(ds):
    """Displays 3D DICOM files as a tiled grid with pagination."""
    if ds is None:
        print("No file loaded.")
        return
    
    volume = ds.pixel_array
    total_slices = len(volume)
    slices_per_page = 16  # 4x4 grid
    current_page = [0]  # Using list to make it accessible in nested function
    fig = plt.figure(figsize=(100, 12))
    fig.suptitle(f'3D Volume Viewer - {total_slices} slices')
    
    def show_page(page_num):
        start_idx = page_num * slices_per_page
        end_idx = min(start_idx + slices_per_page, total_slices)
        
        plt.clf()
        fig.suptitle(f'Slices {start_idx+1}-{end_idx} (Total: {total_slices})')
        
        grid_size = int(np.ceil(np.sqrt(min(slices_per_page, end_idx - start_idx))))
        
        for i, slice_idx in enumerate(range(start_idx, end_idx)):
            ax = plt.subplot(grid_size, grid_size, i + 1)
            ax.imshow(volume[slice_idx], cmap='gray')
            ax.axis('off')
            ax.set_title(f'Slice {slice_idx + 1}')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    def next_page(event):
        max_pages = (total_slices - 1) // slices_per_page
        current_page[0] = min(current_page[0] + 1, max_pages)
        show_page(current_page[0])
        plt.draw()
    
    def prev_page(event):
        current_page[0] = max(current_page[0] - 1, 0)
        show_page(current_page[0])
        plt.draw()
    
    plt.subplots_adjust(bottom=0.15)
    next_button_ax = plt.axes([0.7, 0.02, 0.1, 0.04])
    prev_button_ax = plt.axes([0.2, 0.02, 0.1, 0.04])
    
    next_button = Button(next_button_ax, 'Next')
    prev_button = Button(prev_button_ax, 'Previous')
    
    next_button.on_clicked(next_page)
    prev_button.on_clicked(prev_page)
    
    show_page(0)
    
    def on_key(event):
        if event.key == 'right':
            next_page(event)
        elif event.key == 'left':
            prev_page(event)
    
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()