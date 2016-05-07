from .helpers import *

class Pyivle(login.Login, module.Module, consultation.Consultation, rosters_and_groups.RostersAndGroups, announcement.Announcement, forum.Forum, webcast_lectures.WebcastLectures, poll.Poll, workbin.Workbin, gradebook.Gradebook, library_ereserves.LibraryEReserves, my_organizer.MyOrganizer, community.Community, open_webcast_lectures.OpenWebcastLectures, student_events.StudentEvents, ivle_news.IVLENews, timetable.Timetable, delta_datasets.DeltaDatasets, profile.Profile, lesson_plan.LessonPlan):
    def __init__(self, apiKey, authToken=None, **kwargs):
        api.apiKey = apiKey
        if authToken: 
            api.authToken = authToken

    def login(self, userid, password):
        api.authToken = api.get_auth_token(api.apiKey, userid, password)
    
    # Allow user to call custom methods in case of changes to the LAPI
    def call(self, method, auth=True, verb='get', **kwargs):
        return api.call(method, kwargs, auth, verb)

    # Custom API call for downloading files. Downloads from workbin
    # by default.
    def download_file(self, fileid, target='workbin', auth=True):
        return api.download_file(fileid, target, auth)

    def use_namedtuple(self, useNamedtuple):
        api.useNamedtuple = useNamedtuple

    def set_auth_token(self, authToken):
        api.authToken = authToken