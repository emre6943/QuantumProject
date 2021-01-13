import os
import math
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

def alt_grover_n(circuit, answer):
    num = len(answer)

    # Calculating itteration number
    # r = math.floor(pi / 4 * math.sqrt(2 ** len(answer)))
    # if r == 0:
    #     r = 1
    # print(str(r) + " iterations made")
    # i is one because dono what to itterate
    r = 1

    zero = []
    one = []
    for i, val in enumerate(answer):
        if val:
            one.append(i)
        else:
            zero.append(i)



    for i in range(r):
        # initialisation
        for x in range(num):
            circuit.ry(pi, q[x])

        # oracles
        for x in zero:
            circuit.rx(pi, q[x])

        # diffuser
        for x in range(num):
            circuit.ry(pi, q[x])

        circuit.h(num - 1)
        circuit.mct(list(range(num - 1)), num - 1)  # multi-controlled-toffoli
        circuit.h(num - 1)

        for x in range(num):
            circuit.ry(pi, q[x])

    return circuit


if __name__ == '__main__':

    authentication = get_authentication()
    QI.set_authentication(authentication, QI_URL)
    # qi_backend = QI.get_backend('Starmon-5')
    qi_backend = QI.get_backend('QX single-node simulator')

    q = QuantumRegister(5)
    c = ClassicalRegister(5)
    circuit = QuantumCircuit(q, c)

    # circuit = alt_grover(circuit, search=1)
    circuit = alt_grover_n(circuit, [True, True, True, True, False])

    circuit.measure(q, c)

    print(circuit.draw())

    qi_job = execute(circuit, backend=qi_backend, shots=1024)
    qi_result = qi_job.result()
    probabilities_histogram = qi_result.get_probabilities(circuit)
    plot_results(probabilities_histogram, [120, 20])