import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def prompt_duplicate_resolution(group: list[str]) -> list[str]:
    """
    Shows a group of duplicate images. Returns a list of paths to KEEP.
    """
    root = tk.Tk()
    root.title("Duplicate Found")
    
    keep_list = []
    
    def on_keep(path):
        keep_list.append(path)
        root.quit()
        
    def keep_all():
        keep_list.extend(group)
        root.quit()

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Select which duplicate to keep:").pack()
    
    img_frame = ttk.Frame(frame)
    img_frame.pack(fill=tk.BOTH, expand=True)
    
    photos = []  # keep referencing to prevent garbage collection
    
    for path in group:
        col = ttk.Frame(img_frame, padding=5)
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        try:
            ext = path.lower()
            if ext.endswith(('.mp4', '.mov')):
                ttk.Label(col, text="[Video File]").pack()
            else:
                img = Image.open(path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                photos.append(photo)
                tk.Label(col, image=photo).pack()
        except Exception as e:
            ttk.Label(col, text=f"[Preview Error]\n{e}").pack()
            
        size_mb = os.path.getsize(path) / (1024 * 1024)
        ttk.Label(col, text=f"{os.path.basename(path)}\n{size_mb:.2f} MB").pack()
        ttk.Button(col, text="Keep This", command=lambda p=path: on_keep(p)).pack()
        
    ttk.Button(frame, text="Keep All", command=keep_all).pack(pady=10)
    
    root.mainloop()
    root.destroy()
    
    # default safety fallback
    if not keep_list:
        keep_list.append(group[0])
        
    return keep_list

def prompt_skipped_files(skipped: list[str]):
    """Simply shows a list of skipped files in a scrollable text box."""
    if not skipped:
        return
        
    root = tk.Tk()
    root.title(f"Files Skipped ({len(skipped)})")
    
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text=f"The following {len(skipped)} files were blurred or rejected:").pack()
    
    text = tk.Text(frame, width=80, height=20)
    text.pack(fill=tk.BOTH, expand=True, pady=10)
    
    for p in skipped:
        text.insert(tk.END, p + "\n")
        
    text.config(state=tk.DISABLED)
    ttk.Button(frame, text="Close", command=root.quit).pack(pady=5)
    
    root.mainloop()
    root.destroy()
