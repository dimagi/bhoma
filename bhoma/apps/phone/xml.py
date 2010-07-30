
RESTOREDATA_TEMPLATE =\
"""<restoredata>
%(inner)s
</restoredata>
"""

REGISTRATION_TEMPLATE = \
"""<n0:registration xmlns:n0="http://openrosa.org/user-registration">
    <username>%(username)s</username>
    <password>%(password)s</password>
    <uuid>%(uuid)s</uuid>
    <date>%(date)s</date>
    <user_data>
        <data key="firstname">%(firstname)s</data>
        <data key="lastname">%(lastname)s</data>
        <data key="sex">%(gender)s</data>
        <data key="clinic_id">%(clinic_id)s</data>
    </user_data>
</n0:registration>"""

def get_registration_xml(chw):
    # TODO: this doesn't feel like a final way to do this
    # date should be formatted like 2010-07-28
    return REGISTRATION_TEMPLATE % {"username": chw.username,
                                    "password": chw.password,
                                    "uuid":     chw.get_id,
                                    "date":     chw.created_on.strftime("%Y-%m-%d"),
                                    "firstname":chw.first_name,
                                    "lastname": chw.last_name,
                                    "gender":   chw.gender,
                                    "clinic_id":chw.current_clinic_id}
    
