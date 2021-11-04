def get_testing_options():
    r"""Get testing parameters for this example."""
    out = dict(
        output_dir='Output',
        output_files=['canopy_structure.txt',
                      'growth_rate.txt',
                      'light_intensity.txt',
                      'photosynthesis_rate.txt'],
        skip_check_results=True)
    return out
