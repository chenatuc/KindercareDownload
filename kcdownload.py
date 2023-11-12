import os
import sys
import subprocess
import json
import datetime
import requests
import wget
from datetime import datetime
import time


# Function to load cache from file
def load_cache(cache_file):
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return an empty dictionary if no cache exists

# Function to save data to cache
def save_cache(cache_file, data):
    with open(cache_file, 'w') as f:
        json.dump(data, f)



# Child ID - Replace 'xxxxxx' with the actual child ID
child_id = 'xxxxxx'
no_insert_db = False
caption = False

def usage():
    print("Usage:", sys.argv[0], "[-c] [-i]", file=sys.stderr)

def exit_abnormal():
    usage()
    sys.exit(1)

# Parse command-line arguments
while len(sys.argv) > 1 and sys.argv[1].startswith("-"):
    arg = sys.argv.pop(1)
    if arg == '-c':
        caption = True
    elif arg == '-i':
        no_insert_db = True
    else:
        exit_abnormal()

print(f'caption: {caption}, no_insert_db: {no_insert_db}')

# Check for the existence of the 'id.db' file
if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'id.db')):
    open(os.path.join(os.path.dirname(sys.argv[0]), 'id.db'), 'w').close()

done = False
k = 1

cache_file = 'mycache.json'
cache = load_cache(cache_file)

print(f'cache: {cache}')

while not done:
    url = f"https://classroom.kindercare.com/accounts/{child_id}/journal_api?page={k}"

    print(f'url: {url}')


    try:

        with requests.Session() as session:

            response = session.get(url, cookies={'key': 'value'})
            #print(response.text)

            if response.ok:
                print("Login successful!")
                # You can now access other pages that require login
                # For example: response = session.get('https://example.com/anotherpage')
            else:
                print("Login failed!")


        response.raise_for_status()

        json_data = response.json()

        #print(f'json_data type: {type(json_data)}')

        #json.loads(json_string)
        #print(f'json_data: {json_data}')

        intervals = json_data.get('intervals', [])

        if intervals:
            for interval in intervals.values():

                #print(f'interval:{type(interval)} {interval}')
                
                for activity_container in interval:
                    
                    #print(f'activity_container: {type(activity_container)}, {activity_container}')
                    
                    activity = activity_container.get('activity', {})
                    
                    activity_file_id = activity.get('activity_file_id')
                    
                    print(f'activity_file_id: {activity_file_id}')

                    if str(activity_file_id) in cache:
                        continue

                    title = activity.get('title')
                    
                    description = activity.get('description')
                    
                    created_at = activity.get('created_at')
                    
                    image_url = activity.get('image', {}).get('url', {})

                    video_ufl = activity.get('video', {}).get('url')

                    if image_url:
                        file_path = wget.download(image_url)
                    elif video_ufl:
                        file_path = wget.download(video_ufl)

                    # Original datetime string
                    original_format = "%Y-%m-%dT%H:%M:%S.%f%z"
                    original_string = created_at

                    # Parse the original string into a datetime object
                    datetime_obj = datetime.strptime(original_string, original_format)

                    # Add meta data info to indicate the date time the picture/video is taken
                    picture_taken_format = "%Y:%m:%d %H:%M:%S"
                    picture_taken_string = datetime_obj.strftime(picture_taken_format)

                    print(description)
                    subprocess.run(['exiftool', '-DateTimeOriginal='+picture_taken_string, '-Comment='+description, file_path])
                    #subprocess.run(['exiftool', '-DateTimeOriginal='+picture_taken_string, '-XPcomment='+description, file_path])

                    # Change file name
                    new_file_path_format = "%Y-%m-%d_%H-%M-%S_%f"
                    new_file_path = datetime_obj.strftime(new_file_path_format)

                    if image_url:
                        new_file_name = new_file_path+'.jpg'
                    elif video_ufl:
                        new_file_name = new_file_path+'.MOV'
                        
                    subprocess.run(['mv', file_path, new_file_name])

                    # Format the datetime object into the new string format
                    new_format = "%m/%d/%Y %H:%M:%S"
                    new_string = datetime_obj.strftime(new_format)

                    subprocess.run(['SetFile', '-d', new_string, new_file_name])
                    subprocess.run(['SetFile', '-m', new_string, new_file_name])

                    cache[activity_file_id] = 1
                    save_cache(cache_file, cache)

            k += 1
            # if k >= 41:
            #     break

        else:
            done = True

    except Exception as e:
        print("Error:", str(e))
        done = True

# Additional processing, database updates, and cleanup can be added as needed