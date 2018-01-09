import boto3
import datetime

s3_client = boto3.client('s3')
def get_all_latest_keys(bucketname, max_seconds_diff = 5*60):
	try:
		bucket = s3_client.list_objects(Bucket=bucketname)['Contents']
	except:
		return []
	fresh_key_list = []
	for key in bucket:
		c = datetime.datetime.now() - key['LastModified'].replace(tzinfo=None)
		seconds_diff = c.days * 86400 + c.seconds # Min
		if( seconds_diff < max_seconds_diff ):
			fresh_key_list.append( key["Key"] )
	return fresh_key_list

