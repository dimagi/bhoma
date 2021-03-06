
function wfNewUser() {
    /*
     * Create a new user
     */
    var flow = function (data) {
        
        var user_exists = function(username) {
            var fail_text = "Sorry, the username " + username + " is already taken. Please try a different username.";
            var error_text = "Sorry, something went wrong. I this keeps happening please contact CIDRZ.  Your message is: ";        
            var result = jQuery.ajax({url: '/api/user_exists/', 
					              type: 'POST', 
					              data: {'username': username}, 
					              async: false,
					              success: function(data, textStatus, request) {
	                                    json_res = JSON.parse(data);
                                        if (json_res["result"]) {
					                        request.result = fail_text;
					                    } else {
					                        request.result = null;
					                    }
					                },
					              error: function(request, textStatus, errorThrown) {
					                request.result = error_text + textStatus + " " + errorThrown;
					              }
	                   });
            return result.result;
        };
        
        var userval = function (username) {
            re = new RegExp("^[A-Za-z0-9]+$");
            match = re.exec(username);
            if (match == null) {
                return "User names cannot contain punctuation or spaces";
            } else {
                return user_exists(username);
            }
        }

        var q_username = new wfQuestion({caption: 'Login Name', type: 'str', required: true, validation: userval, domain: 'alpha'});
        yield q_username;
        data['username'] = q_username.value;
        
        var password_format = function (pass) {
            return (pass.length < 4 ? "Passwords must be at least 4 digits" : null);
        };
        var q_password = new wfQuestion({caption: 'Password', type: 'str', required: true, validation: password_format, domain: 'numeric'});
        yield q_password;
        data['password'] = q_password.value;
        
        var q_fname = new wfQuestion({caption: 'First Name', type: 'str', required: true, domain: 'alpha'});
        yield q_fname;
        data['fname'] = q_fname.value;
        
        var q_lname = new wfQuestion({caption: 'Last Name', type: 'str', required: true, domain: 'alpha'});
        yield q_lname;
        data['lname'] = q_lname.value;
        
        var q_role = qRoleList();
        yield q_role;
        data['role'] = q_role.value;
        
    }

    var onFinish = function (data) {
      submit_redirect({result: JSON.stringify(data)});
    }

    return new Workflow(flow, onFinish);
}
