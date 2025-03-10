
from typing import Literal
import pennylane as qml
from pennylane.operation import Operation, Operator
from pennylane.wires import WiresLike


def _linear_depth_ladder_ops(wires: WiresLike) -> tuple[list[Operator], int]:
    r"""
    Helper function to create linear-depth ladder operations used in Khattar and Gidney's MCX synthesis.
    In particular, this implements Step-1 and Step-2 on Fig. 3 of [1] except for the first and last
    CCX gates.

    Args:
        wires (Wires): Wires to apply the ladder operations on.

    Returns:
        tuple[list[Operator], int]: Linear-depth ladder circuit and the index of control qubit to
        apply the final CCX gate.

    References:
        1. Khattar and Gidney, Rise of conditionally clean ancillae for optimizing quantum circuits
        `arXiv:2407.17966 <https://arxiv.org/abs/2407.17966>`__
    """

    n = len(wires)
    if n <= 2:
        raise ValueError("n_ctrls >= 2 to use MCX ladder. Otherwise, use CCX")

    gates = []
    # up-ladder
    for i in range(1, n - 2, 2):
        gates.append(qml.Toffoli(wires=[wires[i + 1], wires[i + 2], wires[i]]))
        gates.append(qml.PauliX(wires=wires[i]))

    # down-ladder
    if n % 2 == 0:
        ctrl_1, ctrl_2, target = n - 3, n - 5, n - 6
    else:
        ctrl_1, ctrl_2, target = n - 1, n - 4, n - 5

    if target >= 0:
        gates.append(qml.Toffoli(wires=[wires[ctrl_1], wires[ctrl_2], wires[target]]))
        gates.append(qml.PauliX(wires=wires[target]))

    for i in range(target, 1, -2):
        gates.append(qml.Toffoli(wires=[wires[i], wires[i - 1], wires[i - 2]]))
        gates.append(qml.PauliX(wires=wires[i - 2]))

    final_ctrl = max(0, 5 - n)

    return gates, final_ctrl


def MCXLinearDepth(
    control_wires: list[WiresLike],
    target_wire: int,
    work_wire: int,
    work_wire_type: Literal["clean", "dirty"] = "clean",
) -> list[Operator]:
    r"""
    Synthesise a multi-controlled X gate with :math:`k` controls using :math:`1` ancillary qubit. It
    produces a circuit with :math:`2k-3` Toffoli gates and depth :math:`O(k)` if the ancilla is clean
    and :math:`4k-3` Toffoli gates and depth :math:`O(k)` if the ancilla is dirty as described in
    Sec. 5.1 of [1].

    Args:
        control_wires (Wires): the control wires
        target_wire (int): the target wire
        work_wires (Wires): the work wires used to decompose the gate
        work_wire_type (string): If "dirty", perform un-computation. Default is "clean".

    Returns:
        list[Operator]: the synthesized quantum circuit

    References:
        1. Khattar and Gidney, Rise of conditionally clean ancillae for optimizing quantum circuits
        `arXiv:2407.17966 <https://arxiv.org/abs/2407.17966>`__
    """

    gates = []
    gates.append(qml.Toffoli(wires=[control_wires[0], control_wires[1], work_wire]))
    ladder_ops, final_ctrl = _linear_depth_ladder_ops(control_wires)
    gates += ladder_ops
    gates.append(qml.Toffoli(wires=[work_wire, control_wires[final_ctrl], target_wire]))
    gates += ladder_ops[::-1]
    gates.append(qml.Toffoli(wires=[control_wires[0], control_wires[1], work_wire]))

    if work_wire_type == "dirty":
        # perform toggle-detection if ancilla is dirty
        gates += ladder_ops
        gates.append(qml.Toffoli(wires=[work_wire, control_wires[final_ctrl], target_wire]))
        gates += ladder_ops[::-1]

    return gates


def _n_parallel_ccx_x(
    control_wires_x: WiresLike, control_wires_y: WiresLike, target_wires: WiresLike
) -> list[Operation]:
    r"""
    Construct a quantum circuit for creating n-condionally clean ancillae using 3n qubits. This
    implements Fig. 4a of [1]. Each wire is of the same size :math:`n`.

    Args:
        control_wires_x (Wires): The control wires for register 1.
        control_wires_y (Wires): The control wires for register 2.
        target_wires (Wires): The wires for target register.

    Returns:
        list[Operation]: The quantum circuit for creating n-condionally clean ancillae.

    References:
        1. Khattar and Gidney, Rise of conditionally clean ancillae for optimizing quantum circuits
        `arXiv:2407.17966 <https://arxiv.org/abs/2407.17966>`__
    """

    if len(control_wires_x) != len(control_wires_y) or len(control_wires_x) != len(target_wires):
        raise ValueError("The number of wires must be the same for x, y, and target.")

    gates = []
    for i in range(len(control_wires_x)):
        gates.append(qml.X(wires=target_wires[i]))
        gates.append(qml.Toffoli(wires=[control_wires_x[i], control_wires_y[i], target_wires[i]]))

    return gates


def _build_logn_depth_ccx_ladder(
    work_wire: int, control_wires: list[WiresLike]
) -> tuple[list[Operator], list[Operator]]:
    r"""
    Helper function to build a log-depth ladder compose of CCX and X gates as shown in Fig. 4b of [1].

    Args:
        work_wire (int): The work wire.
        control_wires (list[Wire]): The control wires.

    Returns:
        tuple[list[Operator], list[WiresLike]: log-depth ladder circuit of cond. clean ancillae and
        control_wires to apply the linear-depth MCX gate on.

    References:
        1. Khattar and Gidney, Rise of conditionally clean ancillae for optimizing quantum circuits
        `arXiv:2407.17966 <https://arxiv.org/abs/2407.17966>`__
    """

    gates = []
    anc = [work_wire]
    final_ctrls = []

    while len(control_wires) > 1:
        next_batch_len = min(len(anc) + 1, len(control_wires))
        control_wires, nxt_batch = control_wires[next_batch_len:], control_wires[:next_batch_len]
        new_anc = []
        while len(nxt_batch) > 1:
            ccx_n = len(nxt_batch) // 2
            st = int(len(nxt_batch) % 2)
            ccx_x, ccx_y, ccx_t = (
                nxt_batch[st : st + ccx_n],
                nxt_batch[st + ccx_n :],
                anc[-ccx_n:],
            )
            assert len(ccx_x) == len(ccx_y) == len(ccx_t) == ccx_n >= 1
            if ccx_t != [work_wire]:
                gates += _n_parallel_ccx_x(ccx_x, ccx_y, ccx_t)
            else:
                gates.append(qml.Toffoli(wires=[ccx_x[0], ccx_y[0], ccx_t[0]]))
            new_anc += nxt_batch[st:]  #                    # newly created cond. clean ancilla
            nxt_batch = ccx_t + nxt_batch[:st]
            anc = anc[:-ccx_n]

        anc = sorted(anc + new_anc)
        final_ctrls += nxt_batch

    final_ctrls += control_wires
    final_ctrls = sorted(final_ctrls)
    final_ctrls.remove(work_wire)  #                        # exclude ancilla
    return gates, final_ctrls


def MCXLogDepth(
    control_wires: WiresLike,
    target_wire: int,
    work_wires: WiresLike,
    work_wire_type: Literal["clean", "dirty"] = "clean",
) -> list[Operator]:
    r"""
    Synthesise a multi-controlled X gate with :math:`k` controls using :math:`2` ancillary qubits.
    It produces a circuit with :math:`2k-3` Toffoli gates and depth :math:`O(\log(k))` if using
    clean ancillae, and :math:`4k-8` Toffoli gates and depth :math:`O(\log(k))` if using dirty
    ancillae as described in Sec. 5 of [1].

    Args:
        control_wires (Wires): The control wires.
        target_wire (int): The target wire.
        work_wires (Wires): The work wires.
        work_wire_type (string): If "dirty" perform uncomputation after we're done. Default is "clean".

    Returns:
        list[Operator]: The synthesized quantum circuit.

    References:
        1. Khattar and Gidney, Rise of conditionally clean ancillae for optimizing quantum circuits
        `arXiv:2407.17966 <https://arxiv.org/abs/2407.17966>`__
    """

    if len(work_wires) < 2:
        raise ValueError("At least 2 work wires are needed for this decomposition.")

    gates = []
    ladder_ops, final_ctrls = _build_logn_depth_ccx_ladder(work_wires[0], control_wires)
    gates += ladder_ops
    if len(final_ctrls) == 1:  # Already a toffoli
        gates.append(qml.Toffoli(wires=[work_wires[0], final_ctrls[0], target_wire]))
    else:
        mid_mcx = MCXLinearDepth(
            work_wires[0:1] + final_ctrls, target_wire, work_wires[1:2], work_wire_type="clean"
        )
        gates += mid_mcx
    gates += ladder_ops[::-1]

    if work_wire_type == "dirty":
        # perform toggle-detection if ancilla is dirty
        gates += ladder_ops[1:]
        if len(final_ctrls) == 1:
            gates.append(qml.Toffoli(wires=[work_wires[0], final_ctrls[0], target_wire]))
        else:
            gates += mid_mcx
        gates += ladder_ops[1:][::-1]

    return gates