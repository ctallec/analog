from os import listdir
from os.path import join, isdir
from typing import Tuple, Callable, List, Optional, Dict
from datetime import datetime
from analog.logdata import ExperimentLog, RunLog, concat

TimeRange = Tuple[datetime, datetime]
LogPredicate = Callable[[str], ExperimentLog]
DATE_FORMAT = "%Y_%m_%d_%H_%M_%S"

class LoadPredicate:
    """Multiple ways of stating predicates on logs.

    Filter method is directly applied on a dir containing only
    date named directories.
    """
    def __init__(self,
                 time_range: Optional[TimeRange] = None,
                 predicate: Optional[LogPredicate] = None,
                 nb_lasts: Optional[int] = None) -> None:
        self._time_range = time_range
        self._predicate = predicate
        self._nb_lasts = nb_lasts

    def filter(self, date_dir: str) -> ExperimentLog:
        if self._time_range:
            return self._filter_range(date_dir, self._time_range)
        elif self._nb_lasts:
            return self._filter_lasts(date_dir, self._nb_lasts)
        elif self._predicate:
            return self._predicate(date_dir)
        else:
            raise AssertionError

    def _filter_range(self, date_dir: str, time_range: TimeRange) -> ExperimentLog:
        runs: List[RunLog] = []
        dir_date: Dict[str, datetime] = {
            join(date_dir, f): datetime.strptime(f, DATE_FORMAT)
            for f in listdir(date_dir)
        }
        dir_list = [k for k, v in dir_date.items()
                    if v >= time_range[0] and v <= time_range[1]]
        for k in dir_list:
            for f in listdir(k):
                sub_dir = join(k, f)
                if isdir(sub_dir):
                    try:
                        runs.append(RunLog(join(sub_dir, 'args'),
                                           join(sub_dir, 'logs.pkl')))
                    except AssertionError:
                        # When files don't exist, pass
                        pass
        return ExperimentLog(runs)

    def _filter_lasts(self, date_dir: str, nb_lasts: int) -> ExperimentLog:
        runs: List[RunLog] = []
        dir_date: Dict[datetime, str] = {
            datetime.strptime(f, DATE_FORMAT): join(date_dir, f)
            for f in listdir(date_dir)
        }
        keys = sorted(dir_date.keys())[-nb_lasts:]
        dir_list = [dir_date[k] for k in keys]
        for k in dir_list:
            for f in listdir(k):
                sub_dir = join(k, f)
                if isdir(sub_dir):
                    try:
                        runs.append(RunLog(join(sub_dir, 'args'),
                                           join(sub_dir, 'logs.pkl')))
                    except AssertionError:
                        # When files don't exist, pass
                        pass
        return ExperimentLog(runs)

def load(directory: str, predicate: LoadPredicate) -> ExperimentLog:
    sub_dir = listdir(directory)[0]
    try:
        datetime.strptime(sub_dir, DATE_FORMAT)
        return predicate.filter(directory)
    except ValueError:
        exp_log = ExperimentLog([])
        for sub_dir in listdir(directory):
            full_dir = join(directory, sub_dir)
            if isdir(full_dir):
                exp_log = concat(exp_log, load(full_dir, predicate))
        return exp_log
