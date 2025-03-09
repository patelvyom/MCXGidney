# Optimised MCX Implementations using Conditionally Clean Ancillae

## Overview
This repository contains a Qiskit implementation of Multi Controlled X gate based on  [Rise of Conditionally Clean Ancillae for Optimizing Quantum Circuits](https://arxiv.org/abs/2407.17966). The implementation leverages conditionally clean ancillae to reduce the gate counts and depths of the MCX gate.

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
The implementation can be used to generate and analyze optimized circuits. Example usage:
```python
from mcx import MCXLinearDepth, MCXLogDepth
n = 5
gate = MCXLogDepth(n, clean=False)
gate.definition.draw()
```

## References
- [Rise of Conditionally Clean Ancillae for Optimizing Quantum Circuits](https://arxiv.org/abs/2407.17966)
