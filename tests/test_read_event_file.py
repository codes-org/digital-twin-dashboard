def test_read_event_file():
    from codes_dashboard.app.core.event_trace_file import EventFile

    ross_file = EventFile("tests/data/ross-binary-data/esnet-model-inst-evtrace.bin")
    ross_file.read()
    ross_file.close()