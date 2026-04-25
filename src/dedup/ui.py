import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def center_window(root):
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')

def prompt_duplicate_resolution(group: list[str], is_dry_run: bool = False) -> list[str]:
    """
    Shows a group of duplicate images. Returns a list of paths to KEEP.
    """
    root = tk.Tk()
    title = "Duplicate Found"
    if is_dry_run:
        title += " (DRY RUN - PREVIEW ONLY)"
    root.title(title)
    
    keep_list = []
    resolved = [False]

    def on_keep(path):
        keep_list.append(path)
        resolved[0] = True
        root.quit()
        
    def keep_all():
        keep_list.extend(group)
        resolved[0] = True
        root.quit()

    def discard_all():
        keep_list.clear()
        resolved[0] = True
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
        
        ext = path.lower()
        if ext.endswith(('.mp4', '.mov')):
            ttk.Label(col, text="[Video File]").pack()
        else:
            img = Image.open(path)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)
            photos.append(photo)
            tk.Label(col, image=photo).pack()

        size_mb = os.path.getsize(path) / (1024 * 1024)
        ttk.Label(col, text=f"{os.path.basename(path)}\n{size_mb:.2f} MB").pack()
        ttk.Button(col, text="Keep This", command=lambda p=path: on_keep(p)).pack()

    btn_frame = ttk.Frame(frame, padding=10)
    btn_frame.pack()
    ttk.Button(btn_frame, text="Keep All", command=keep_all).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Discard All", command=discard_all).pack(side=tk.LEFT, padx=5)

    center_window(root)
    root.mainloop()
    root.destroy()

    if not resolved[0]:
        raise ValueError("No resolution was selected. Please choose to Keep or Discard.")

    return keep_list

def prompt_rejection_confirmation(path: str, reason: str, is_dry_run: bool = False) -> str:
    """
    Shows a file rejected for a specific reason. 
    Returns 'skip', 'keep', or 'skip_all'.
    """
    root = tk.Tk()
    title = f"Confirm Rejection: {reason}"
    if is_dry_run:
        title += " (DRY RUN)"
    root.title(title)

    choice = ["skip"]

    def on_choice(c):
        choice[0] = c
        root.quit()

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=f"This file was flagged as [bold]{reason}[/bold]. Skip it?").pack()

    ext = path.lower()
    if ext.endswith(('.mp4', '.mov')):
        ttk.Label(frame, text="[Video File]").pack(pady=10)
    else:
        img = Image.open(path)
        img.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(frame, image=photo)
        lbl.image = photo # type: ignore
        lbl.pack(pady=10)

    ttk.Label(frame, text=os.path.basename(path)).pack()
    
    btn_frame = ttk.Frame(frame, padding=10)
    btn_frame.pack()
    
    ttk.Button(btn_frame, text="Skip (Move to skipped/)", command=lambda: on_choice("skip")).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Keep Anyway", command=lambda: on_choice("keep")).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Skip All Remaining", command=lambda: on_choice("skip_all")).pack(side=tk.LEFT, padx=5)

    center_window(root)
    root.mainloop()
    root.destroy()
    return choice[0]

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
    
    center_window(root)
    root.mainloop()
    root.destroy()
