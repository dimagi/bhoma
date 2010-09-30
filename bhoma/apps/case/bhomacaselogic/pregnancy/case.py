

def update_pregnancy_cases(patient, encounter):
    return
    # todo
    # assumes the pregnancies have already been updated
    # just sees if this encounter belongs in any of them
    found_preg = None
    for preg in patient.pregnancies:
        if encounter.get_id in preg.encounter_ids:
            found_preg = preg
            break
    