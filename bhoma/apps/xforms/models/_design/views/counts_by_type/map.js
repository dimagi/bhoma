function(doc) { 
    if (doc["#doc_type"] == "XForm") 
        emit(doc["@xmlns"], 1); 
}