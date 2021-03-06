
function wfLogin () {
  var flow = function (data) {
    var q_username = qUsernameList();
    yield q_username;
    var username = q_username.value;
    
    //enter password
    var auth_validation = function(password) {
        var auth_fail_text = "Sorry, that is not the right password for " + username + ". Please try again.";
        var error_text = "Sorry, something went wrong. If this keeps happening please contact CIDRZ.  Your message is: ";        
        var auth_res = jQuery.ajax({url: '/api/auth/', 
                                type: 'POST', 
                                data: {'username': username, 'password': password}, 
                                async: false,
                                success: function(data, textStatus, request) {
                                    json_res = JSON.parse(data);
                                    if (json_res["result"]) {
                                        request.result = null;
                                    } else {
                                        request.result = auth_fail_text;
                                    }
                                },
                                error: function(request, textStatus, errorThrown) {
                                    request.result = error_text + textStatus + " " + errorThrown;
                                }
                               });
        return auth_res.result;
    }
    var q_password = new wfQuestion({caption: 'Password', type: 'passwd', required: true, validation: auth_validation, domain: 'numeric'});
    yield q_password;
    
    data["username"] = username;
    data["password"] = q_password.value;
    // once we're here we're authenticated.
    // use onFinish to establish the session in django...
    
  }

  var onFinish = function (data) {
    submit_redirect({result: JSON.stringify(data)});
  }

  return new Workflow(flow, onFinish);
}

