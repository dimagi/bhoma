function(doc) { 
    if (doc.doc_type == "ExceptionRecord")
    {
        emit(doc.clinic_id, 1);
    }
}