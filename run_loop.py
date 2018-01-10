import face_search_api as fsa
from time import sleep 
import time

t_gap = 1000000
from send_mail_test2 import Gmail
gm = Gmail('info@reelsandframes.in', 'sk8erboI!m')
restart_gmail_t = time.time()

## Index periodically whenever there are photos in an S3 folder

while (1):
#	Sending mail
	try:
		fsa.Save_selfie_and_send_mail_pkls(gm)
	except:
		continue;

	t_s = time.time()

	try:
		fsa.IndexFacesFromS3Folder("rnf-test-set-1",t_gap)
	except:
		pass
	sleep(2)
	t_gap = int(time.time() - t_s) + 1

	current_gmail_t = time.time()
	try:
		if( (current_gmail_t - restart_gmail_t) > 5*60 ): # #Every 5 minutes, relogin
			gm = Gmail('info@reelsandframes.in', 'sk8erboI!m')
			restart_gmail_t = time.time()
	except:
		pass
		

