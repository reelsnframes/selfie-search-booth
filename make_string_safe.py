import bidict
import pickle
import uuid
import os.path
import string
import random

dict_temp_path = "string_convert_bidict.pkl"

def get_rand_string(rstring_len=10):
	return str(uuid.uuid4().hex[:rstring_len].upper())

def get_safe_string(original_string,supported_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"):
	mbidict = bidict.bidict()
	if( os.path.exists(dict_temp_path) ):
		mbidict = pickle.load(open(dict_temp_path,"r"))
	safe_string = original_string;
	for c in original_string:
		if( c in supported_chars ):
			continue;
		if( c not in mbidict.keys() ):
			mbidict[c] = get_rand_string()
		safe_string = safe_string.replace(c,mbidict[c])
	pickle.dump(mbidict, open(dict_temp_path,"w"));
	return safe_string

def get_original_string(safe_string):
	mbidict = bidict.bidict()
	if( os.path.exists(dict_temp_path) ):
		mbidict = pickle.load(open(dict_temp_path,"r"))

	original_string = safe_string
	for k in mbidict.inv.keys():
		original_string = original_string.replace(k,mbidict.inv[k])

	return original_string

#Test case
#fileName = "chetan(copy).jpg"
#print get_original_string( get_safe_string(fileName) )

## Test Code	
# def getCode(length = 10, char = string.ascii_uppercase +
#                           string.digits +           
#                           string.ascii_lowercase ):
#     return ''.join(random.choice( char) for x in range(length))
# 
# for i in range(1000):	
# 	original_string = getCode(length=1000, char="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-/~`!@#$%^&*()_+{}[];:<>,.?/\|"  )  
# 	print get_original_string( get_safe_string(original_string) ) == original_string , original_string
# 
