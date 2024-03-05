import boto3  # API testing:
import requests  # https://developer.vimeo.com/api/reference/videos#get_videos
import time
import concurrent.futures
import os
from dotenv import load_dotenv
import vimeo
import datetime
import json

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

VIMEO_TOKEN = os.getenv("VIMEO_TOKEN")
VIMEO_CLIENT_IDENTIFIER = os.getenv("VIMEO_CLIENT_IDENTIFIER")
VIMEO_CLIENT_SECRET = os.getenv("VIMEO_CLIENT_SECRET")

S3_BUCKET_NAME = os.getenv("BUCKET_NAME")
OPTIONAL_PATH = os.getenv("OPTIONAL_PATH")  # use if you want to store the videos in a
# specific folder inside the S3 bucket
# '' if transferring the files to the root of the bucket

if OPTIONAL_PATH != "":
    OPTIONAL_PATH = OPTIONAL_PATH + "/"
start_time = time.time()

# initialize Vimeo and S3 clients
s3 = boto3.client(
    "s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
client = vimeo.VimeoClient(
    token=VIMEO_TOKEN, key=VIMEO_CLIENT_IDENTIFIER, secret=VIMEO_CLIENT_SECRET, **{'timeout':100}
)


def check_date(last_action_date_string):
    date_format = "%Y-%m-%d"

    last_action_date = datetime.datetime.strptime(last_action_date_string, date_format)
    previous_migration_date = datetime.datetime.strptime("2023-10-05", date_format)

    if last_action_date <= previous_migration_date:
        print("Reached the end")
        quit()


def append_to_file(file_path, data):
    try:
        with open(file_path, "a") as file:
            file.write(data + "\n")
        print("Data appended successfully.")
    except Exception as e:
        print("An error occurred:", str(e))


def transfer_video(video):
    video_id = video["uri"].split("/")[-1]
    video_name = video["name"]
    video_url = video["download"][0]["link"]
    ancestor_path = [""]
    parent_folder_name = ""

    check_date(video["last_user_action_event_date"].split("T")[0])

    # generate Vimeo video full path
    # ancestor path is all the folders above up to the root, except the parent folder
    if video["parent_folder"] is not None:
        parent_folder_name = video["parent_folder"]["name"] + "/"
        if video["parent_folder"]["metadata"]["connections"]["ancestor_path"]:
            ancestors = video["parent_folder"]["metadata"]["connections"][
                "ancestor_path"
            ]
            for ancestor in ancestors:
                ancestor_name = ancestor["name"]
                ancestor_path.insert(0, ancestor_name)
    full_path = "/".join(ancestor_path) + parent_folder_name
    path_string = " /" + OPTIONAL_PATH + full_path + video_name
    print(path_string)

    append_to_file(f"parallelism-items-{datetime.now()}.json", path_string)


#    with open(f"vimeo-items-{datetime.now()}.txt", "a") as myfile:
#        myfile.write('/' + OPTIONAL_PATH + full_path + video_name)


# upload the content to S3 using a request stream
#    r = requests.get(video_url, stream=True, timeout=3600)
#    s3.upload_fileobj(r.raw, S3_BUCKET_NAME, OPTIONAL_PATH + full_path + video_name + '.mp4')

if __name__ == "__main__":
    response = client.get(
        "/me/videos",
        params={
            "per_page": 50,
            "sort": "date",
            "direction": "desc",
            "fields": "uri,download,name,parent_folder,last_user_action_event_date",
        },
    )
    total_pages = response.json()["total"] // 50 + 1
    videos = response.json()["data"]
    append_to_file(f"Vic-object-{datetime.datetime.now()}.json", json.dumps(videos))

    # parallelism
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for i in range(2, total_pages + 1):
            futures.append(
                executor.submit(
                    client.get,
                    "/me/videos",
                    params={
                        "per_page": 50,
                        "page": i,
                        "sort": "date",
                        "direction": "desc",
                        "fields": "uri,download,name,parent_folder,last_user_action_event_date",
                    },
                )
            )
        for future in concurrent.futures.as_completed(futures):
            try:
                videos.extend(future.result().json()["data"])
            except Exception as e:
                append_to_file('error-data.json',json.dumps(future.result().json()))
                print("this error here: ")
                print(str(e))
        for video in videos:
            executor.submit(transfer_video, video)
print("--- %s seconds ---" % (time.time() - start_time))
