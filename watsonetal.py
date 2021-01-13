import os
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, execute
from numpy import pi
from quantuminspire.qiskit import QI
from grover import get_authentication, plot_results

QI_EMAIL = os.getenv('QI_EMAIL')
QI_PASSWORD = os.getenv('QI_PASSWORD')
QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

def alt_grover(circuit, search=0):
    # initialisation
    circuit.y(q[0])
    circuit.y(q[1])

    # oracles
    if search == 0:  # 00
        circuit.rx(pi, q[0])
        circuit.rx(pi, q[1])
    elif search == 1:  # 01
        circuit.rx(pi, q[1])
    elif search == 2:  # 10
        circuit.rx(pi, q[0])
    elif search == 3:  # 11
        pass
    else:
        print("Searching for non-existing element. The possibilities are: 0, 1, 2, 3.")

    # diffuser
    circuit.y(q[1])
    circuit.y(q[0])
    circuit.cz(q[0], q[1])
    circuit.y(q[0])
    circuit.y(q[1])

    return circuit

if __name__ == '__main__':

    authentication = get_authentication()
    QI.set_authentication(authentication, QI_URL)
    qi_backend = QI.get_backend('QX single-node simulator')

    q = QuantumRegister(2)
    c = ClassicalRegister(2)
    circuit = QuantumCircuit(q, c)

    circuit = alt_grover(circuit, search=1)

    circuit.measure(q, c)

    print(circuit.draw())

    qi_job = execute(circuit, backend=qi_backend, shots=1024)
    qi_result = qi_job.result()
    probabilities_histogram = qi_result.get_probabilities(circuit)
    plot_results(probabilities_histogram, [120, 20])