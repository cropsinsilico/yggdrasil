import pytest
try:
    from mpi4py import MPI
    _on_mpi = (MPI.COMM_WORLD.Get_size() > 1)
except ImportError:
    _on_mpi = False


if _on_mpi:
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
    def sync_result(request):
        r"""Synchronize results between MPI ranks."""
        comm = MPI.COMM_WORLD
        size = comm.Get_size()
        yield
        failure = (request.node.rep_setup.failed
                   or request.node.rep_call.failed)
        all_failure = comm.alltoall([failure] * size)
        if (not failure) and any(all_failure):
            raise Exception("Failure occured on another MPI process.")

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
