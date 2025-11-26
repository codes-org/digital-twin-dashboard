def test_read_ross_file():
    from codes_dashboard.app.core.ross_binary_file import ROSSFile

    ross_file = ROSSFile("tests/data/ross-binary-data/ross-stats-gvt.bin")
    ross_file.read()
    ross_file.close()
    
