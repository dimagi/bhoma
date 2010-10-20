%% Filter Function
fun({Doc}, Req) ->
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
            ClinicMatches(Doc, Clin) and ZoneMatches(Doc, Zone) and HasOpenPhoneCase(Doc);
        _ -> ok
    end
end.

