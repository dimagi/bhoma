%% View Function
fun({Doc}) ->
    ClinicMatches = fun(Doc, ClinicId) ->
        case ClinicId of
            null -> false;
            _ ->
                Clinics = proplists:get_value(<<"clinic_ids">>, Doc, null),
                case Clinics of 
                    null ->
                        false;
                    _ ->
                        Found = fun(X) -> X == ClinicId end,
                        lists:any(Found, Clinics) 
                end
        end
    end,
    ZoneMatches = fun(Doc, Zone) ->
        case Zone of 
            null -> false;
            _ ->
                % seriously, you have to dereference this to access it.  That's 
                % what the brackets around doc do above.
                {Addr} = proplists:get_value(<<"address">>, Doc, {null}),
                case Addr of 
                    null -> false;
                    _ ->
                        proplists:get_value(<<"zone">>, Addr, null) == Zone
                end
        end
    end,
    HasOpenPhoneCase = fun(Doc) -> 
        OpenForPhone = fun({Case}) ->
            Closed = proplists:get_value(<<"closed">>, Case, null) == true, 
            SendToPhone =  proplists:get_value(<<"send_to_phone">>, Case, null) == true,
            not Closed and SendToPhone
        end,
        Cases = proplists:get_value(<<"cases">>, Doc, []),
        lists:any(OpenForPhone, Cases)
    end,  
    
    case proplists:get_value(<<"doc_type">>, Doc) of 
        <<"CPatient">> ->
            Clin = <<"5010110">>,
            Zone = 3,
            MeetsSendingCriteria = ClinicMatches(Doc, Clin) and ZoneMatches(Doc, Zone) and HasOpenPhoneCase(Doc),
            case MeetsSendingCriteria of 
                true ->
                    Emit(proplists:get_value(<<"clinic_ids">>, Doc, null), true);
                _ -> ok
            end;
        _ -> ok
    end
end.

%% function(doc, req)
%% {   
%%     
%%     if(!req.query.clinic_id) {
%%         throw("Please provide a query parameter 'clinic_id'.");
%%     }
%%     if(!req.query.zone) {
%%         throw("Please provide a query parameter 'zone'.");
%%     }
%% 
%%         zone = req.query.zone;
%%         clinic_id = req.query.clinic_id;
%%         return (matches_clinic(doc, clinic_id) && matches_zone(doc, zone) && has_open_case_for_phone(doc));
%%     }
%%     return false;
%% }