import os,sys 

def clean_small_json_file(folder_name):
    for root, dirs, files in os.walk(folder_name):
        for f in files:
            if f.endswith(".json"):
                file_path = os.path.join(root,f)
                if os.path.getsize(file_path)<2048:
                    print(f"Remove {file_path}")
                    os.remove(file_path)


if __name__ == "__main__":
    clean_small_json_file(r"\\10.16.12.105\disk\G\Info")