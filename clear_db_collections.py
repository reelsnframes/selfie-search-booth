import glob
import boto3
import pickle
import time
import os
import uuid
from make_string_safe import get_safe_string
from make_string_safe import get_original_string
from send_mail_test2 import Gmail
import requests
myip = requests.get("http://169.254.169.254/latest/meta-data/public-ipv4").content ## Gives the global ip

gm = Gmail('info@reelsandframes.in', 'sk8erboI!m')

selfie_dir = "selfies" #local directory
imageBucket = 'rnf-test-set-1' ## While creating make sure you set the bucket permissions to public
#{
#    "Version": "2012-10-17",
#    "Statement": [
#        {
#            "Sid": "AddPerm",
#            "Effect": "Allow",
#            "Principal": "*",
#            "Action": "s3:GetObject",
#            "Resource": "arn:aws:s3:::testset1/*"
#        }
#    ]
#}

defaultRegion = 'eu-west-1'
collection_id = "testbucketrframes_c" 
algo = 'rekognition' # Amazon
client = boto3.client(algo, region_name='eu-west-1')
collection_id_selfies = collection_id + "_selfies"

from pymongo import MongoClient
conn = MongoClient('localhost', 27017)
conn.drop_database("face_list")

try:
	resp = client.delete_collection( CollectionId=collection_id_selfies)
except:
	print "Collection_selfie already created, proceeding..."

try:
	resp = client.delete_collection( CollectionId=collection_id)
except:
	print "Collection_selfie already created, proceeding..."


