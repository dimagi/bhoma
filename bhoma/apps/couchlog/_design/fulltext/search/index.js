function(doc) {
    try {
        if (doc.doc_type == "ExceptionRecord")
        {
            var ret=new Document(); 
            ret.add(doc.message, {"field": "default"}); 
            ret.add(doc.clinic_id, {"field": "clinic"});
            ret.add(doc.date, {"field": "date"}); 
            if (doc.commit_id) {
                ret.add(doc.commit_id, {"field": "commit"});
            }
            if (doc.app_version) {
                ret.add(doc.app_version, {"field": "version"});
            }
            if (doc.url) {
                ret.add(doc.url, {"field": "default"});
            }
            if (doc.type) {
                ret.add(doc.type, {"field": "default"});
            }
            if (doc.archived) {
                ret.add("archived", {"field": "default"});
            }
            if (doc.extra_info) {
                ret.add(doc.extra_info, {"field": "default"});
            } 
            return ret;
        }
    }
    catch (err) {
        // lucene may not be configured, do nothing
    }
    
}