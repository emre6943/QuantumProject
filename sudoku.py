from qiskit import *
from qiskit.providers.aer import QasmSimulator


class QC(QuantumCircuit):

    def cccx(self, c1c2, c3, t, invert=[False, False]):
        self.h(t)
        for i in range(4):
            j = i % 2
            if invert[j]:
                self.x(t)
            if not j:
                self.ccx(c1c2[0], c1c2[1], t)
                self.t(t)
            else:
                self.cx(c3, t)
                self.tdg(t)
        self.h(t)

    def ccccx(self, c12, c34, t, invert=[False, False]):
        self.h(t)
        for i in range(4):
            j = i % 2
            if invert[j]:
                self.x(t)
            if not j:
                self.ccx(c12[0], c12[1], t)
                self.t(t)
            else:
                self.ccx(c34[0], c34[1], t)
                self.tdg(t)
        self.h(t)

    def ncx(self, controls, ancilla, output, reverse=True):
        l = len(controls)
        if l == 1:
            self.cx(controls, output)
        elif l == 2:
            self.ccx(controls[0], controls[1], output)
        else:
            self.ccx(controls[0], controls[1], ancilla[0])
            self.ccx(controls[2:-1], ancilla[:l - 3], ancilla[1:l - 2])
            self.ccx(controls[-1], ancilla[l - 3], output)
            if reverse:
                self.ccx(controls[2:-1][::-1], ancilla[:l - 3][::-1], ancilla[1:l - 2][::-1])
                self.ccx(controls[0], controls[1], ancilla[0])

    def oracle_for_14(self, qc, cs, qr, qrc, qrr, qro, qrz, out, output=False):
        m = 0

        for x in cs:
            lst = chklst14[x]
            n = len(lst)
            M = m + 2 * n

            qc.cx(qr[2 * x:2 * x + 2] * n, qrc[m:M])
            qc.barrier(qrc[m:M])
            suj = []
            for el in lst:
                suj.extend(qr[2 * el:2 * el + 2])
            qc.cx(suj, qrc[m:M])
            qc.barrier(qr)

            m = M
        qc.barrier(qrc, qrr)
        # rekenen maar

        qc.ccx(qrc[::2], qrc[1::2], qrr[:(len(qrc) + 1) // 2])
        qc.ncx(qrr, qro, qrz, reverse=True)

        qc.barrier(qrr)

        qc.ccx(qrc[::-2], qrc[-2::-2], qrr[:(len(qrc) + 1) // 2][::-1])

        qc.barrier(qrc, qrr)

        for x in cs[::-1]:
            lst = chklst14[x]
            n = len(lst)
            m = M - 2 * n

            qc.cx(qr[2 * x:2 * x + 2][::-1] * n, qrc[m:M][::-1])
            qc.barrier(qrc[m:M])
            suj = []
            for el in lst:
                suj.extend(qr[2 * el:2 * el + 2])
            qc.cx(suj[::-1], qrc[m:M][::-1])
            qc.barrier(qr)

            M = m

    def oracle_for_44(self, qc, cs, out, qr, qrc, qrr, qro, qrz, output=False):
        qc = self

        m = 0

        for x in cs:
            lst = chklst44[x]
            n = len(lst)
            M = m + 2 * n

            qc.cx(qr[2 * x:2 * x + 2] * n, qrc[m:M])
            qc.barrier(qc.qrc[m:M])
            suj = []
            for el in lst:
                suj.extend(qr[2 * el:2 * el + 2])
            qc.cx(suj, qrc[m:M])
            qc.barrier(qr)

            m = M

        qc.barrier(qrc, qrr)

        qc.ccccx([qrc[:16:2], qrc[1:17:2]], [qrc[16::2], qrc[17::2]], qrr[:8], [True, True])
        qc.ccccx([qrr[:4:2], qrr[1:5:2]], [qrr[4:8:2], qrr[5:9:2]], qrr[8:10])
        qc.ccx(qrr[8], qrr[9], qro[out])

        if output:
            qc.barrier(qro, qrz)

            qc.ccccx(qro[:2], qro[2:4], qrz)
            # extra info test

            # qc.ccccx(qro[:2], qro[2:4], qro[-1])

            qc.barrier(qro, qrz)
            qc.ccx(qrr[8], qrr[9], qro[out])
        qc.ccccx([qrr[4:8:2], qrr[5:9:2]], [qrr[:4:2], qrr[1:5:2]], qrr[8:10])
        qc.barrier(qrr)
        qc.ccccx([qrc[16::2][::-1], qrc[17::2][::-1]], [qrc[:16:2][::-1], qrc[1:17:2][::-1]], qrr[:8][::-1],
                 [True, True])

        qc.barrier(qrc, qrr)

        for x in cs[::-1]:
            lst = chklst44[x]
            n = len(lst)
            m = M - 2 * n
            suj = []
            for el in lst:
                suj.extend(qr[2 * el:2 * el + 2])
            qc.cx(suj[::-1], qrc[m:M][::-1])

            qc.barrier(qrc[m:M])
            qc.cx(qr[2 * x:2 * x + 2][::-1] * n, qrc[m:M][::-1])

            qc.barrier(qr)

            M = m

    def apply_known(self, qc, qr, input):
        """Apply a grid if some numbers are already given."""
        for i in range(len(input)):
            x = input[i]
            if x == 'x':
                qc.h(qr[2 * i:2 * i + 2])
            else:
                if x > 1:
                    qc.x(qr[2 * i])
                if x % 2 == 1:
                    qc.x(qr[2 * i + 1])


def sudoku14(input=['x', 'x', 2, 3], simulate=True):
    """Method to solve 1x4 Sudoku. Input can specify if some numbers are already given."""
    qr = QuantumRegister(8, 'v')  # value  register
    qrc = QuantumRegister(12, 'c')  # check  register
    qrr = QuantumRegister(6, 'r')  # result register
    qro = QuantumRegister(4, 'o')  # output register
    qrz = QuantumRegister(1, 'z')  # z      register
    cr = ClassicalRegister(8, 'out')  # measurement out
    cr2 = ClassicalRegister(12, 'cc')
    cr3 = ClassicalRegister(6, 'cr')
    cr4 = ClassicalRegister(4, 'co')
    crt = ClassicalRegister(1, 'test')  # testing functionality
    qc = QC(qr, qrc, qrr, qro, qrz, cr)  # , crt)#, cr2, cr3, cr4)       #quantum circuit

    # initialize
    qc.apply_known(qc, qr, input)
    qc.x(qrc)
    qc.x(qrr)

    # create |-> state
    qc.x(qrz)
    qc.h(qrz)

    for r in range(1):
        # setup check 00, 01, 06
        qc.barrier()
        qc.oracle_for_14(qc, [0, 1, 2], qr, qrc, qrr, qro, qrz, 0, output=False)

        # diffuser
        # cancel initialization
        qc.barrier()
        qc.apply_known(qc, qr, input)
        qc.x(qrc)
        qc.x(qrr)

        # diffuse!
        qc.x(qr)
        qc.ncx(qr, qrc, qrz)
        # extra check
        # qc.x(qrz)
        qc.barrier()
        qc.x(qr)
        qc.x(qrc)
        qc.apply_known(qc, qr, input)

    qc.h(qrz)
    qc.x(qrz)

    # measurement
    qc.barrier()
    qc.measure(qr, cr[:len(qr)][::-1])

    # qc.measure(qrc, cr2[::-1])
    # qc.measure(qrr, cr3[::-1])
    # qc.measure(qro, cr4[::-1])
    # qc.measure(qrz, crt)

    # drawings
    # qc.draw(filename='14.txt', fold=-1)
    # qc.draw('latex_source', filename='14latex.txt', fold=-1)
    # qc.draw('mpl', filename='14mpl.png', fold=-1)

    if simulate:
        simulator = QasmSimulator(method='matrix_product_state')
        res = execute(qc, simulator, shots=1000).result()
        result = res.get_counts(qc)
        counts = dict(sorted(result.items(), key=lambda x: x[1]))
        print_result(counts)


def sudoku44(input=['x', 'x', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], simulate=True):
    """Method to solve 4x4 Sudoku. Input can specify if some numbers are already given."""
    qr = QuantumRegister(32, 'v')  # value  register
    qrc = QuantumRegister(32, 'c')  # check  register
    qrr = QuantumRegister(10, 'r')  # result register
    qro = QuantumRegister(8, 'o')  # output register
    qrz = QuantumRegister(1, 'z')  # z      register
    cr = ClassicalRegister(32, 'out')  # measurement out
    crt = ClassicalRegister(1, 'test')  # testing functionality
    crc = ClassicalRegister(32, 'crc')  # measure check
    crr = ClassicalRegister(10, 'crr')  # measure resultregister
    qc = QC(qr, qrc, qrr, qro, qrz, cr, crc, crr)  # quantum circuit

    qc.apply_known(qc, qr, input)
    qc.x(qrc)

    # create |-> state
    qc.x(qrz)
    qc.h(qrz)

    for r in range(1):
        # setup check 00, 01, 06
        qc.barrier()
        qc.x(qro[1:])
        qc.oracle_for_44(qc, [0], qr, qrc, qrr, qro, qrz, 0, output=True)  # [0,1,6]
        qc.x(qro[1:])
        '''
        qc.check([2, 3, 7, 8], 1)
        qc.check([4, 5, 9, 10], 2)
        qc.check([7, 8, 11, 12, 13], 3, output = True)
        qc.check([4, 5, 9, 10], 2)
        qc.check([2, 3, 7, 8], 1)
        qc.check([0,1,6], 0)
        '''

        # diffuser
        # cancel initialization
        qc.barrier()
        qc.apply_known(qc, qr, input)
        qc.x(qrc)

        # diffuse!
        qc.x(qr)
        qc.ccx(qr[0], qr[1], qrc[0])
        qc.ccx(qr[2:], qrc[:len(qr) - 2], qrc[1:len(qr) - 1])

        qc.cx(qrc[-2], qrz)
        # extra chek
        # qc.x(qrz)

        qc.ccx(qr[2:][::-1], qrc[:len(qr) - 2][::-1], qrc[1:len(qr) - 1][::-1])
        qc.ccx(qr[0], qr[1], qrc[0])
        qc.barrier()
        qc.x(qr)

        qc.x(qrc)
        qc.apply_known(qc, qr, input)

    qc.h(qrz)
    qc.x(qrz)
    # measurement
    qc.barrier()
    qc.measure(qr, cr[::-1])
    qc.measure(qrc, crc[::-1])
    qc.measure(qrr, crr[::-1])
    # qc.measure(qro[-1], crt)
    qc.draw(filename='44.txt', fold=-1)

    if simulate:
        simulator = QasmSimulator(method='matrix_product_state')
        print('2')
        res = execute(qc, simulator, shots=4000).result()
        print(res)
        result = res.get_counts(qc)
        counts = dict(sorted(result.items(), key=lambda x: x[1])[-20:])
        print_result(counts)


chklst14 = [[1, 2, 3], [2, 3], [3]]
chklst44 = [[1, 2, 3, 4, 5, 8, 12], [2, 3, 4, 5, 9, 13], [3, 6, 7, 10, 14], [6, 7, 11, 15], [5, 6, 7, 8, 12],
            [6, 7, 9, 13], [7, 10, 14], [11, 15], [9, 10, 11, 12, 13], [10, 11, 12, 13], [11, 14, 15], [14, 15],
            [13, 14, 15], [14, 15], [15]]


def print_result(result):
    s = str(result)
    r = s.replace(',', '\n')
    print(r)

if __name__ == '__main__':
    # the default input here is a row with [X, X, 2, 3] where X is a number that should be found with Grover's algorithm
    sudoku14()
