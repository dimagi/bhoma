function(doc) { 
    if (doc.doc_type == "ExceptionRecord")
    {
        emit(doc.clinic_id, new Date(doc.date), doc);
    }
}