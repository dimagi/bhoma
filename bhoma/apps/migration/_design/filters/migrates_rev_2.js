/* 
 * Filter that only returns things that are meant to migrate in rev2
 */

function(doc, req)
{
    return (doc.doc_type == "CommunityHealthWorker" ||          // chws  
            doc.django_type == "profile.bhomauserprofile"       // user profiles
            )
}