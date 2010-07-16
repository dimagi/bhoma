function(doc) { 
    if (doc.doc_type == "CommunityHealthWorker")
        emit(doc._id, doc); 
}