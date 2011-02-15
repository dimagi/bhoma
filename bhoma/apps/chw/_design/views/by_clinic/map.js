function(doc) { 
    if (doc.doc_type == "CommunityHealthWorker")
        emit(doc.current_clinic_id, null); 
}