from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader
import uuid
import tempfile
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
print sys.path
from bhoma.utils.post import post_file

DELETE_DB = False
# server object
server = Server()

if DELETE_DB:
    try:    server.delete_db("patient")
    except: pass

# create database
db = server.get_or_create_db("patient")

# load views
# loader = FileSystemDocsLoader("../apps/xforms/_design")
# loader.sync(db, verbose=True)

filenames = ["data/brac_reg.xml", "data/demo_form.xml", "data/no_uuid_form.xml", "data/no_xmlns_form.xml"] 
for filename in filenames:
    id = uuid.uuid4()
    with open(filename, "rb") as f:
        xml_data = f.read()  
    xml_data = xml_data.replace("REPLACE_ME", str(id))
    tmp_file_path = tempfile.TemporaryFile().name
    try:
        tmp_file = open(tmp_file_path, "w")
        tmp_file.write(xml_data)
    finally:
        tmp_file.close()
    print post_file(tmp_file_path, "http://localhost:5984/patient/_design/xforms/_update/xform/")
