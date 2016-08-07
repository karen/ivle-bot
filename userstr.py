# Main Bot Strings
#
# Invalid IVLE API token
authenticate='Please authenticate by logging in to IVLE and sending me your token. [/help]'
# /help
help='To get started, please get a token by logging in to IVLE: /login and send it to me: /setup <token>.'
# Describes available commands
helpcmd='Available commands:\n/login\n/setup\n/nextclass\n/classestomorrow\n/announcements\n/gradebook\n/timetable\n/examtime\n\n/credits\n/disclaimer'
# Successfully validated user auth token
setup_true='I\'ll set up your modules now...'
module_ids_not_found='Hmm, have you executed the /setup command? (Please also check that you have spelled each module code correctly.)'

# Bot Helper Strings
validate_true='Great! I\'ve validated your token.'
validate_false='There was an error validating your IVLE token. /login and /setup <token> again. 🙊' 
setup_validate_false='Something went wrong validating your token. Giving up and self-destructing in T-10, 9...'

setup_modules_true='Successfully set up your modules!'
setup_modules_false='Oops, an error occurred while setting up your modules. Popping off to make a sandwich instead. 😢'

gradebook_false='I\'m sorry, an error occurred while retrieving your grades.'

timetable_false='I\'m sorry, an error occurred while retrieving your timetable'
timetable_none='No classes yet! Go party! http://gph.is/11pY1qn'

module_no_exams='There are no exams for the modules specified. Yay!'
exam_timetable_false='I\'m sorry, an error occurred while retrieving the exam timetable'

nextclass_false='I\'m sorry, an error occurred while computing your next class'

classes_tomorrow_wait='Checking if you have a free day tomorrow...'
classes_tomorrow_none='You have no classes tomorrow. Sleep in!'

unread_ann_none='There are no unread announcements.'
unread_ann_false='I\'m sorry, an error occurred retrieving your unread announcements'
recent_ann_false='I\'m sorry, an error occurred retrieving all recent announcements'

# The small stuff
credits='Ingredients: IVLE API, Pyivle, Telepot.\n\nMade because I was lazy and why not? 🌝'
disclaimer='THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. '.lower().capitalize() + 'IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'.lower().capitalize()
fortune1='Be content with what you have; rejoice in the way things are. When you realize there is nothing lacking, the whole world belongs to you.'
fortune2='Nature does not hurry, yet everything is accomplished.'
