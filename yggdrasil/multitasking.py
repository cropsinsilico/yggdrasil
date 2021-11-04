import os
import sys
import six
import atexit
import weakref
import logging
import threading
import queue
import multiprocessing
import asyncio
from yggdrasil.tools import YggClass, sleep
MPI = None
_on_mpi = False
_mpi_rank = -1
if os.environ.get('YGG_SUBPROCESS', False):
    if 'YGG_MPI_RANK' in os.environ:
        _on_mpi = True
        _mpi_rank = int(os.environ['YGG_MPI_RANK'])
else:
    try:
        from mpi4py import MPI
        _on_mpi = (MPI.COMM_WORLD.Get_size() > 1)
        _mpi_rank = MPI.COMM_WORLD.Get_rank()
    except ImportError:
        pass


mp_ctx = multiprocessing.get_context()
mp_ctx_spawn = multiprocessing.get_context("spawn")
_main_thread = threading.main_thread()
_thread_registry = weakref.WeakValueDictionary()
_lock_registry = weakref.WeakValueDictionary()
logger = logging.getLogger(__name__)


def test_target_error():  # pragma: debug
    raise RuntimeError("Test error.")


def test_target_sleep():  # pragma: debug
    sleep(10.0)


def check_processes():  # pragma: debug
    r"""Check for processes that are still running."""
    import psutil
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    if len(children) > 0:
        logging.info("Process %s has %d children" % (
            current_process.pid, len(children)))
        for child in children:
            logger.info("    %s process running" % child.pid)


def check_threads():  # pragma: debug
    r"""Check for threads that are still running."""
    # logger.info("Checking %d threads" % len(_thread_registry))
    for k, v in _thread_registry.items():
        if v.is_alive():
            logger.error("Thread is alive: %s" % k)
    if threading.active_count() > 1:
        logger.info("%d threads running" % threading.active_count())
        for t in threading.enumerate():
            logger.info("    %s thread running" % t.name)


def check_locks():  # pragma: debug
    r"""Check for locks in lock registry that are locked."""
    # logger.info("Checking %d locks" % len(_lock_registry))
    for k, v in _lock_registry.items():
        res = v.acquire(False)
        if res:
            v.release()
        else:
            logger.error("Lock could not be acquired: %s" % k)


def check_sockets():  # pragma: debug
    r"""Check registered sockets."""
    from yggdrasil.communication import cleanup_comms
    count = cleanup_comms('ZMQComm')
    if count > 0:
        logger.info("%d sockets closed." % count)


def ygg_atexit():  # pragma: debug
    r"""Things to do at exit."""
    check_locks()
    check_threads()
    # # This causes a segfault in a C dependency
    # if not is_subprocess():
    #     check_sockets()
    # Python 3.4 no longer supported if using pip 9.0.0, but this
    # allows the code to work if somehow installed using an older
    # version of pip
    if sys.version_info[0:2] == (3, 4):  # pragma: no cover
        # Print empty line to ensure close
        print('', end='')
        sys.stdout.flush()


atexit.register(ygg_atexit)


class SafeThread(threading.Thread):
    r"""Thread that sets Event on error."""

    def __init__(self, *args, **kwargs):
        self._errored = threading.Event()
        super(SafeThread, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        try:
            super(SafeThread, self).run(*args, **kwargs)
        except BaseException:
            self._errored.set()
            raise

    @property
    def exitcode(self):
        r"""int: Exit code. 1 if error, 0 otherwise."""
        if (not self._started.is_set()) or self.is_alive():
            return None
        return int(self._errored.is_set())

    @property
    def pid(self):
        r"""Process ID."""
        return os.getpid()


class AliasDisconnectError(RuntimeError):
    pass


def add_aliased_attribute(cls, name, with_lock=False):
    r"""Factory to alias an attribute so that it refers to the wrapped
    object.

    Args:
        name (str): Name of attribute to alias.
        with_lock (bool, optional): If True, the class's lock will be
            acquired before getting the attribute. Defaults to False.

    """
    def alias_wrapper(self):
        self.check_for_base(name)
        lock_acquired = False
        if ((with_lock and hasattr(self, 'lock')
             and (name not in self._unlocked_attr))):
            self.lock.acquire()
            lock_acquired = True
        try:
            out = getattr(self._base, name)
        finally:
            if lock_acquired:
                self.lock.release()
        return out
    alias_wrapper.__name__ = name
    setattr(cls, name, property(alias_wrapper))


def add_aliased_method(cls, name, with_lock=False):
    r"""Factory to alias a method so that it refers to the wrapped
    object.

    Args:
        name (str): Name of method to alias.
        with_lock (bool, optional): If True, the class's lock will be
            acquired before executing the method. Defaults to False.

    """
    def alias_wrapper(self, *args, **kwargs):
        self.check_for_base(name)
        lock_acquired = False
        if ((with_lock and hasattr(self, 'lock')
             and (name not in self._unlocked_attr))):
            self.lock.acquire()
            lock_acquired = True
        try:
            out = getattr(self._base, name)(*args, **kwargs)
        finally:
            if lock_acquired:
                self.lock.release()
        return out
    alias_wrapper.__name__ = name
    setattr(cls, name, alias_wrapper)


class AliasMeta(type):
    r"""Meta class for adding aliased methods to the class."""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        for k in cls._base_meth:
            assert(not hasattr(cls, k))
            add_aliased_method(cls, k, with_lock=cls._base_locked)
        for k in cls._base_attr:
            assert(not hasattr(cls, k))
            add_aliased_attribute(cls, k, with_lock=cls._base_locked)
        cls._base_meth = []
        cls._base_attr = []
        if (cls._base_class_name is None) and (name not in ['AliasObject',
                                                            'MultiObject',
                                                            'ContextObject']):
            cls._base_class_name = name
        return cls


@six.add_metaclass(AliasMeta)
class AliasObject(object):
    r"""Alias object that calls to attribute.

    Args:
        dont_initialize_base (bool, optional): If True the base object
            will not be initialized. Defaults to False.

    """

    __slots__ = ['_base', '__weakref__']
    _base_class_name = None
    _base_class = None
    _base_attr = []
    _base_meth = []
    _base_locked = False
    _unlocked_attr = []

    def __init__(self, *args, dont_initialize_base=False, **kwargs):
        self._base = None
        if (not dont_initialize_base) and (self._base_class is not None):
            self._base = self._base_class(*args, **kwargs)

    @classmethod
    def from_base(cls, base, *args, **kwargs):
        r"""Create an instance by creating a based from the provided
        base class."""
        if base is not None:
            kwargs['dont_initialize_base'] = True
            out = cls(*args, **kwargs)
            out._base = base
        else:
            out = cls(*args, **kwargs)
        return out

    def __getstate__(self):
        out = dict()
        
        def add_base_slots(base):
            out.update(
                dict((slot, getattr(self, slot))
                     for slot in base.__slots__
                     if (hasattr(self, slot)
                         and (slot not in ['_base_class', '__weakref__'])
                         and (slot not in out))))
            for x in base.__bases__:
                if x != object:
                    add_base_slots(x)
        add_base_slots(self.__class__)
        return out

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    def check_for_base(self, attr):
        r"""Raise an error if the aliased object has been disconnected."""
        if self._base is None:
            raise AliasDisconnectError(
                ("Aliased object has been disconnected so "
                 "'%s' is no longer available.") % attr)

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        return None

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        if self._base is not None:
            dummy = self.dummy_copy
            del self._base
            self._base = dummy

    def __del__(self):
        self.disconnect()

        
class MultiObject(AliasObject):
    r"""Concurrent/parallel processing object using either threads
    or processes."""

    __slots__ = ['task_method', 'parallel']

    def __init__(self, *args, task_method="threading", **kwargs):
        self.task_method = task_method
        if task_method in ["thread", "threading", "concurrent"]:
            self.parallel = False
        elif task_method in ["process", "multiprocessing", "parallel"]:
            self.parallel = True
        else:  # pragma: debug
            raise ValueError(("Unsupported method for concurrency/"
                              "parallelism: '%s'") % task_method)
        super(MultiObject, self).__init__(*args, **kwargs)


class Context(MultiObject):
    r"""Context for managing threads/processes."""

    def __init__(self, task_method='thread', dont_initialize_base=False):
        super(Context, self).__init__(dont_initialize_base=True,
                                      task_method=task_method)
        if not dont_initialize_base:
            if self.parallel:
                self._base = mp_ctx_spawn
            else:
                self._base = threading

    def __getstate__(self):
        state = super(Context, self).__getstate__()
        if self.parallel:
            state['_base'] = state['_base']._name
        else:
            state['_base'] = None
        return state

    def __setstate__(self, state):
        if state['_base'] is None:
            state['_base'] = threading
        else:
            # Use the existing context?
            # state['_base'] = mp_ctx_spawn
            state['_base'] = multiprocessing.get_context(state['_base'])
        super(Context, self).__setstate__(state)

    def RLock(self, *args, **kwargs):
        r"""Get a recursive lock in this context."""
        kwargs['task_context'] = self
        return RLock(*args, **kwargs)

    def Event(self, *args, **kwargs):
        r"""Get an event in this context."""
        kwargs['task_context'] = self
        return Event(*args, **kwargs)

    def Task(self, *args, **kwargs):
        r"""Get a task in this context."""
        kwargs['task_context'] = self
        return Task(*args, **kwargs)

    def Queue(self, *args, **kwargs):
        r"""Get a queue in this context."""
        kwargs['task_context'] = self
        return Queue(*args, **kwargs)

    def Dict(self, *args, **kwargs):
        r"""Get a shared dictionary in this context."""
        kwargs['task_context'] = self
        return Dict(*args, **kwargs)

    def current_task(self):
        r"""Current task (process/thread)."""
        if self.parallel:
            return self._base.current_process()
        else:
            return self._base.current_thread()

    def main_task(self):
        r"""Main task (process/thread)."""
        if self.parallel:
            out = None
            if hasattr(self._base, 'parent_process'):  # pragma: no cover
                out = self._base.parent_process()
            if out is None:
                out = self.current_task()
            return out
        else:
            return _main_thread


class DummyContextObject(object):  # pragma: no cover

    __slots__ = []

    @property
    def context(self):
        return None

    def disconnect(self):
        pass


class ContextObject(MultiObject):
    r"""Base class for object intialized in a context."""

    __slots__ = ["_managed_context", "_context", "_base_class"]

    def __init__(self, *args, task_method='threading',
                 task_context=None, **kwargs):
        self._managed_context = None
        if task_context is None:
            task_context = Context(task_method=task_method)
            self._managed_context = task_context
        elif isinstance(task_context, weakref.ReferenceType):
            task_context = task_context()
        task_method = task_context.task_method
        self._context = weakref.ref(task_context)
        self._base_class = self.get_base_class(task_context)
        if ((self._base_class
             and isinstance(self._base_class, type)
             and issubclass(self._base_class, (LockedObject, ContextObject)))):
            kwargs['task_context'] = task_context
        super(ContextObject, self).__init__(
            *args, task_method=task_method, **kwargs)

    def __getstate__(self):
        state = super(ContextObject, self).__getstate__()
        state['_context'] = None
        return state

    def __setstate__(self, state):
        if state['_managed_context'] is None:
            state['_managed_context'] = Context(task_method=state['task_method'])
        state['_context'] = weakref.ref(state['_managed_context'])
        super(ContextObject, self).__setstate__(state)
        
    @classmethod
    def get_base_class(cls, context):
        r"""Get instance of base class that will be represented."""
        name = cls._base_class_name
        context.check_for_base(name)
        return getattr(context._base, name)

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        if ContextObject is not None:
            super(ContextObject, self).disconnect()
        if self._managed_context is not None:
            self._managed_context.disconnect()
            self._managed_context = None

    @property
    def context(self):
        r"""Context: Context used to create this object."""
        return self._context()


class DummyRLock(DummyContextObject):  # pragma: no cover

    def acquire(self, *args, **kwargs):
        pass

    def release(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        pass
    

class RLock(ContextObject):
    r"""Recursive lock. Acquiring the lock after disconnect is called
    through use as a context will not raise an error, but will not
    do anything."""

    _base_meth = ['acquire', 'release', '__enter__', '__exit__']

    def __getstate__(self):
        state = super(RLock, self).__getstate__()
        if (not self.parallel) and (not isinstance(state['_base'], DummyRLock)):
            state['_base'] = None
        return state

    def __setstate__(self, state):
        if state['_base'] is None:
            state['_base'] = threading.RLock()
        super(RLock, self).__setstate__(state)

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        return DummyRLock()


class DummyEvent(DummyContextObject):  # pragma: no cover

    __slots__ = ["_value"]

    def __init__(self, value=False):
        self._value = value

    def is_set(self):
        return self._value

    def set(self):
        self._value = True

    def clear(self):
        self._value = False

    def wait(self, *args, **kwargs):
        if self._value:
            return
        raise AliasDisconnectError("DummyEvent will never change to True.")


class ProcessEvent(object):
    r"""Multiprocessing/threading event associated with a process that has
    a discreet start and end."""

    __slots__ = ["started", "stopped"]

    def __init__(self, *args, **kwargs):
        self.started = Event(*args, **kwargs)
        self.stopped = Event(task_context=self.started.context)

    def start(self):
        r"""Set the started event."""
        self.started.set()

    def stop(self):
        r"""Set the stopped event."""
        self.stopped.set()

    def has_started(self):
        r"""bool: True if the process has started."""
        return self.started.is_set()

    def has_stopped(self):
        r"""bool: True if the process has stopped."""
        return self.stopped.is_set()

    def is_running(self):
        r"""bool: True if the processes has started, but hasn't stopped."""
        return (self.has_started() and (not self.has_stopped()))


class Event(ContextObject):
    r"""Multiprocessing/threading event."""

    __slots__ = ["_set", "_clear", "_set_callbacks", "_clear_callbacks"]
    _base_attr = ContextObject._base_attr + ['is_set', 'wait']

    def __init__(self, *args, **kwargs):
        self._set = None
        self._clear = None
        self._set_callbacks = []
        self._clear_callbacks = []
        super(Event, self).__init__(*args, **kwargs)
        self._set = self._base.set
        self._clear = self._base.clear

    def set(self):
        r"""Set the event."""
        self._set()
        for (x, a, k) in self._set_callbacks:
            x(*a, **k)

    def clear(self):
        r"""Clear the event."""
        self._clear()
        for (x, a, k) in self._clear_callbacks:
            x(*a, **k)

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        return DummyEvent(self._base.is_set())
        
    def __getstate__(self):
        state = super(Event, self).__getstate__()
        if not self.parallel:
            state.pop('_set')
            state.pop('_clear')
            state['_base'] = state['_base'].is_set()
        return state

    def __setstate__(self, state):
        if isinstance(state['_base'], bool):
            val = state['_base']
            state['_base'] = threading.Event()
            state['_set'] = state['_base'].set
            state['_clear'] = state['_base'].clear
            if val:
                state['_base'].set()
        super(Event, self).__setstate__(state)

    # @classmethod
    # def from_event_set(cls, *events):
    #     r"""Create an event that is triggered when any one of the provided
    #     events is set.

    #     Args:
    #         *events: One or more events that will trigger this event.

    #     """
    #     # Modified version of https://stackoverflow.com/questions/12317940/
    #     # python-threading-can-i-sleep-on-two-threading-events-simultaneously/
    #     # 36661113
    #     or_event = cls()

    #     def changed():
    #         bools = [e.is_set() for e in events]
    #         if any(bools):
    #             or_event.set()
    #         else:
    #             or_event.clear()
    #     for e in events:
    #         e.add_callback(changed, trigger='set')
    #         e.add_callback(changed, trigger='clear')
    #     return or_event

    def add_callback(self, callback, args=(), kwargs={}, trigger='set'):
        r"""Add a callback that will be called when set or clear is invoked.

        Args:
            callback (callable): Callable executed when set is called.
            args (tuple, optional): Arguments to pass to the callback.
            kwargs (dict, optional): Keyword arguments to pass to the
                callback.
            trigger (str, optional): Action triggering the set call.
                Options are 'set' or 'clear'. Defaults to 'set'.

        """
        getattr(self, f'_{trigger}_callbacks').append(
            (callback, args, kwargs))

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        if Event is not None:
            super(Event, self).disconnect()
            self._set = self._base.set
            self._clear = self._base.clear


class ValueEvent(Event):
    r"""Class for handling storing a value that also triggers an event."""

    __slots__ = ["_event_value"]

    def __init__(self, *args, **kwargs):
        self._event_value = None
        super(ValueEvent, self).__init__(*args, **kwargs)

    def set(self, value=None):
        self._event_value = value
        super(ValueEvent, self).set()

    def clear(self):
        self._event_value = None
        super(ValueEvent, self).clear()

    def get(self):
        return self._event_value


class DummyTask(DummyContextObject):  # pragma: no cover

    __slots__ = ["name", "exitcode", "daemon"]

    def __init__(self, name='', exitcode=0, daemon=False):
        self.name = name
        self.exitcode = exitcode
        self.daemon = daemon
        super(DummyTask, self).__init__()

    def join(self, *args, **kwargs):
        return

    def is_alive(self):
        return False

    def terminate(self):
        pass

    def kill(self):
        pass
    

class Task(ContextObject):
    r"""Multiprocessing/threading process."""

    __slots__ = ["_target", "_args", "_kwargs"]
    _base_attr = ['name', 'daemon', 'authkey', 'sentinel', 'exitcode', 'pid']
    _base_meth = ['start', 'run', 'join',
                  # Thread only
                  'getName', 'setName', 'isDaemon', 'setDaemon',
                  # Process only
                  'terminate']

    def __init__(self, target=None, args=(), kwargs={}, **kws):
        self._target = target
        self._args = args
        self._kwargs = kwargs
        if self._target is not None:
            kws['target'] = self.target
        super(Task, self).__init__(**kws)

    @classmethod
    def get_base_class(cls, context):
        r"""Get instance of base class that will be represented."""
        if context.parallel:
            return context._base.Process
        else:
            return SafeThread

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        name = b'dummy'
        exitcode = 0
        daemon = False
        try:
            name = self._base.name
            exitcode = self._base.exitcode
            daemon = self._base.daemon
        except AttributeError:  # pragma: debug
            pass
        return DummyTask(name=name, exitcode=exitcode, daemon=daemon)
        
    def __getstate__(self):
        state = super(Task, self).__getstate__()
        if not self.parallel:
            state['_base'] = {
                'name': state['_base'].name, 'group': None,
                'daemon': state['_base'].daemon,
                'target': state['_base']._target,
                'args': state['_base']._args,
                'kwargs': state['_base']._kwargs}
        return state

    def __setstate__(self, state):
        if isinstance(state['_base'], dict):
            state['_base'] = SafeThread(**state['_base'])
        super(Task, self).__setstate__(state)

    def is_alive(self):
        r"""Determine if the process/thread is alive."""
        out = self._base.is_alive()
        if out is None:  # pragma: debug
            out = False
        return out

    @property
    def ident(self):
        r"""Process ID."""
        if self.parallel:
            return self._base.pid
        else:
            return self._base.ident

    def target(self, *args, **kwargs):
        r"""Run the target."""
        try:
            self._initialize()
            self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self._on_error(e)
        finally:
            self._finalize()
            
    def _initialize(self):
        r"""Initialize a run."""
        pass

    def _finalize(self):
        r"""Finalize a run."""
        pass

    def _on_error(self, e):
        r"""Handle an error during a run."""
        raise
        
    def kill(self, *args, **kwargs):
        r"""Kill the task."""
        if self.parallel and hasattr(self._base, 'kill'):
            return self._base.kill(*args, **kwargs)
        elif hasattr(self._base, 'terminate'):
            return self._base.terminate(*args, **kwargs)

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        self._target = None
        if Task is not None:
            super(Task, self).disconnect()


class TaskLoop(Task):
    r"""Class for looping over a task."""

    __slots__ = ["break_flag", "polling_interval", "break_stack",
                 "_loop_target", "_loop_count"]

    def __init__(self, target=None, polling_interval=0.0, **kws):
        self.polling_interval = polling_interval
        self.break_stack = None
        self._loop_target = target
        self._loop_count = 0
        if self._loop_target is not None:
            kws['target'] = self.loop_target
        super(TaskLoop, self).__init__(**kws)
        self.break_flag = Event(task_context=self._context)

    def break_loop(self, break_stack=None):
        r"""Break the task loop."""
        if self.break_stack is None:
            if break_stack is None:
                import traceback
                break_stack = ''.join(traceback.format_stack())
            self.break_stack = break_stack
        self.break_flag.set()

    def kill(self, *args, **kwargs):
        r"""Kill the task."""
        self.break_loop()
        return super(TaskLoop, self).kill(*args, **kwargs)

    def loop_target(self, *args, **kwargs):
        r"""Continue calling the target until the loop is broken."""
        while not self.break_flag.is_set():
            try:
                self._loop_target(*args, **kwargs)
            except BreakLoopException as e:
                self.break_loop(e.break_stack)
                break
            if self.polling_interval:
                self.break_flag.wait(self.polling_interval)
            self._loop_count += 1

    def _finalize(self):
        r"""Finalize a run."""
        self.break_loop()

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        self.break_flag.disconnect()
        self._loop_target = None
        if TaskLoop is not None:
            super(TaskLoop, self).disconnect()


class DummyQueue(DummyContextObject):  # pragma: no cover

    def empty(self):
        return True

    def full(self):
        return False

    def get(self, *args, **kwargs):
        raise AliasDisconnectError("There are no messages in a DummyQueue.")

    def get_nowait(self, *args, **kwargs):
        raise AliasDisconnectError("There are no messages in a DummyQueue.")

    def put(self, *args, **kwargs):
        raise AliasDisconnectError("Cannot put messages in a DummyQueue.")

    def put_nowait(self, *args, **kwargs):
        raise AliasDisconnectError("Cannot put messages in a DummyQueue.")

    def qsize(self):
        return 0

    def join(self, *args, **kwargs):
        return

    def join_thread(self, *args, **kwargs):
        return
    
    def close(self):
        pass


class Queue(ContextObject):
    r"""Multiprocessing/threading queue."""

    _base_meth = ['full', 'get', 'get_nowait', 'join_thread', 'qsize']
    
    @classmethod
    def get_base_class(cls, context):
        r"""Get instance of base class that will be represented."""
        if context.parallel:
            return context._base.Queue
        else:
            return queue.Queue

    def __getstate__(self):
        state = super(Queue, self).__getstate__()
        if (not self.parallel) and (not isinstance(state['_base'], DummyQueue)):
            state['_base'] = None
        return state

    def __setstate__(self, state):
        if state['_base'] is None:
            state['_base'] = queue.Queue()
        super(Queue, self).__setstate__(state)

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        return DummyQueue()

    def join(self, *args, **kwargs):
        self.check_for_base('join')
        if self.parallel:
            try:
                self._base.close()
            except OSError:  # pragma: debug
                pass
            return self._base.join_thread(*args, **kwargs)
        else:
            return self._base.join(*args, **kwargs)

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        if self.parallel:
            self.join()
        if Queue is not None:
            super(Queue, self).disconnect()

    def empty(self):
        try:
            return self._base.empty()
        except OSError:  # pragma: debug
            self.disconnect()
            return True

    def put(self, *args, **kwargs):
        try:
            self._base.put(*args, **kwargs)
        except AttributeError:  # pragma: debug
            # Multiprocessing queue asserts it is not closed
            self.disconnect()
            raise AliasDisconnectError("Queue was closed.")

    def put_nowait(self, *args, **kwargs):
        try:
            self._base.put_nowait(*args, **kwargs)
        except AttributeError:  # pragma: debug
            # Multiprocessing queue asserts it is not closed
            self.disconnect()
            raise AliasDisconnectError("Queue was closed.")


class Dict(ContextObject):
    r"""Multiprocessing/threading shared dictionary."""

    _base_meth = ['clear', 'copy', 'get', 'items', 'keys',
                  'pop', 'popitem', 'setdefault', 'update', 'values',
                  '__contains__', '__delitem__', '__getitem__',
                  '__iter__', '__len__', '__setitem__']
    
    @classmethod
    def get_base_class(cls, context):
        r"""Get instance of base class that will be represented."""
        if context.parallel:
            manager = context._base.Manager()
            return manager.dict
        else:
            return LockedDict

    # Don't define this so that is is not called after manager is
    # shut down.
    # @property
    # def dummy_copy(self):
    #     r"""Dummy copy of base."""
    #     return self._base.copy()
        
    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        try:
            final_value = {k: v for k, v in self._base.items()}
        except BaseException:  # pragma: debug
            final_value = {}
        if LockedDict and isinstance(self._base, LockedDict):
            self._base.disconnect()
        if getattr(self._base, '_manager', None) is not None:
            self._base._manager.shutdown()
            self._base._manager.join()
            del self._base._manager
            self._base._manager = None
        if hasattr(self._base, '_close'):
            self._base._close()
        if Dict is not None:
            super(Dict, self).disconnect()
        self._base = final_value


class LockedObject(AliasObject):
    r"""Container that provides a lock that is acquired before accessing
    the object."""

    _base_locked = True
    
    def __init__(self, *args, task_method='process',
                 task_context=None, **kwargs):
        self.lock = RLock(task_method=task_method,
                          task_context=task_context)
        super(LockedObject, self).__init__(*args, **kwargs)

    def disconnect(self):
        r"""Disconnect from the aliased object by replacing it with
        a dummy object."""
        if LockedObject is not None:
            super(LockedObject, self).disconnect()
        self.lock.disconnect()


# class LockedList(LockedObject):
#     r"""List intended to be shared between threads."""

#     def __init__(self, *args, **kwargs):
#         base = list(*args, **kwargs)
#         super(LockedList, self).__init__(base)


class LockedDict(LockedObject):
    r"""Dictionary that can be shared between threads."""

    _base_class = dict
    _base_meth = ['clear', 'copy', 'get', 'items', 'keys',
                  'pop', 'popitem', 'setdefault', 'update', 'values',
                  '__contains__', '__delitem__', '__getitem__',
                  '__iter__', '__len__', '__setitem__']
    
    def add_subdict(self, key):
        r"""Add a subdictionary."""
        self[key] = {}

    @property
    def dummy_copy(self):
        r"""Dummy copy of base."""
        try:
            out = self._base.copy()
        except BaseException:  # pragma: debug
            out = {}
        return out


class TimeoutError(asyncio.TimeoutError):
    r"""Error to raise when a wait times out."""

    def __init__(self, msg, function_value):
        self.function_value = function_value
        super(TimeoutError, self).__init__(msg)
    

class WaitableFunction(object):
    r"""Create an object that can be waited on until a function returns True.

    Args:
        function (callable): Callable function that takes no arguments and
            returns a boolean.
        polling_interval (float, optional): Time (in seconds) that should be
            waited in between function calls. Defaults to 0.1 seconds.

    """

    __slots__ = ["function", "polling_interval"]

    def __init__(self, function, polling_interval=0.01):
        self.function = function
        self.polling_interval = polling_interval

    def wait(self, timeout=None, on_timeout=False):
        r"""Wait for the function to return True.

        Args:
            timeout (float, optional): Time (in seconds) that should be
                waited for the process to finish. A value of None will wait
                indefinitely. Defaults to None.
            on_timeout (callable, bool, str, optional): Object indicating
                what action should be taken in the event that the timeout is
                reached. If a callable is provided, it will be called. A
                value of False will cause a TimeoutError to be raised. A
                value of True will cause the function value to be returned.
                A string will be used as the error message for a raised
                timeout error. Defaults to False.

        Returns:
            object: The result of the function call.

        """
        def task_target():
            if self.function():
                raise BreakLoopException
        loop = TaskLoop(target=task_target,
                        polling_interval=self.polling_interval)
        loop.start()
        loop.join(timeout)
        if loop.is_alive():
            loop.kill()
            if on_timeout is True:
                return self.function()
            elif (on_timeout is False):
                msg = f'Timeout at {timeout} s'
            elif isinstance(on_timeout, str):
                msg = on_timeout
            else:
                return on_timeout()
            raise TimeoutError(msg, self.function())
        return self.function()


def wait_on_function(function, timeout=None, on_timeout=False,
                     polling_interval=0.1):
    r"""Wait for the function to return True.

    Args:
        function (callable): Callable function that takes no arguments and
            returns a boolean.
        timeout (float, optional): Time (in seconds) that should be
            waited for the process to finish. A value of None will wait
            indefinitely. Defaults to None.
        on_timeout (callable, bool, str, optional): Object indicating
            what action should be taken in the event that the timeout is
            reached. If a callable is provided, it will be called. A
            value of False will cause a TimeoutError to be raised. A
            value of True will cause the function value to be returned.
            A string will be used as the error message for a raised
            timeout error. Defaults to False.
        polling_interval (float, optional): Time (in seconds) that should be
            waited in between function calls. Defaults to 0.1 seconds.

    Returns:
        object: The result of the function call.

    """
    x = WaitableFunction(function, polling_interval=polling_interval)
    return x.wait(timeout=timeout, on_timeout=on_timeout)


class MPIRequestWrapper(WaitableFunction):
    r"""Wrapper for an MPI request."""

    __slots__ = ["request", "completed", "canceled", "_result"]

    def __init__(self, request, completed=False, **kwargs):
        self.request = request
        self.completed = completed
        self.canceled = False
        self._result = None
        super(MPIRequestWrapper, self).__init__(
            lambda: self.test()[0] or self.canceled, **kwargs)

    def cancel(self):
        r"""Cancel the request."""
        if not self.test()[0]:
            self.canceled = True
            return self.request.Cancel()

    @property
    def result(self):
        r"""object: The result of the MPI request."""
        if not self.completed:  # pragma: intermittent
            self.test()
        return self._result

    def test(self):
        r"""Test to see if the request has completed."""
        if not self.completed:
            self.completed, self._result = self.request.test()
        return (self.completed, self._result)

    def wait(self, timeout=None, on_timeout=False):
        r"""Wait for the request to be completed.

        Args:
            timeout (float, optional): Time (in seconds) that should be
                waited for the process to finish. A value of None will wait
                indefinitely. Defaults to None.
            on_timeout (callable, bool, str, optional): Object indicating
                what action should be taken in the event that the timeout is
                reached. If a callable is provided, it will be called. A
                value of False will cause a TimeoutError to be raised. A
                value of True will cause the function value to be returned.
                A string will be used as the error message for a raised
                timeout error. Defaults to False.

        Returns:
            object: The result of the request.

        """
        if not self.test()[0]:
            super(MPIRequestWrapper, self).wait(timeout=timeout,
                                                on_timeout=on_timeout)
        return self._result


class MPIPartnerError(Exception):
    r"""Error raised when there is an error on another process."""
    pass


class MPIErrorExchange(object):
    r"""Set of MPI messages to check for errors."""

    tags = {'ERROR_ON_RANK0': 1,
            'ERROR_ON_RANKX': 2}
    closing_messages = ['ERROR', 'COMPLETE']

    def __init__(self, global_tag=0):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        if self.rank == 0:
            self.partner_ranks = list(range(1, self.size))
        else:
            self.partner_ranks = [0]
        self.reset(global_tag=global_tag)
        self._first_use = True

    def reset(self, global_tag=0):
        r"""Rest comms for the next test."""
        global_tag = max(self.comm.alltoall([global_tag] * self.size))
        self.global_tag = global_tag + max(self.tags.values()) + 1
        if self.rank == 0:
            self.incoming_tag = self.tags['ERROR_ON_RANKX'] + global_tag
            self.outgoing_tag = self.tags['ERROR_ON_RANK0'] + global_tag
        else:
            self.incoming_tag = self.tags['ERROR_ON_RANK0'] + global_tag
            self.outgoing_tag = self.tags['ERROR_ON_RANKX'] + global_tag
        self.outgoing = None
        self.incoming = [
            MPIRequestWrapper(
                self.comm.irecv(source=i, tag=self.incoming_tag),
                polling_interval=0)
            for i in self.partner_ranks]
        self._first_use = False
        
    def recv(self, wait=False):
        r"""Check for response to receive request."""
        results = []
        for i, x in enumerate(self.incoming):
            if wait:
                x.wait()
            completed, result = x.test()
            
            if ((completed
                 and ((self.rank != 0)
                      or (result[1] not in self.closing_messages)))):
                self.incoming[i] = MPIRequestWrapper(
                    self.comm.irecv(
                        source=self.partner_ranks[i],
                        tag=self.incoming_tag),
                    polling_interval=0)
            results.append((completed, result))
        return results

    def send(self, msg):
        r"""Send a message."""
        if (self.rank == 0) or (self.outgoing is None):
            for i in self.partner_ranks:
                self.comm.send(msg, dest=i, tag=self.outgoing_tag)
            if (self.rank != 0) and (msg[1] in self.closing_messages):
                self.outgoing = msg

    def finalize(self, failure):
        r"""Finalize an instance by waiting for completions.

        Args:
            failure (bool): True if there was an error.

        """
        complete = True
        try:
            complete = self.sync(msg='COMPLETE',
                                 local_error=failure,
                                 check_complete=True,
                                 sync_tag=True)
        finally:
            while not complete:  # pragma: debug
                complete = self.sync(msg='COMPLETE',
                                     local_error=failure,
                                     check_complete=True,
                                     dont_raise=True,
                                     sync_tag=True)

    def sync(self, local_tag=None, msg=None, get_tags=False,
             check_equal=False,
             dont_raise=False, local_error=False, sync_tag=False,
             check_complete=False):
        r"""Synchronize processes.

        Args:
            local_tag (int): Next tag that will be used by the local MPI comm.
            get_tags (bool, optional): If True, tags will be exchanged between
                all processes. Defaults to False.
            check_equal (bool, optional): If True, tags will be checked to be
                equal. Defaults to False.
            dont_raise (bool, optional): If True and a MPIPartnerError were
                to be raised, the sync will abort. Defaults to False.

        Raises:
            MPIPartnerError: If there was an error on one of the other MPI
                processes.
            AssertionError: If check_equal is True and the tags are not
                equivalent.

        """
        if local_tag is None:
            local_tag = self.global_tag
        remote_error = False
        if msg is None:
            msg = 'TAG'
        if local_error:  # pragma: debug
            msg = 'ERROR'
        if self.outgoing is not None:  # pragma: debug
            msg = self.outgoing
        if self.rank != 0:
            self.send((local_tag, msg))
            out = self.recv(wait=True)
            complete, results = out[0]  # self.recv(wait=True)[0]
            assert(complete)
        else:
            if (self.outgoing is None) and (msg in self.closing_messages):
                self.outgoing = msg
            results = [(True, (local_tag, msg))] + self.recv(wait=True)
            # TODO: Check for completion (instead of error)
            self.send(results)
        remote_error = any((x[0] and (x[1][1] == 'ERROR'))
                           for x in results)
        all_tag = [x[1][0] for x in results]
        if sync_tag:
            self.global_tag = max(all_tag)
        else:
            self.global_tag = local_tag
        if remote_error and (not local_error) and (not dont_raise):  # pragma: debug
            raise MPIPartnerError("Error on another process.")
        if check_equal and not (remote_error or local_error):
            assert(all((x == local_tag) for x in all_tag))
        if check_complete:
            return all(x[1][1] in self.closing_messages
                       for x in results)
        if get_tags:
            return all_tag
            

# class LockedWeakValueDict(LockedDict):
#     r"""Dictionary of weakrefs that can be shared between threads."""

#     _base_class = weakref.WeakValueDictionary
#     _base_attr = ['data']
#     _base_meth = ['itervaluerefs', 'valuerefs']
    
#     def __init__(self, *args, **kwargs):
#         self._dict_refs = {}
#         super(LockedWeakValueDict, self).__init__(*args, **kwargs)

#     def add_subdict(self, key):
#         r"""Add a subdictionary."""
#         self._dict_refs[key] = weakref.WeakValueDictionary()
#         self[key] = self._dict_refs[key]


class YggTask(YggClass):
    r"""Class for managing Ygg thread/process."""

    _disconnect_attr = (YggClass._disconnect_attr
                        + ['context', 'lock', 'process_instance',
                           'error_flag', 'start_flag', 'terminate_flag',
                           'pipe'])
    
    def __init__(self, name=None, target=None, args=(), kwargs=None,
                 daemon=False, group=None, task_method='thread',
                 context=None, with_pipe=False, **ygg_kwargs):
        if kwargs is None:
            kwargs = {}
        if (target is not None) and ('target' in self._schema_properties):
            ygg_kwargs['target'] = target
            target = None
        self.context = Context.from_base(task_method=task_method,
                                         base=context)
        self.as_process = self.context.parallel
        if self.as_process:
            self.in_process = False
            self.pipe = None
            self.send_pipe = None
            if with_pipe:
                self.pipe = self.context._base.Pipe()
                kwargs['send_pipe'] = self.pipe[1]
        else:
            self.in_process = True
        process_kwargs = dict(
            name=name, group=group, daemon=daemon,
            target=self.run)
        self.process_instance = self.context.Task(**process_kwargs)
        self._ygg_target = target
        self._ygg_args = args
        self._ygg_kwargs = kwargs
        self.lock = self.context.RLock()
        self.create_flag_attr('error_flag')
        self.create_flag_attr('start_flag')
        self.create_flag_attr('terminate_flag')
        self._calling_thread = None
        self.state = ''
        super(YggTask, self).__init__(name, **ygg_kwargs)
        if not self.as_process:
            global _thread_registry
            global _lock_registry
            _thread_registry[self.name] = self.process_instance._base
            _lock_registry[self.name] = self.lock._base
            atexit.register(self.atexit)

    def __getstate__(self):
        out = super(YggTask, self).__getstate__()
        out.pop('_input_args', None)
        out.pop('_input_kwargs', None)
        return out

    def atexit(self):  # pragma: debug
        r"""Actions performed when python exits."""
        if self.is_alive():
            self.info('Thread alive at exit')
            self.cleanup()

    def printStatus(self, return_str=False):
        r"""Print the class status."""
        fmt = '%s(%s): state: %s'
        args = (self.__module__, self.print_name, self.state)
        if return_str:
            msg, _ = self.logger.process(fmt, {})
            return msg % args
        self.logger.info(fmt, *args)

    def cleanup(self):
        r"""Actions to perform to clean up the thread after it has stopped."""
        self.disconnect()
        
    def create_flag_attr(self, attr):
        r"""Create a flag."""
        setattr(self, attr, self.context.Event())

    def get_flag_attr(self, attr):
        r"""Return the flag attribute."""
        return getattr(self, attr)

    def set_flag_attr(self, attr, value=True):
        r"""Set a flag."""
        if value:
            self.get_flag_attr(attr).set()
        else:
            self.get_flag_attr(attr).clear()

    def clear_flag_attr(self, attr):
        r"""Clear a flag."""
        self.set_flag_attr(attr, value=False)

    def check_flag_attr(self, attr):
        r"""Determine if a flag is set."""
        return self.get_flag_attr(attr).is_set()

    def wait_flag_attr(self, attr, timeout=None):
        r"""Wait until a flag is True."""
        return self.get_flag_attr(attr).wait(timeout=timeout)

    def start(self, *args, **kwargs):
        r"""Start thread/process and print info."""
        self.state = 'starting'
        if not self.was_terminated:
            self.set_started_flag()
            self.before_start()
        self.process_instance.start(*args, **kwargs)
        # self._calling_thread = self.get_current_task()

    def before_start(self):
        r"""Actions to perform on the main thread/process before
        starting the thread/process."""
        self.debug('')

    def run(self, *args, **kwargs):
        r"""Continue running until terminate event set."""
        self.debug("Starting method")
        self.state = 'running'
        try:
            self.run_init()
            self.call_target()
        except BaseException:  # pragma: debug
            self.state = 'error'
            self.run_error()
        finally:
            self.run_finally()
            if self.state != 'error':
                self.state = 'finished'

    def run_init(self):
        r"""Actions to perform at beginning of run."""
        # atexit.register(self.atexit)
        self.debug('pid = %s, ident = %s', self.pid, self.ident)
        self.in_process = True
        if self.as_process and ('send_pipe' in self._ygg_kwargs):
            self.send_pipe = self._ygg_kwargs.pop('send_pipe')

    def call_target(self):
        r"""Call target."""
        if self._ygg_target:
            self._ygg_target(*self._ygg_args, **self._ygg_kwargs)

    def run_error(self):
        r"""Actions to perform on error in try/except wrapping run."""
        self.exception("%s ERROR", self.context.task_method.upper())
        self.set_flag_attr('error_flag')

    def run_finally(self):
        r"""Actions to perform in finally clause of try/except wrapping
        run."""
        if self.as_process:
            if self.send_pipe is not None:
                self.send_pipe.close()
        for k in ['_ygg_target', '_ygg_args', '_ygg_kwargs']:
            if hasattr(self, k):
                delattr(self, k)

    def join(self, *args, **kwargs):
        r"""Join the process/thread."""
        return self.process_instance.join(*args, **kwargs)

    def is_alive(self, *args, **kwargs):
        r"""Determine if the process/thread is alive."""
        return self.process_instance.is_alive(*args, **kwargs)

    @property
    def pid(self):
        r"""Process ID."""
        return self.process_instance.pid

    @property
    def ident(self):
        r"""Process ID."""
        return self.process_instance.ident

    @property
    def daemon(self):
        r"""bool: Indicates whether the thread/process is daemonic or not."""
        return self.process_instance.daemon
        
    @property
    def exitcode(self):
        r"""Exit code."""
        if self.as_process:
            out = int(self.check_flag_attr('error_flag'))
            if self.process_instance.exitcode:
                out = self.process_instance.exitcode
            return out
        else:
            return int(self.check_flag_attr('error_flag'))

    @property
    def returncode(self):
        r"""Return code."""
        return self.exitcode

    def kill(self, *args, **kwargs):
        r"""Kill the process."""
        self.process_instance.kill(*args, **kwargs)
        return self.terminate(*args, **kwargs)

    def terminate(self, no_wait=False):
        r"""Set the terminate event and wait for the thread/process to stop.

        Args:
            no_wait (bool, optional): If True, terminate will not block until
                the thread/process stops. Defaults to False and blocks.

        Raises:
            AssertionError: If no_wait is False and the thread/process has not
                stopped after the timeout.

        """
        self.debug('')
        with self.lock:
            self.state = 'terminated'
            if self.was_terminated:  # pragma: debug
                self.debug('Driver already terminated.')
                return
            self.set_terminated_flag()
        if not no_wait:
            # if self.is_alive():
            #     self.join(self.timeout)
            self.wait(timeout=self.timeout)
            assert(not self.is_alive())
        # if self.as_process:
        #     self.process_instance.terminate()

    def poll(self):
        r"""Check if the process is finished and return the return
        code if it is."""
        out = None
        if not self.is_alive():
            out = self.returncode
        return out

    def get_current_task(self):
        r"""Get the current process/thread."""
        return self.context.current_task()

    def get_main_proc(self):
        r"""Get the main process/thread."""
        return self.context.main_task()

    def set_started_flag(self, value=True):
        r"""Set the started flag for the thread/process to True."""
        self.set_flag_attr('start_flag', value=value)

    def set_terminated_flag(self, value=True):
        r"""Set the terminated flag for the thread/process to True."""
        self.set_flag_attr('terminate_flag', value=value)

    @property
    def was_started(self):
        r"""bool: True if the thread/process was started. False otherwise."""
        return self.check_flag_attr('start_flag')

    @property
    def was_terminated(self):
        r"""bool: True if the thread/process was terminated. False otherwise."""
        return self.check_flag_attr('terminate_flag')

    @property
    def main_terminated(self):
        r"""bool: True if the main thread/process has terminated."""
        return (not self.get_main_proc().is_alive())

    def wait(self, timeout=None, key=None):
        r"""Wait until thread/process finish to return using sleeps rather than
        blocking.

        Args:
            timeout (float, optional): Maximum time that should be waited for
                the driver to finish. Defaults to None and is infinite.
            key (str, optional): Key that should be used to register the timeout.
                Defaults to None and is set based on the stack trace.

        """
        self.wait_on_function(lambda: not self.is_alive(),
                              timeout=timeout, key_level=1, key=key)


class BreakLoopException(BaseException):
    r"""Special exception that can be raised by the target function
    for a loop in order to break the loop."""

    __slots__ = ["break_stack"]

    def __init__(self, *args, **kwargs):
        import traceback
        self.break_stack = ''.join(traceback.format_stack())
        super(BreakLoopException, self).__init__(*args, **kwargs)


class BreakLoopError(BreakLoopException):
    r"""Version of BreakLoopException that sets an error message."""
    pass
        

class YggTaskLoop(YggTask):
    r"""Class to run a loop inside a thread/process."""

    _disconnect_attr = (YggTask._disconnect_attr
                        + ['break_flag', 'loop_flag', 'unpause_flag'])

    def __init__(self, *args, **kwargs):
        super(YggTaskLoop, self).__init__(*args, **kwargs)
        self._1st_main_terminated = False
        self._loop_count = 0
        self.create_flag_attr('break_flag')
        self.create_flag_attr('loop_flag')
        self.create_flag_attr('unpause_flag')
        self.set_flag_attr('unpause_flag', value=True)
        self.break_stack = None

    @property
    def loop_count(self):
        r"""int: Number of loops performed."""
        with self.lock:
            return self._loop_count

    def on_main_terminated(self, dont_break=False):  # pragma: debug
        r"""Actions performed when 1st main terminated.

        Args:
            dont_break (bool, optional): If True, the break flag won't be set.
                Defaults to False.

        """
        self._1st_main_terminated = True
        if not dont_break:
            self.debug("on_main_terminated")
            self.set_break_flag()

    def set_break_flag(self, value=True, break_stack=None):
        r"""Set the break flag for the thread/process to True."""
        if self.break_stack is None:
            if break_stack is None:
                import traceback
                break_stack = ''.join(traceback.format_stack())
            self.break_stack = break_stack
        self.set_flag_attr('break_flag', value=value)
        if value:
            self.set_flag_attr('unpause_flag', value=True)

    def pause(self):
        r"""Pause the loop execution."""
        self.set_flag_attr('unpause_flag', value=False)

    def resume(self):
        r"""Resume the loop execution."""
        self.set_flag_attr('unpause_flag', value=True)

    @property
    def was_break(self):
        r"""bool: True if the break flag was set."""
        return self.check_flag_attr('break_flag')

    def set_loop_flag(self, value=True):
        r"""Set the loop flag for the thread/process to True."""
        self.set_flag_attr('loop_flag', value=value)

    @property
    def was_loop(self):
        r"""bool: True if the thread/process was loop. False otherwise."""
        return self.check_flag_attr('loop_flag')

    def wait_for_loop(self, timeout=None, key=None, nloop=0):
        r"""Wait until thread/process enters loop to return using sleeps rather than
        blocking.

        Args:
            timeout (float, optional): Maximum time that should be waited for
                the thread/process to enter loop. Defaults to None and is infinite.
            key (str, optional): Key that should be used to register the timeout.
                Defaults to None and is set based on the stack trace.
            nloop (int, optional): Number of loops that should be performed
                before breaking. Defaults to 0.

        """
        self.wait_on_function(
            lambda: (self.was_loop and (self.loop_count >= nloop)
                     or (not self.is_alive())),
            timeout=timeout, key=key, key_level=1)

    def before_loop(self):
        r"""Actions performed before the loop."""
        self.debug('')

    def after_loop(self):
        r"""Actions performed after the loop."""
        self.debug('')

    def call_target(self):
        r"""Call target."""
        self.debug("Starting loop")
        self.before_loop()
        if (not self.was_break):
            self.set_loop_flag()
        while (not self.was_break):
            if ((self.main_terminated
                 and (not self._1st_main_terminated))):  # pragma: debug
                self.on_main_terminated()
            else:
                self.wait_flag_attr('unpause_flag')
                try:
                    self.run_loop()
                except BreakLoopError as e:
                    self.error("BreakLoopError: %s", e)
                    self.set_break_flag(break_stack=e.break_stack)
                except BreakLoopException as e:
                    self.debug("BreakLoopException: %s", e)
                    self.set_break_flag(break_stack=e.break_stack)
        if not self.break_stack:
            self.set_break_flag()
        
    def run_loop(self, *args, **kwargs):
        r"""Actions performed on each loop iteration."""
        if self._ygg_target:
            self._ygg_target(*self._ygg_args, **self._ygg_kwargs)
        else:
            self.set_break_flag()
        with self.lock:
            self._loop_count += 1

    def run_error(self):
        r"""Actions to perform on error in try/except wrapping run."""
        super(YggTaskLoop, self).run_error()
        self.debug("run_error")
        self.set_break_flag()
        
    def run(self, *args, **kwargs):
        r"""Continue running until terminate event set."""
        super(YggTaskLoop, self).run(*args, **kwargs)
        try:
            self.after_loop()
        except BaseException:  # pragma: debug
            self.exception("AFTER LOOP ERROR")
            self.set_flag_attr('error_flag')

    def terminate(self, *args, **kwargs):
        r"""Also set break flag."""
        self.debug("terminate")
        self.set_break_flag()
        super(YggTaskLoop, self).terminate(*args, **kwargs)
