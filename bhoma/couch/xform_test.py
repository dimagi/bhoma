from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader
from post import post
import uuid
import tempfile

DELETE_DB = False
# server object
server = Server()

if DELETE_DB:
    try:    server.delete_db("xform")
    except: pass

# create database
db = server.get_or_create_db("xform")

# load views
loader = FileSystemDocsLoader("./xform_design")
loader.sync(db, verbose=True)

filenames = ["data/brac_reg.xml", "data/demo_form.xml", "data/no_uuid_form.xml", "data/no_xmlns_form.xml"] 
for filename in filenames:
    id = uuid.uuid4()
    xml_data = open(filename, "rb").read()  
    xml_data = xml_data.replace("REPLACE_ME", str(id))
    tmp_file_path = tempfile.TemporaryFile().name
    tmp_file = open(tmp_file_path, "w")
    tmp_file.write(xml_data)
    tmp_file.close()
    post(tmp_file_path, "http://localhost:5984/xform/_design/xform/_update/xform/")
