import os
from pyivle.pyivle import Pyivle
from models import User, Module
import datetime
import html_stripper
import userstr

API_KEY = os.environ['API_KEY']
auth_token = None
IVLE = Pyivle(API_KEY)

MODULE_ID_NULL_STRING='00000000-0000-0000-0000-000000000000'

async def do(auth_token, func, params={}):
    IVLE.set_auth_token(auth_token)
    try:
        response = IVLE.validate()
        if not response.Success:
            return userstr.validate_false, False
    except:
        return userstr.validate_false, False
    return func(**params)

def setup_user(user, auth_token):
    try:
        response = IVLE.validate()
        if response.Success:
            user.auth_token = auth_token
            user.save()
        return (userstr.validate_true, True) if response.Success else (userstr.setup_validate_false, False)
    except Exception as e:
        print(e)
        return (userstr.setup_validate_false, False)

def setup_modules():
    try:
        response = IVLE.modules(includeAllInfo=False)
        module_list = []
        for module in response.Results:
            mod, _ = Module.get_or_create(module_code=module.CourseCode, acad_year=module.CourseAcadYear, semester=int(module.CourseSemester[-1]), defaults={'module_id': module.ID})
            if mod.module_id is None or mod.module_id == '':
                mod.module_id = MODULE_ID_NULL_STRING
            mod.save()
        return (userstr.setup_modules_true, True)
    except Exception as e:
        print(e)
        return (userstr.setup_modules_false, False)

def get_gradebook(module_code, module_id):
    try:
        response = IVLE.gradebook_view_items(module_id)
        gradebook_items = {}
        for category in response.Results:
            processed_category = ''.join(map(__process_gradebook_item, category.Items))
            title = category.CategoryTitle + '\n##########\n'
            gradebook_items[title] = processed_category
        result = []
        for category, v in gradebook_items.items():
            result.append(category)
            result.append(v)
        success = 'Here are your grades for {}:\n\n'.format(module_code) + ''.join(result)
        return (success, True)
    except Exception as e:
        print(e)
        return (userstr.gradebook_false, False)
    
def __process_gradebook_item(item):
    result = []
    if not item.MarksObtained and not item.Grade:
        return ''
    grade = item.MarksObtained if item.MarksObtained else item.Grade
    result.append(item.ItemName + ': ' + grade + '\n')
    result.append('Highest-Lowest: ' + item.HighestLowestMarks + '\n')
    result.append('Average-Median: ' + item.AverageMedianMarks + '\n')
    result.append('Percentile: ' + item.Percentile + '\n')
    return ''.join(result) + '\n'

def get_timetable(modules):
    try:
        all_module_timetables = get_unformatted_timetable(modules)
        all_module_timetables = list(map(strf_timetable, all_module_timetables))
        success = ''.join(all_module_timetables)
        return (success, True) if success else (userstr.timetable_none, True)
    except Exception as e:
        print(e)
        return (userstr.gradebook_false, False)

def get_unformatted_timetable(modules, merged=False):
    try:
        result = []
        for m_id in modules:
            module_timetable = IVLE.timetable_student_module(m_id).Results
            if merged:
                result.extend(module_timetable)
            else:
                result.append(module_timetable)
        return result
    except Exception as e:
        print(e)
        return []

def strf_timetable(module_timetable):
    result = []
    if module_timetable:
        result.append(module_timetable[0].ModuleCode + ':\n')
        for lesson in module_timetable:
            result.append(lesson.DayText + ' ')
            result.append(lesson.LessonType.lower() + ' from ')
            result.append(lesson.StartTime + ' to ')
            result.append(lesson.EndTime + ' at ')
            result.append(lesson.Venue + '\n')
        result.append('\n')
    return ''.join(result)

def get_exam_timetable(modules):
    try:
        all_module_timetables = []
        for m_id in modules:
            timetables = IVLE.timetable_module_exam(m_id).Results
            all_module_timetables.append(strf_exam_timetable(timetables))
        success = ''.join(all_module_timetables)
        return (success, True) if len(success) else (userstr.module_no_exams, True)
    except Exception as e:
        print(e)
        return (userstr.exam_timetable_false, False)

def strf_exam_timetable(module_timetable):
    if not module_timetable:
        return ''
    result = []
    result.append(module_timetable[0].ModuleCode + '\'s exam is on ')
    exam_dates = set()
    for exam in module_timetable:
        exam_dates.add(exam.ExamInfo + '\n')
    for exam in exam_dates:
        result.append(exam)
    result.append('\n')
    return ''.join(result)

def get_next_class():
    try:
        simplified_lessons, result = _sort_lessons(_get_all_lessons())
        classesIdx = _get_next_classes(simplified_lessons)
        if not classesIdx:
            lessons = map(strf_lesson, map(lambda idx: result[idx], classesIdx))
            if len(lessons) == 1:
                success = 'Your next class is: ' + lessons[0]
            else:
                success = 'Your next classes are: ' + '\n'.join(lessons)
            return (success, True)
        return (userstr.nextclass_false, False)
    except Exception as e:
        print(e)
        return (userstr.nextclass_false, False)

def _get_all_lessons():
    results = IVLE.modules(includeAllInfo=False).Results
    module_ids = list(map(lambda mod: mod.ID, results))
    return get_unformatted_timetable(module_ids, merged=True)

def _sort_lessons(all_lessons):
    today = datetime.date.today().isoweekday()
    lessons = []
    for i in range(len(all_lessons)):
        l = all_lessons[i]
        lesson_day = int(l.DayCode)
        lesson_day = lesson_day if lesson_day >= today else lesson_day + 7
        triplet = (lesson_day, l.StartTime, i)
        lessons.append(triplet)
    lessons = sorted(lessons, key=lambda l: l[1])
    lessons = sorted(lessons, key=lambda l: l[0])
    result = []
    for l in lessons:
        result.append(all_lessons[l[2]])
    return (lessons, result)

def _get_next_classes(lesson_triplets):
    candidateClassesIdx = []
    next_class_day = None
    next_class_time = None
    for i in range(len(lesson_triplets)):
        today = datetime.date.today().isoweekday()
        time_now = datetime.datetime.now().strftime('%H%M')
        lesson = lesson_triplets[i]
        day, time = lesson[0], lesson[1]
        if (day == today and int(time) >= int(time_now)) or (day > today):
            if not candidateClassesIdx:
                candidateClassesIdx.append(i)
                next_class_day = day
                next_class_time = time
            elif day == next_class_day and time == next_class_time:
                candidateClassesIdx.append(i)
            else:
                break
    return candidateClassesIdx

def strf_lesson(lesson):
    result = []
    result.append(lesson.ModuleCode + ' ')
    result.append(lesson.LessonType.lower() + ' at ')
    result.append(lesson.Venue + ' on ')
    result.append(lesson.DayText + ', ')
    result.append(lesson.StartTime)
    return ''.join(result)

def get_classes_tomorrow():
    today = datetime.date.today().isoweekday()
    if today == 5:
        return ('TGIF! No classes!', True)
    elif today == 6:
        return ('It\'s the weekend...', True)
    try:
        tomorrow = (today + 1) % 7
        classes_tomorrow = '\n'.join(map(strf_lesson, filter(lambda l: int(l.DayCode) == tomorrow, _get_all_lessons())))
        return (userstr.classes_tomorrow_describe + classes_tomorrow, True) if classes_tomorrow else (userstr.classes_tomorrow_none, True)
    except Exception as e:
        print(e)
        return (failure, False)

def get_unread_ann():
    try:
        results = {}
        res = IVLE.announcements_unread().Results
        for r in res:
            results[r.CourseCode] = (strf_announcements(r.Announcements, True))
        return (results, True) if results else (userstr.unread_ann_none, True)
    except Exception as e:
        print(e)
        return (userstr.unread_ann_false, False)

def strf_announcements(announcements, mark_read=False):
    results = []
    for i in range(len(announcements)):
        if mark_read:
            IVLE.announcements_add_log(announcements[i].ID)
        results.append('#{}: '.format(i+1) + datetime.datetime.strptime(announcements[i].CreatedDate_js, '%Y-%m-%dT%H:%M:%S').strftime('%H:%M on %a, %d-%m-%y \n') + announcements[i].Title + '\n' + html_stripper.strip_tags(announcements[i].Description))
    return '\n'.join(results)

def get_recent_ann(module_code, count, duration=0):
    try:
        course_id = Module.select(Module.module_id). \
        where(Module.module_code.contains(module_code)). \
        order_by(Module.acad_year.desc(), Module.semester.desc()). \
        get().module_id

        results = strf_announcements(IVLE.announcements(courseId=course_id, duration=duration).Results[:count])
        return (results, True) if results else ('There are no announcements for {}'.format(module_code), True)
    except Exception as e:
        print(e)
        return (userstr.recent_ann_false, False)
