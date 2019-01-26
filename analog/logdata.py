import pickle as pkl
from os.path import isfile
from typing import Iterable, Dict, Any, Set
from typing import Callable, List

# define an Args type
Args = Dict[str, Any]

def _from_dict(dico: Dict[str, Any]) -> str:
    return ", ".join(f"{str(k)}: {str(v)}" for k, v in dico.items())

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
                # we remove the seed from the args
                # to be able to process multiple logs
                if 'seed' in args:
                    del args['seed']
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
        self.settings: Dict[str, SettingLog] = {}
        for run in runs:
            args = run.args
            if _from_dict(args) in self.settings:
                self.settings[_from_dict(args)].append(run)
            else:
                self.settings[_from_dict(args)] = SettingLog([run])

    def _args_set(self) -> Dict[str, Set[Any]]:
        args_set: Dict[str, Set[Any]] = {}
        for str_args, setting in self.settings.items():
            args = setting.args
            for k, v in args:
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
        for str_args1, setting1 in exp1.settings.items():
            if str_args1 not in self.settings:
                self.settings[str_args1] = SettingLog([])
            self.settings[str_args1].extend(setting1)

def concat(exp1: 'ExperimentLog', exp2: 'ExperimentLog') -> 'ExperimentLog':
    result_exp = ExperimentLog([])
    result_exp.extend(exp1)
    result_exp.extend(exp2)
    return result_exp

def filter(exp: ExperimentLog, predicate: Callable[[Args], bool]) -> ExperimentLog:
    """Filter out settings that do not match the predicate."""
    runs: List[RunLog] = []
    for _, setting in exp.settings.items():
        if predicate(setting.args):
            runs.extend(setting.runs)
    return ExperimentLog(runs)
