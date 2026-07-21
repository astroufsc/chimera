# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import inspect

import pytest

from chimera.controllers.scheduler.model import Operator as OperatorAction
from chimera.interfaces.operator import Operator


def test_request_accepts_what_the_scheduler_sends():
    # OperatorHandler calls op.request(action.type, action.message); this is
    # the mismatch the missing interface file made impossible to catch
    inspect.signature(Operator.request).bind(None, "confirmation", "continue?")


def test_message_is_optional():
    inspect.signature(Operator.request).bind(None, "alert")


def test_request_field_names_match_the_action():
    columns = {c.name for c in OperatorAction.__table__.columns}
    assert {"type", "message"} <= columns


def test_unimplemented_by_default():
    class Incomplete(Operator):
        pass

    with pytest.raises(NotImplementedError):
        Incomplete().request("confirmation", "continue?")
