import os
import shutil
import imagehash

def group_identical_or_near(hashes_dict: dict[str, str], threshold: int) -> list[list[str]]:
    """Groups file paths by their perceptual hash similarity."""
    groups = []
    visited = set()
    
    files = list(hashes_dict.keys())
    
    for i, file_a in enumerate(files):
        if file_a in visited:
            continue
            
        hash_a_str = hashes_dict[file_a]
        if not hash_a_str:
            continue
            
        # Parse the string back to a hash object for distance comparison
        hash_a = imagehash.hex_to_hash(hash_a_str)
        current_group = [file_a]
        visited.add(file_a)
        
        for j in range(i + 1, len(files)):
            file_b = files[j]
            if file_b in visited:
                continue
                
            hash_b_str = hashes_dict[file_b]
            if not hash_b_str:
                continue
                
            hash_b = imagehash.hex_to_hash(hash_b_str)
            
            # Simple Hamming distance
            if hash_a - hash_b <= threshold:
                current_group.append(file_b)
                visited.add(file_b)
                
        if len(current_group) > 1:
            groups.append(current_group)
            
    return groups

def move_to_skipped(files_to_skip: list[str], base_dir: str, folder_name: str = "skipped"):
    """Moves a list of absolute file paths to the skipped folder under base_dir."""
    if not files_to_skip:
        return
    skipped_dir = os.path.join(base_dir, folder_name)
    os.makedirs(skipped_dir, exist_ok=True)
    
    for file_path in files_to_skip:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            dest = os.path.join(skipped_dir, file_name)
            
            # handle naming collisions in the skipped directory
            counter = 1
            while os.path.exists(dest):
                name, ext = os.path.splitext(file_name)
                dest = os.path.join(skipped_dir, f"{name}_{counter}{ext}")
                counter += 1
                
            shutil.move(file_path, dest)
