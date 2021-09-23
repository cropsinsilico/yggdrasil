import pytest
try:
    from mpi4py import MPI
    _on_mpi = (MPI.COMM_WORLD.Get_size() > 1)
except ImportError:
    _on_mpi = False
_mpi_error_exchange = None


if _on_mpi:
    from yggdrasil.multitasking import MPIErrorExchange
    _global_tag = 0

    def new_mpi_exchange():
        global _mpi_error_exchange
        global _global_tag
        if _mpi_error_exchange is None:
            _mpi_error_exchange = MPIErrorExchange(global_tag=_global_tag)
        else:
            _global_tag = _mpi_error_exchange.global_tag
            _mpi_error_exchange.reset(global_tag=_global_tag)
        return _mpi_error_exchange

    def adv_global_mpi_tag(value=1):
        global _mpi_error_exchange
        assert(_mpi_error_exchange is not None)
        out = _mpi_error_exchange.global_tag
        _mpi_error_exchange.global_tag += value
        return out

    def sync_mpi_exchange(*args, **kwargs):
        global _mpi_error_exchange
        assert(_mpi_error_exchange is not None)
        return _mpi_error_exchange.sync(*args, **kwargs)

    # Method of raising errors when other process fails
    # https://docs.pytest.org/en/latest/example/simple.html#
    # making-test-result-information-available-in-fixtures
    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(item, call):
        # execute all other hooks to obtain the report object
        outcome = yield
        rep = outcome.get_result()
        # set a report attribute for each phase of a call, which can
        # be "setup", "call", "teardown"
        setattr(item, "rep_" + rep.when, rep)

    @pytest.fixture(autouse=True)
    def sync_mpi_result(request):
        r"""Synchronize results between MPI ranks."""
        global _global_tag
        mpi_exchange = new_mpi_exchange()
        mpi_exchange.sync()
        yield
        failure = (request.node.rep_setup.failed
                   or request.node.rep_call.failed)
        mpi_exchange.finalize(failure)

    # Monkey patch pytest-cov plugin with MPI Barriers to prevent multiple
    # MPI processes from attempting to modify the .coverage data file at
    # the same time and limit the coverage output to the rank 0 process
    @pytest.fixture(scope="session", autouse=True)
    def finalize_mpi(request):
        """Slow down the exit on MPI processes to prevent collision in access
        to .coverage file."""
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        manager = request.config.pluginmanager
        plugin_class = manager.get_plugin('pytest_cov').CovPlugin
        plugin = None
        for x in manager.get_plugins():
            if isinstance(x, plugin_class):
                plugin = x
                break
        if not plugin:  # pragma: no cover
            return
        old_finish = getattr(plugin.cov_controller, 'finish')

        def new_finish():
            comm.Barrier()
            for _ in range(rank):
                comm.Barrier()
            old_finish()
            # These lines come after coverage collection
            for _ in range(rank, size):  # pragma: testing
                comm.Barrier()  # pragma: testing
            comm.Barrier()  # pragma: testing

        plugin.cov_controller.finish = new_finish
        if rank != 0:

            def new_is_worker(session):  # pragma: testing
                return True

            plugin._is_worker = new_is_worker
