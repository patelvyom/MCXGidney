> **ℹ️ Note:** This implementation has been **officially merged into [Qiskit](https://github.com/Qiskit/qiskit)** and **[PennyLane](https://github.com/PennyLaneAI/pennylane)**.
> - Qiskit: [qiskit PR #13922](https://github.com/Qiskit/qiskit/pull/13922)
> - PennyLane: [pennylane PR #7028](https://github.com/PennyLaneAI/pennylane/pull/7028)

> **Quick usage:**
> 
> **Qiskit**
```python
from qiskit import QuantumCircuit, transpile

qc = QuantumCircuit(11)
qc.mcx(list(range(8)), 8)
transpile(qc, basis_gates=['u', 'cx']).count_ops()["cx"] # Should be 6*n_ctrl - 6
```
> **Pennylane**
```python
import pennylane as qml

gate = qml.MultiControlledX(wires=list(range(9)), work_wires=list(range(9, 11)), work_wire_type="clean")
gate.decomposition()
```

# Optimised MCX Implementations using Conditionally Clean Ancillae

## Overview
This repository contains implementation of Multi Controlled X gate based on [Rise of Conditionally Clean Ancillae for Optimizing Quantum Circuits](https://arxiv.org/abs/2407.17966).
The implementation leverages conditionally clean ancillae to reduce the gate counts and depths of the MCX gate. They
are implemented in both Qiskit and PennyLane.

**Optimised Multi-Controlled Toffoli Gates:**
- **1 clean ancilla:** Reduces an *n*-bit Toffoli to `2n − 3` Toffoli gates with **O(n) depth**.
- **2 clean ancillae:** Reduces an *n*-bit Toffoli to `2n − 3` Toffoli gates with **O(log n) depth**.
- **1 dirty ancilla:** Reduces an *n*-bit Toffoli to `4n − 8` Toffoli gates with **O(n) depth**.
- **2 dirty ancillae:** Reduces an *n*-bit Toffoli to `4n − 8` Toffoli gates with **O(log n) depth**.
  
## Installation
```bash
git clone https://github.com/patelvyom/MCXGidney.git
cd MCXGidney
pip install -r requirements.txt
```

## Usage
The implementation can be used to generate and analyze optimised circuits.

### Example usage in Qiskit:
```python
from mcx_qiskit import MCXLinearDepth, MCXLogDepth
n_ctrls = 5

gate = MCXLinearDepth(n_ctrls, clean=True)
gate.definition.draw()

gate = MCXLogDepth(n_ctrls, clean=False)
gate.definition.draw()
```

### Example usage in PennyLane:
```python
import pennylane as qml
from pennylane.wires import Wires
from mcx_pennylane import MCXLinearDepth, MCXLogDepth

n_ctrl_wires = 5
dev = qml.device("default.qubit")
control_wires = Wires(range(n_ctrl_wires))
target_wire = Wires([n_ctrl_wires])
work_wires = Wires(range(n_ctrl_wires + 1, n_ctrl_wires + 3))

mcx_linear_depth = MCXLinearDepth(control_wires, target_wire, work_wires[0], work_wire_type="clean")
mcx_log_depth = MCXLogDepth(control_wires, target_wire, work_wires, work_wire_type="dirty")

@qml.qnode(dev)
def circuit(gates):
    [qml.apply(gate) for gate in gates]
    return qml.state()

qml.draw_mpl(circuit)(mcx_linear_depth)
qml.draw_mpl(circuit)(mcx_log_depth)
```



## References
- [Rise of Conditionally Clean Ancillae for Optimizing Quantum Circuits](https://arxiv.org/abs/2407.17966)
