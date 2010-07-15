function(doc) { 
    if (doc.django_type == "profile.bhomauserprofile")
        emit(doc._id, doc.user); 
}