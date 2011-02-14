function(doc) { 
    if (doc.doc_type == "ExceptionRecord" && !doc.archived)
    {
        emit(doc.message, doc);
    }
}