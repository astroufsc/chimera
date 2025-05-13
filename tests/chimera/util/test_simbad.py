from chimera.util.simbad import simbad_lookup


def test_simbad_lookup():
    """
    Test the simbad_lookup function to ensure it returns the expected data.
    """
    # Example object name for testing
    object_name = "Sirius"
    expected_result = ("* alf CMa", 6.752477022222223, -16.71611586111111, 2000.0)

    result = simbad_lookup(object_name)

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
