import boto3                # API testing:          
import requests             # https://developer.vimeo.com/api/reference/videos#get_videos
import time
import concurrent.futures         
import os
from dotenv import load_dotenv
import vimeo

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

VIMEO_TOKEN = os.getenv("VIMEO_TOKEN")
VIMEO_CLIENT_IDENTIFIER = os.getenv("VIMEO_CLIENT_IDENTIFIER")
VIMEO_CLIENT_SECRET = os.getenv("VIMEO_CLIENT_SECRET")

S3_BUCKET_NAME = os.getenv("BUCKET_NAME")
OPTIONAL_PATH = os.getenv("OPTIONAL_PATH")      # use if you want to store the videos in a 
                                                # specific folder inside the S3 bucket
                                                # '' if transferring the files to the root of the bucket

if OPTIONAL_PATH != '': OPTIONAL_PATH = OPTIONAL_PATH + '/'
start_time = time.time()

# initialize Vimeo and S3 clients
s3 = boto3.client('s3', aws_access_key_id = AWS_ACCESS_KEY, aws_secret_access_key = AWS_SECRET_ACCESS_KEY)
client = vimeo.VimeoClient(token = VIMEO_TOKEN, key = VIMEO_CLIENT_IDENTIFIER, secret = VIMEO_CLIENT_SECRET)
