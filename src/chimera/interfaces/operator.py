# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface

__all__ = ["Operator"]


class Operator(Interface):
    """A human telescope operator the observatory can ask for a decision.

    The scheduler's operator action blocks on request() until the operator
    answers, so an implementation may take as long as a person does.
    """

    def request(self, type: str, msg: str | None = None) -> bool:  # noqa: A002
        """Request operator intervention and wait for the answer.

        @param type: The kind of request, matching the scheduler action's
                     'type' field: "confirmation", "input", "alert", etc.
                     Implementations decide which kinds they can present,
                     and should reject the ones they cannot.
        @type  type: str

        @param msg: Message to show the operator.
        @type  msg: str | None

        @return: True if the operator approved, False otherwise.
        @rtype: bool
        """
        raise NotImplementedError()
