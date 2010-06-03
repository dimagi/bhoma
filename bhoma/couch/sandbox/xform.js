a = function(doc, req) {
    log("ping!")
    var xmlJsonClass = require("util/jsonxml").xmlJsonClass;
    xmlJsonClass.hello()
    if (!doc) {
        doc = {};
    }
    // Workaround: Mozilla Bug 336551
    // see https://developer.mozilla.org/en/E4X
    var content = req.body.replace(/^<\?xml\s+version\s*=\s*(["'])[^\1]+\1[^?]*\?>/, "");
    var xml_content = new XML(content); 
    
    var json = xmlJsonClass.e4x2json(xml_content);
    log("json: " + json);
    
    log("===== Handling submission for type: " + xml_content.*::type + ", name: " + xml_content.name() + ", uri: " + xml_content.uri + " =====");
    
    // Because there is an xmlns in the form we can't reference these normally 
    // like .uuid therefore we have to use the *:: annotation, which searches 
    // every namespace.
    // See: http://dispatchevent.org/roger/using-e4x-with-xhtml-watch-your-namespaces/
    var uuid = xml_content.*::uuid
    
    // TODO: why doesn't this get called?
    if (!uuid || uuid.toString == "") {
        log("no uuid in form, generating one server side.");
        // TODO: find a better guid generator / plug into couch uuid framework
        var guid = function() {
            return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
        }
        uuid = guid();
    }
    
    doc["_id"] = uuid.toString();
    var version = xml_content.@version;
    var uiVersion = xml_content.@uiVersion;
    log("version: " + version + ", uiVersion: " + uiVersion);
    doc["hqVersion"] = version.toString();
    doc["hqUiVersion"] = uiVersion.toString();
    
    var resp =  {"headers" : {"Content-Type" : "text/plain"},
                 "body" : "Thanks for submitting! Id is: " + uuid };
    return [doc, resp];
}

