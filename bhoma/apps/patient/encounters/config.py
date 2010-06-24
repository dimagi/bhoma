from bhoma.apps.encounter.encounter import EncounterTypeRecord

REGISTRATION_NAMESPACE = "http://openrosa.org/bhoma/registration"
REGISTRATION_SLUG      = "registration"
REGISTRATION_NAME      = "registration"
REGISTRATION_ENCOUNTER = EncounterTypeRecord(REGISTRATION_NAME, REGISTRATION_NAMESPACE, REGISTRATION_NAME)

TEST_NAMESPACE = "http://openrosa.org/bhoma/test"
TEST_SLUG      = "test"
TEST_NAME      = "test form"
TEST_ENCOUNTER = EncounterTypeRecord(TEST_SLUG, TEST_NAMESPACE, TEST_NAME)

ACTIVE_ENCOUNTERS = {
    REGISTRATION_SLUG: REGISTRATION_ENCOUNTER, 
    TEST_SLUG:         TEST_ENCOUNTER
}