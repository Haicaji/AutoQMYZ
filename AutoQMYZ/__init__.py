import os
import sys


def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_project_path(*parts):
    return os.path.join(get_project_root(), *parts)


from AutoQMYZ.ImitateProcessing.Login import *
from AutoQMYZ.ImitateProcessing.SubmitAnswer import *
from AutoQMYZ.ImitateProcessing.GetQuestion import *
from AutoQMYZ.ImitateProcessing.AfterAnswer import *
from AutoQMYZ.ImitateProcessing.StandardQuestion import *
from AutoQMYZ.ImitateProcessing.IntoAnswerWeb import *
from AutoQMYZ.ImitateProcessing.AntiRobotDetection import *
from AutoQMYZ.GetAnswerProcessing.GetAnswer import *
