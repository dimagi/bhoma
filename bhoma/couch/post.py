from urlparse import urlparse
import httplib
import subprocess

def post(filename, url,curl_command="curl", use_curl=False,
         content_type = "text/xml"):
    """Do a POST with some options"""     

    up = urlparse(url)
    dict = {}
    try:
        file = open(filename, "rb")
        data = file.read()
        dict["content-type"] = content_type
        dict["content-length"] = len(data)
        if use_curl:
            p = subprocess.Popen([curl_command,
                                  '--header','Content-type:%s' % content_type, 
                                  '--header','"Content-length:%s' % len(data), 
                                  '--data-binary', '@%s' % filename, 
                                  '--request', 'POST', 
                                  url],
                                  stdout=PIPE,stderr=PIPE,shell=False)
            errors = p.stderr.read()
            results = p.stdout.read()
            print "curl gets back:\n%s\nAnd errors:\n%s" % (results, errors)
        else:
            conn = httplib.HTTPConnection(up.netloc)
            conn.request('POST', up.path, data, dict)
            resp = conn.getresponse()
            results = resp.read()
            print "httplib gets back\n%s" % results
    except Exception, e:
        print"problem submitting form: %s" % filename 
        print e
        
