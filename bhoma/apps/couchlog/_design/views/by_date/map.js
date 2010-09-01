function(doc) { 
    // find encounters in patients 
    if (doc.doc_type == "ExceptionRecord")
    {
        
        emit(new Date(doc.date), doc);
    }
}