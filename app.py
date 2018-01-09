__author__ = 'chetanjakkoju'
from flask.ext.cors import CORS
from flask.ext.jsonpify import jsonify
from datetime import timedelta
from flask import session, app
import json
import urllib2
import re
import os, csv
import uuid
import smtplib
#from PIL import Image
from io import BytesIO
import base64
#import numpy as np
#import cv2
import time
## Training
#train_faces.TrainFromFile("train.txt");

# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
import flask
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response
from werkzeug import secure_filename
import smtplib
from face_search_api import SearchIndexByLargestFace
from face_search_api import SearchIndexByFaceId

# Initialize the Flask application
app = Flask(__name__, template_folder='public' )
cors = CORS(app)

@app.route('/')
def index():
        print 'Main called'
        return render_template("photo.html") 

@app.route('/assets/<path:path>')
def send_css(path):
        return send_from_directory("public/assets/",path) 


@app.route('/save/', methods=['POST'])
def save_image():
        content = request.json
	image_data = re.sub('^data:image/.+;base64,', '', content['image']).decode('base64')
	try:
		listOfUrls = SearchIndexByLargestFace(image_data, content["name"], content["email"], content["phone"] )
	except:
		listOfUrls = []
	return jsonify(results={"status":"success", "data":listOfUrls}); 

@app.route('/search_face_by_id/')
def search_face_by_id():
	fid = request.args.get('fid',default="111", type=str)
	try:
		listOfUrls = SearchIndexByFaceId(fid)
	except:
		listOfUrls = []
	html_code = ""
	for i in range(len(listOfUrls)):
		html_code += "<img src=\""+listOfUrls[i]+"\" width="">"
	return html_code

if __name__ == '__main__':
    app.run(
        host="127.0.0.1",
        port=int("9099"),
        debug = True
    )
