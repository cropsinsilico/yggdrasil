def get_testing_options(example_name='timesync1'):
    r"""Get testing parameters for this example."""
    def validation_function():
        import os
        import tempfile
        from yggdrasil.examples.timesync1.plot_timesync import main
        tempdir = tempfile.gettempdir()
        fileA = os.path.join(tempdir, "modelA_output.txt")
        fileB = os.path.join(tempdir, "modelB_output.txt")
        main(fileA, fileB, example_name)
    return dict(
        validation_function=validation_function,
        env={'TIMESYNC_TSTEP_A': '20', 'TIMESYNC_TSTEP_B': '3'})
