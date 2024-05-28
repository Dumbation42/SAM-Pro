import requests
import difflib
import os

github_url = "https://raw.githubusercontent.com/Dumbation42/SAM-Pro/main/SAM pro.py"

local_file_path = "Local path to SAM pro.py"

# Function to fetch bot.py from GitHub
def fetch_github_version(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch the GitHub version of bot.py: {e}")
        return None

# Function to read the local version of bot.py 
def read_local_version(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except IOError as e:
        print(f"Failed to read the local version of bot.py: {e}")
        return None

# Compare the GitHub version with the local version
def compare_and_update(github_content, local_content, local_path):
    if github_content is None or local_content is None:
        print("One of the versions could not be read. Aborting update.")
        return
    
    # Use difflib to compare the files
    if github_content == local_content:
        print("The local version of SAM pro.py is up-to-date.")
    else:
        print("Differences detected. Updating the local version of bot.py...")
        try:
            with open(local_path, 'w', encoding='utf-8') as file:
                file.write(github_content)
            print("Update successful!")
        except IOError as e:
            print(f"Failed to update the local version of bot.py: {e}")

if __name__ == "__main__":
    github_version = fetch_github_version(github_url)
    local_version = read_local_version(local_file_path)
    compare_and_update(github_version, local_version, local_file_path)
