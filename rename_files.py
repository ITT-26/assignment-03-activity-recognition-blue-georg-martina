# for inconsitencies (more "-" than usual)
import os

# base path
parent_folder = 'data' 

# os.walk goes through all folders and files in the base path
for root, folders, files in os.walk(parent_folder):
    for file_name in files:

        new_name = file_name
        
        # check if the filename contains "jumping_jacks"
        if "jumping_jacks" in new_name:
            
            # change "jumping_jacks" to "jumpingjacks" in the filename
            new_name = new_name.replace("jumping_jacks", "jumpingjacks")

        # check if the filename contains "Viet-Hang-Thu"
        if "Viet-Hang-Thu" in new_name:

            # change "Viet-Hang-Thu" to "thu" in the filename
            new_name = new_name.replace("Viet-Hang-Thu", "thu")

        if new_name != file_name:
            old_path = os.path.join(root, file_name)
            new_path = os.path.join(root, new_name)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed in {os.path.basename(root)}: {file_name} -> {new_name}")
            except OSError as e:
                print(f"Error when trying to rename {file_name}: {e}")            

print("Done")