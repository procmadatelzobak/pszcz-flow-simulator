from server.state import SimState


def test_add_pipe_unknown_nodes():
    state = SimState()
    # create one node so the other is missing
    state.apply_edits([
        {"op": "add_node", "id": "n1", "type": "source", "params": {}}
    ])
    err = state.apply_edits([
        {"op": "add_pipe", "id": "p1", "a": "n1", "b": "n2", "params": {}}
    ])
    assert err == {"code": "unknown_entity"}


def test_add_pipe_missing_endpoints():
    state = SimState()
    state.apply_edits([
        {"op": "add_node", "id": "n1", "type": "source", "params": {}}
    ])
    err = state.apply_edits([
        {"op": "add_pipe", "id": "p1", "a": "n1"}
    ])
    assert err == {"code": "bad_request"}
