import os
import matplotlib.pyplot as plt
from getpass import getpass
from quantuminspire.credentials import load_account, get_token_authentication, get_basic_authentication

from qiskit.circuit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute

from quantuminspire.qiskit import QI

QI_EMAIL = os.getenv('QI_EMAIL')
QI_PASSWORD = os.getenv('QI_PASSWORD')
QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')


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

def initialize_s(qc, qubits):
    """Apply a H-gate to 'qubits' in qc"""
    for q in qubits:
        qc.h(q)
    return qc

def oracle(qc, answer):
    """
    Creates the oracle depending on the output wanted
    :param qc: quantum circuit
    :param answer: the wanted element
    :return: quantum circuit
    """
    answer = answer[::-1]

    zero = []
    one = []
    for i, val in enumerate(answer):
        if val:
            one.append(i)
        else:
            zero.append(i)
    if len(one) % 2 == 0 and len(one) > 0:
        for i, val in enumerate(one):
            if i % 2 == 1:
                qc.cz(one[i - 1], one[i])
    elif len(zero) % 2 == 0 and len(zero) > 0:
        for i, val in enumerate(zero):
            if i % 2 == 1:
                qc.x(zero[i - 1])
                qc.x(zero[i])
                qc.cz(zero[i - 1], zero[i])
                qc.x(zero[i - 1])
                qc.x(zero[i])
    elif len(one) % 2 == 1 and len(zero) > 0:
        for i, val in enumerate(one):
            if i < len(zero):
                qc.x(zero[i])
                qc.cz(zero[i], one[i])
                qc.x(zero[i])
    elif len(zero) % 2 == 1 and len(one) > 0:
        for i, val in enumerate(zero):
            if i < len(one):
                qc.x(zero[i])
                qc.cz(zero[i], one[i])
                qc.x(zero[i])
    return qc


def diffuser(qc, nqubits):
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
    return qc

def plot_results(probabilities_histogram):
    names = []
    values = []

    for state, val in probabilities_histogram.items():
        names.append(state)
        values.append(val)

    plt.bar(names, values)
    plt.xlabel('Probabilities')
    plt.ylabel('States')
    plt.title('Results')
    plt.show()



if __name__ == '__main__':

    authentication = get_authentication()
    QI.set_authentication(authentication, QI_URL)
    qi_backend = QI.get_backend('Starmon-5')

    q = QuantumRegister(2)
    b = ClassicalRegister(2)
    circuit = QuantumCircuit(q, b)

    circuit = initialize_s(circuit, [0, 1])
    circuit = oracle(circuit, [True, False])
    circuit = diffuser(circuit, 2)

    circuit.measure(q, b)

    print(circuit.draw())

    qi_job = execute(circuit, backend=qi_backend, shots=256)
    qi_result = qi_job.result()
    probabilities_histogram = qi_result.get_probabilities(circuit)
    plot_results(probabilities_histogram)
