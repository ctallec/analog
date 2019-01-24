import pickle as pkl
from os.path import isfile
from typing import Iterable, Dict, Any, Set
from typing import Callable, List

# define an Args type
Args = Dict[str, Any]

class RunLog:
    """Stores a single run."""
    def __init__(self, args_file: str, logs_file: str) -> None:
        assert isfile(args_file), \
            f"Non existing args file {args_file}."
        assert isfile(logs_file), \
            f"Non existing logs file {logs_file}."

        with open(args_file, 'rb') as f:
            args = pkl.load(f)
            if not isinstance(args, dict):
                args = vars(args)
                self.args = args

        self._logs_file = logs_file
        self._logs: Any = None

    @property
    def logs(self):
        """Only load logs when needed."""
        with open(self._logs_file, 'rb') as f:
            self._logs = pkl.load(f)
        return self._logs

class SettingLog:
    """Stores several runs with the same setting (args)."""
    def __init__(self, runs: Iterable[RunLog]) -> None:
        self.args = next(iter(runs)).args
        assert all(run.args == self.args for run in runs), \
            "Not all runs have the same args."
        self.runs = list(runs)

    def append(self, run: RunLog):
        assert run.args == self.args, \
            "Appended run does not have the same args."
        self.runs.append(run)

    def extend(self, settings: 'SettingLog'):
        for r in settings.runs:
            self.append(r)

class ExperimentLog:
    """Stores a whole experiment as a disctionary of settings."""
    def __init__(self, runs: Iterable[RunLog]) -> None:
        self.settings: Dict[Args, SettingLog] = {}
        for run in runs:
            args = run.args
            if args in self.settings:
                self.settings[args].append(run)
            else:
                self.settings[args] = SettingLog([run])

    def _args_set(self) -> Dict[str, Set[Any]]:
        args_set: Dict[str, Set[Any]] = {}
        for args in self.settings:
            for k, v in args.items():
                if k not in args_set:
                    args_set[k] = set()
                args_set[k].add(v)
        return args_set

    @property
    def delta_args(self):
        return {k: v_set for k, v_set in self._args_set.items() if len(v_set) > 1}

    @property
    def shared_args(self):
        return {k: v_set.pop() for k, v_set in self._args_set.items()
                if len(v_set) == 1}

    def extend(self, exp1: 'ExperimentLog'):
        for args in exp1.settings:
            if args not in self.settings:
                self.settings[args] = SettingLog([])
            self.settings[args].extend(exp1.settings[args])

def concat(exp1: 'ExperimentLog', exp2: 'ExperimentLog') -> 'ExperimentLog':
    result_exp = ExperimentLog([])
    result_exp.extend(exp1)
    result_exp.extend(exp2)
    return result_exp

def filter(exp: ExperimentLog, predicate: Callable[[Args], bool]) -> ExperimentLog:
    """Filter out settings that do not match the predicate."""
    runs: List[RunLog] = []
    for args, setting in exp.settings.items():
        if predicate(args):
            runs.extend(setting.runs)
    return ExperimentLog(runs)
