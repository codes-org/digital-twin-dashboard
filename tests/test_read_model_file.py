def test_read_model_file():
    from codes_dashboard.app.core.model_file import ModelFile

    ross_file = ModelFile("tests/data/ross-binary-data/esnet-model-inst-analysis-lps.bin")
    ross_file.read()
    ross_file.close()