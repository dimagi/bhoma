import sys, os
######################
#POST_URL = "http://localhost:5984/bhoma_test/_design/xforms/_update/xform/"
POST_URL = "http://localhost:8000/a/cory2/receiver/"
#POST_URL = "http://bhoma.dimagi.com/phone/post/"
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dimagi.utils.post import post_file, post_authenticated_file
# path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instances", "chw_follow_test_2.xml")
#path = r"C:\Users\czue\source\bhomalite\bhoma\apps\case\tests\data\bhoma\bhoma_create_chw_follow.xml"
path = r"C:\Users\czue\source\commcare-hq\lib\temp\tempInstance1230017201359950324.xml"
# print post_authenticated_file(path, POST_URL, "admin", "admin")
print post_file(path, POST_URL)
