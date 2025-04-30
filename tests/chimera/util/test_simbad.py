from chimera.util.simbad import simbad_lookup


def test_simbad_lookup():
    """
    Test the simbad_lookup function to ensure it returns the expected data.
    """
    # Example object name for testing
    object_name = "Sirius"
    expected_result = {
        "simbad_oid": 8399845,
        "main_id": "* alf CMa",
        "ra": 101.28715533333335,
        "dec": -16.71611586111111,
    }

    result = simbad_lookup(object_name)

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
