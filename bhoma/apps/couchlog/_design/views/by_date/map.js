function(doc) { 
    if (doc.doc_type == "ExceptionRecord")
    {
        emit(new Date(doc.date), doc);
    }
}