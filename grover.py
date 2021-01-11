import os
import matplotlib.pyplot as plt
import numpy as np
import math
from getpass import getpass
from quantuminspire.credentials import load_account, get_token_authentication, get_basic_authentication

from qiskit.circuit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute

from quantuminspire.qiskit import QI

QI_EMAIL = os.getenv('QI_EMAIL')
QI_PASSWORD = os.getenv('QI_PASSWORD')
QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

def all_bits(q_num):
    arr = []
    for x in range(q_num):
        arr.append(x)
    return arr

def get_authentication():
    """ Gets the authentication for connecting to the Quantum Inspire API."""
    token = load_account()
    if token is not None:
        return get_token_authentication(token)
    else:
        if QI_EMAIL is None or QI_PASSWORD is None:
            print('Enter email:')
            email = input()
            print('Enter password')
            password = getpass()
        else:
            email, password = QI_EMAIL, QI_PASSWORD
        return get_basic_authentication(email, password)

# modular ccz good for 4 - 6 qubits
def connecter(qc, n):
    angle = np.pi / 16
    qc.rz(angle, 0)

    qc.cx(0, 1)
    qc.rz(-angle, 1)
    qc.cx(0, 1)
    qc.rz(angle, 1)

    i = 2
    while i < n:
        for x in range(2):
            p = i - 1
            while p != 0:
                qc.cx(p, i)
                qc.rz(-angle, i)
                qc.cx(0, i)
                qc.rz(angle, i)
                p = p - 1
        i = i + 1

    return qc

# used for 3 qubits
def ccz(qc, a, b, c):
    qc.cx(b, c)
    qc.tdg(c)
    qc.cx(a, c)
    qc.t(c)
    qc.cx(b, c)
    qc.tdg(c)
    qc.cx(a, c)
    qc.t([b, c])
    qc.cx(a, b)
    qc.t(a)
    qc.tdg(b)
    qc.cx(a, b)
    return qc

def initialize_s(qc, qubits):
    """Apply a H-gate to 'qubits' in qc"""
    for q in qubits:
        qc.h(q)
    return qc

def oracle(answer):
    """
    Creates the oracle depending on the output wanted
    :param qc: quantum circuit
    :param answer: the wanted element
    :return: quantum circuit
    """
    answer = answer[::-1]
    num = len(answer)
    qc = QuantumCircuit(num)

    zero = []
    one = []
    for i, val in enumerate(answer):
        if val:
            one.append(i)
        else:
            zero.append(i)

    # Placing Zeros
    for x in zero:
        qc.x(x)

    # Connectors
    if num == 2:
        qc.cz(0, 1)
    elif num == 3:
        qc = ccz(qc, 0, 1, 2)
    else:
        # qc = connecter(qc, num)
        qc.h(num - 1)
        qc.mct(list(range(num - 1)), num - 1)  # multi-controlled-toffoli
        qc.h(num - 1)

    # Placing Zeros
    for x in zero:
        qc.x(x)

    gate = qc.to_gate()
    gate.name = "Oracle"
    print(qc.draw())

    return gate


def diffuser(nqubits):
    qc = QuantumCircuit(nqubits)
    # Apply transformation |s> -> |00..0> (H-gates)
    for qubit in range(nqubits):
        qc.h(qubit)
    # Apply transformation |00..0> -> |11..1> (X-gates)
    for qubit in range(nqubits):
        qc.x(qubit)
    # Do multi-controlled-Z gate
    qc.h(nqubits-1)
    qc.mct(list(range(nqubits-1)), nqubits-1)  # multi-controlled-toffoli
    qc.h(nqubits-1)
    # Apply transformation |11..1> -> |00..0>
    for qubit in range(nqubits):
        qc.x(qubit)
    # Apply transformation |00..0> -> |s>
    for qubit in range(nqubits):
        qc.h(qubit)
    # We will return the diffuser as a gate
    gate = qc.to_gate()
    gate.name = "Diffuser"
    print(qc.draw())
    return gate

def plot_results(probabilities_histogram, size):
    names = []
    values = []

    for state, val in probabilities_histogram.items():
        names.append(state)
        values.append(val)
    plt.figure(figsize=(size[0], size[1]))
    plt.bar(names, values)
    plt.xlabel('Probabilities')
    plt.ylabel('States')
    plt.title('Results')
    plt.show()


def grover(qc, answer, bits):
    r = math.floor(np.pi * math.sqrt(2 ** len(bits)) / 4)
    print(str(r) + " iterations made")
    for i in range(r):
        for an in answer:
            qc.append(oracle(an), bits)
        qc.append(diffuser(len(bits)), bits)
    return qc

if __name__ == '__main__':

    authentication = get_authentication()
    QI.set_authentication(authentication, QI_URL)
    # qi_backend = QI.get_backend('Starmon-5')
    qi_backend = QI.get_backend('QX single-node simulator')

    q_num = 10
    bits = all_bits(q_num)

    q = QuantumRegister(q_num)
    b = ClassicalRegister(q_num)
    circuit = QuantumCircuit(q, b)

    circuit = initialize_s(circuit, bits)

    circuit = grover(circuit, [[True, True, True, False, True, True, True, False, True, True]], bits)

    circuit.measure(q, b)

    print(circuit.draw())

    qi_job = execute(circuit, backend=qi_backend, shots=1024)
    qi_result = qi_job.result()
    probabilities_histogram = qi_result.get_probabilities(circuit)
    plot_results(probabilities_histogram, [120, 20])
