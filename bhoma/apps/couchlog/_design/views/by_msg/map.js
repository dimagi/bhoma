function(doc) { 
    if (doc.doc_type == "ExceptionRecord")
    {
        emit(doc.message, doc);
    }
}