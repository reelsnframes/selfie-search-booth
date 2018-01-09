import glob
import boto3
import pickle
import time
import os
import uuid
import shutil
from make_string_safe import get_safe_string
from make_string_safe import get_original_string
import requests
import cv2
import get_all_latest_keys

FACE_MATCH_CUTOFF = 80
myip = requests.get("http://169.254.169.254/latest/meta-data/public-ipv4").content # Gets the global ip


selfie_dir = "selfies"
mail_dir = "mail_dir"
sent_dir = "sent_dir"
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
collection_id = "testbucketrframes_g"  ## Amazon-index, ID1

face_client = boto3.client('rekognition', region_name='eu-west-1')
s3_client = boto3.client('s3')

collection_id_selfies = collection_id + "_selfies" ## Amzon-index, ID2

from pymongo import MongoClient
db = MongoClient('localhost', 27017).face_list

try:
	resp = face_client.create_collection( CollectionId=collection_id_selfies)
except:
	print "Collection_selfie already created, proceeding..."

try:
        resp = face_client.create_collection( CollectionId=collection_id)
except:
        print "Collection already created, proceeding..."


def CheckIfEmailExistsInDb (email_id):
	rs = db.posts.find({"email":get_original_string(email_id)})
	for r in rs:
		if( r.has_key("marriage_id") ):
			if( r["marriage_id"] == collection_id ):
				return True

	return False

def get_face_id_all(email_id):
	r = db.posts.find_one({"email":get_original_string(email_id),"marriage_id":collection_id})
	if( r == None ):
		return ""
	else:
		return r["face_id_all"]

def get_name_from_email_id(email_id):
	r = db.posts.find_one({"email":get_original_string(email_id)})
	if( r == None ):
		return ""
	return r["name"]

def get_all_files(bucketname):
	fileList = []
	try:
		for key in s3_client.list_objects(Bucket=bucketname)['Contents']:
			fileList.append( key['Key'] )
	except:
		pass
	return fileList


def get_existing_indexed_file_list( collection_id ):
        resp = face_client.list_faces(CollectionId=collection_id,MaxResults=400000)
        list_of_images = []
        for i in range(len(resp['Faces'])):
                list_of_images.append( get_original_string( resp['Faces'][i]['ExternalImageId'] ) )
        return list( set( list_of_images ) )


def Send_mail_to_user_simple(images_list, email_id, name, gm):
	html_code = "               "
	for impath in images_list[:3]:
		full_url = "https://s3-eu-west-1.amazonaws.com/"+imageBucket+"/"+impath
		full_url = full_url.replace(" ","+")
#		html_code += "<img src="+full_url+"><br>"
	if( len( html_code ) > 10 ):
		isSentFlag = False
		for tryi in range(2):
			face_id_all = get_face_id_all(  get_original_string(email_id) )
			if( len(face_id_all) <= 1 ):
				continue
			print "Sent mail to : "+ email_id
			html_code_prepend = ""
			html_code_prepend = "Click <a href="+"\"http://"+myip+"/reelsnframes/search_face_by_id?fid="+ face_id_all + "\">here</a> for full list.<br>"
			email_body = "Hi "+name+ "<br><br>"+"We found few photos of you. "+html_code_prepend +"<br>"+ html_code + "<br><br>" + "Regards  <br> Anand Rathi <br> <a href=http://reelsandframes.in>reelsandframes.in</a>"
			gm.send_message_html(email_id,'Found few photos of you!', email_body)
			
			isSentFlag = True
			if( isSentFlag ):
				break;
	


def Send_mail_to_user(images_list):
	listOfAddedFaces = []
	listOfAddedFaces_ExIds = []
	dict_email_images = {}
	dict_email_selfie = {}
	## Add the indexed images to selfies list
	for key in images_list:
		try:
			resp = face_client.index_faces(CollectionId = collection_id_selfies ,Image = {"S3Object" : {'Bucket' : imageBucket, 'Name' : key}}, ExternalImageId = get_safe_string(key))
		except:
			continue;
		for i in range(len( resp['FaceRecords'] )): 
			listOfAddedFaces.append( resp['FaceRecords'][i]['Face']['FaceId'] ) # Per face
			listOfAddedFaces_ExIds.append( key ) #Image file name
		

	
	## Query with face_id's and get multiple images per email_id
	for afi in range(len(listOfAddedFaces)):
		face_id = listOfAddedFaces[afi]
		resp = face_client.search_faces(CollectionId=collection_id_selfies,FaceId=face_id, MaxFaces=1000,FaceMatchThreshold=FACE_MATCH_CUTOFF)

		for i in range(len(resp['FaceMatches'])):
			external_path = resp['FaceMatches'][i]['Face']['ExternalImageId'] 
			if( "@" in get_original_string(external_path) ): ## Selfie
				email_key = get_original_string(external_path)
				if( not dict_email_images.has_key(email_key) ):
					dict_email_images[email_key] = []
				dict_email_images[email_key].append( listOfAddedFaces_ExIds[afi] ) ## Per email we will have multiple external ids

	if( len(listOfAddedFaces) > 0 ):
		face_client.delete_faces( CollectionId = collection_id_selfies, FaceIds = listOfAddedFaces ) 

	for email_id in dict_email_images: ## New detected email ids
		html_code = ""
		dict_email_images[email_id] = list(set(dict_email_images[email_id]))

		mail_dict = {}
		mail_dict["listOfNewFiles"] = dict_email_images[email_id]
		mail_dict["email"] = email_id
		mail_dict["name"] = get_name_from_email_id(email_id)
	
		pickle.dump(  mail_dict, open( mail_dir+"/"+str(uuid.uuid4())+"_simple.pkl", "wb" ) )
	


def Reduce_resolution(bucketName, key, max_width = 2000):
	tempImageFileName = str(uuid.uuid4())+"."+key.split(".")[-1]
	s3_client.download_file(bucketName, key, tempImageFileName)
	im = cv2.imread(tempImageFileName)
	if( im.shape[1] > max_width ):
		s3_client.delete_object(Bucket=bucketName, Key=key)
		im = cv2.resize(im, (max_width,int( max_width*im.shape[0]/im.shape[1] )) )
		cv2.imwrite( tempImageFileName, im )
	s3_client.upload_file(tempImageFileName, bucketName, key)
	os.remove( tempImageFileName )
	
	return 		
def IndexFacesFromS3Folder(imageBucket, time_gap):
	### Index will be updated if new images are present.

	listOfNewKeys = get_all_latest_keys.get_all_latest_keys(imageBucket,max_seconds_diff=time_gap)
	print "ListOfNewKeys:", len(listOfNewKeys)
	intersetction_files = []
	if( len(listOfNewKeys) > 0 ):
		files_in_bucket = get_all_files(imageBucket)
		existing_imgs = get_existing_indexed_file_list(collection_id)
		
	
		print "Number of files_in_bucket:", len(files_in_bucket)
		print "Existing images:", len(existing_imgs)
	
		intersetction_files = list( set(files_in_bucket) - set(existing_imgs)) ## Get new images
		print "Number of remaining images to be indexed: ", len(intersetction_files)

	## Index these files only.
#	count = 0
	for key in intersetction_files:
		key_extension = key.split(".")[-1]
		print key_extension.lower(), key_extension.lower() in ["jpg", "jpeg", "png", "bmp" ]
		if( key_extension.lower() in ["jpg", "jpeg", "png", "bmp" ] ):
			facerecords = []

			try:
				## Reduce resolution 
				Reduce_resolution(imageBucket, key)
				resp = face_client.index_faces(CollectionId = collection_id , Image = {"S3Object" : {'Bucket' : imageBucket, 'Name' : key}}, ExternalImageId = get_safe_string(key) )
				print "Indexing: ",imageBucket, key
				facerecords = resp['FaceRecords']
			except:
				pass
	
			if( len( facerecords ) == 0 ):
				print "Deleting ", key
				s3_client.delete_object(Bucket=imageBucket, Key=key)

#		count += 1
#		if( count >= 10 ):
#			break;
	print "Mail Dict"
	#Send_mail_to_user( intersetction_files )
	print "Done Indexing all files"

	return 

def DumpFaces(folder_name, jpegFileName,max_faces=100):
	fdata = open( jpegFileName ,"rb").read()
	listOfUrls = SearchIndexByLargestFace(fdata, "", "", "", send_mail=False, max_faces=max_faces)
	image_extension = jpegFileName.split(".")[-1] 
	os.system("cp \""+jpegFileName+"\" "+folder_name+"/"+"selfie."+image_extension)
	for i in range(len(listOfUrls)):
		image_extension = listOfUrls[i].split(".")[-1] 
		os.system("wget "+listOfUrls[i].strip()+" -O "+ folder_name+"/" +"%d.%s"%(i,image_extension))
	return

def SearchIndexByLargestFace(jpegBuf, name, email, phone, send_mail=True, max_faces=40): #Given image name in S3, picks the largest face, retrieves the list of image file names in S3 (Keep it in public folder).
	isFaceFound = False 
	
	try:
		resp = face_client.search_faces_by_image(CollectionId=collection_id,Image={'Bytes': jpegBuf}, MaxFaces=max_faces, FaceMatchThreshold=FACE_MATCH_CUTOFF )
		isFaceFound = True
	except:
		isFaceFound = False
		pass
	if( not isFaceFound ):
		return []
	base_url = "https://s3-eu-west-1.amazonaws.com/"+imageBucket+"/"

#	print "Number of faces matched:", len( resp['FaceMatches'] )
	listOfImages = []
	listOfNewFiles = []
	for i in range(len(resp['FaceMatches'])):
		external_path = resp['FaceMatches'][i]['Face']['ExternalImageId'] 
		if( "@" in get_original_string(external_path) ):
			continue;
		listOfNewFiles.append( get_original_string(external_path))
		fullUrl = base_url + get_original_string( external_path ) 
		listOfImages.append( fullUrl )

	if not os.path.exists(mail_dir):
    		os.makedirs(mail_dir)

	if not os.path.exists(sent_dir):
    		os.makedirs(sent_dir)



	#Save_selfie_and_send_mail( listOfNewFiles, jpegBuf, name, email, phone )
	##Instead of sending mail right away. Dump the required data into pickle.
	mail_dict = {}
	mail_dict["listOfNewFiles"] =  listOfNewFiles
	mail_dict["jpegBuf"] = jpegBuf
	mail_dict["name"] = name
	mail_dict["email"] = email
	mail_dict["phone"] = phone
	if( send_mail ):
		pickle.dump(  mail_dict, open( mail_dir+"/"+str(uuid.uuid4())+"_main.pkl", "wb" ) )

	return listOfImages

def Save_selfie_and_send_mail_pkls(gm):
	listOfPickles = glob.glob(mail_dir+"/*_main.pkl")
 	for i in range(len(listOfPickles)):
		mail_dict = pickle.load( open(listOfPickles[i], "rb") )
		Save_selfie_and_send_mail( mail_dict["listOfNewFiles"], mail_dict["jpegBuf"], mail_dict["name"], mail_dict["email"], mail_dict["phone"] , gm)
		shutil.move( listOfPickles[i], sent_dir )

	listOfPickles = glob.glob(mail_dir+"/*_simple.pkl")
 	for i in range(len(listOfPickles)):
		mail_dict = pickle.load( open(listOfPickles[i], "rb") )
		Send_mail_to_user_simple( mail_dict["listOfNewFiles"], mail_dict["email"], mail_dict["name"] , gm)
		shutil.move( listOfPickles[i], sent_dir )

	
		
def Save_selfie_and_send_mail( listOfNewFiles,  jpegBuf, name, email, phone , gm):
	email = get_safe_string(email)
	db_insert_dict = {"email":get_original_string(email),"name":name, "phone":phone}

	resp = face_client.index_faces(CollectionId = collection_id_selfies ,Image = {"Bytes":jpegBuf}, ExternalImageId = email)
	resp1 = face_client.index_faces(CollectionId = collection_id,Image = {"Bytes":jpegBuf}, ExternalImageId = email)

	db_insert_dict["face_id_selfie"] = resp['FaceRecords'][0]['Face']['FaceId']
	db_insert_dict["face_id_all"] = resp1['FaceRecords'][0]['Face']['FaceId']
	db_insert_dict["marriage_id"] = collection_id

	if not os.path.exists(selfie_dir):
    		os.makedirs(selfie_dir)

	img_file_name = selfie_dir+"/"+email+"___"+db_insert_dict["face_id_selfie"]+".jpg"
	open(img_file_name,"w").write(jpegBuf);

	db.posts.insert_one(db_insert_dict)
	
	Send_mail_to_user_simple( listOfNewFiles , get_original_string(email), name, gm )
	
	return 

def SearchIndexByFaceId(face_id):
	listOfImages = []
	base_url = "https://s3-eu-west-1.amazonaws.com/"+imageBucket+"/"
	resp = face_client.search_faces(CollectionId=collection_id,FaceId=face_id, MaxFaces=40, FaceMatchThreshold=FACE_MATCH_CUTOFF)

	for i in range(len(resp['FaceMatches'])):
		external_path = resp['FaceMatches'][i]['Face']['ExternalImageId'] 
		if( "@" in get_original_string(external_path) ):
			continue;
		fullUrl = base_url + get_original_string(external_path)
		listOfImages.append( fullUrl )

	return listOfImages
	
#SearchIndexByLargestFace("DAY02_02_RNF_YK_WELCOME_DINNER-1293.jpg")
#print SearchIndexByFaceId("91a5c3bc-7ce7-50dd-9a44-0887687def3c")


#files_in_bucket = get_all_files(imageBucket)
#print files_in_bucket
#IndexFacesFromS3Folder(imageBucket)
#Reduce_resolution(imageBucket, "testImage.jpeg")

#for fname in glob.glob("beforedec1/*"):
#	try:
#		folder_name = "selfie_tests/"+str(uuid.uuid4())
#		os.system("mkdir "+folder_name)
#		DumpFaces( folder_name, fname,max_faces=200 )
#	except:
#		continue;
#	
