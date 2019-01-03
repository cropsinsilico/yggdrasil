_lookup_overhead = {
    'c': 0.55,
    'c++': 0.63,
    'cpp': 0.63,
    'matlab': 10.85,
    'python': 1.43}


def calculate_speedup(src_lang, dst_lang, nloops,
                      tinitA, t1A, t2A, t3A, tfinalA,
                      tinitB, t1B, t2B, t3B, tfinalB,
                      t_comm=None, T_overhead=None):
    r"""Function to calculate the speedup resulting from parallelism and
    asynchronous communication between two models.

    Args:
        src_lang (str): Source language.
        dst_lang (str): Destination language.
        nloops (int): Number of loops in integration.
        tinitA (float): Duration of Initial Phase in Model A (before loop).
        t1A (float): Duration of 1st Phase in Model A (before sending).
        t2A (float): Duration of 2nd Phase in Model A (between sending and receiving).
        t3A (float): Duration of 3rd Phase in Model A (after receiving).
        tfinalA (float): Duration of Final Phase in Model A (after loop).
        tinitB (float): Duration of Initial Phase in Model B (before loop).
        t1B (float): Duration of 1st Phase in Model B (before receiving).
        t2B (float): Duration of 2nd Phase in Model B (between receiving and sending).
        t3B (float): Duration of 3rd Phase in Model B (after sending).
        tfinalB (float): Duration of Final Phase in Model B (after loop).
        t_comm (float, optional): Time required to move a message from an output
            of one model to the input of another. Defaults to a value based on a
            lookup table for communication between different langauges.
        T_overhead (float, optional): Time required to setup an integration and
            start both models on their own processes. Defaults to a value based on
            a lookup table for starting different langauges.

    Returns:
        float: Speedup.

    """
    # Set defaults
    if t_comm is None:
        if src_lang.lower() == 'matlab':
            if dst_lang.lower() == 'matlab':
                t_comm = 0.53
            else:
                t_comm = 0.14
        elif dst_lang.lower() == 'matlab':
            t_comm = 0.51
        else:
            t_comm = 0.02
        print("t_comm(%s to %s) = %f s/msg" % (src_lang, dst_lang, t_comm))
    if T_overhead is None:
        T_overhead = _lookup_overhead[src_lang] + _lookup_overhead[dst_lang]
        print("T_overhead(%s to %s) = %f s" % (src_lang, dst_lang, T_overhead))
    # Calculate parallel execution time
    iloop = 0
    T_A = tinitA
    T_B = tinitB
    while (iloop < nloops):
        T_A += t1A
        T_B += t1B
        T_B = max(T_A, T_B + t_comm)
        T_A += t2A
        T_B += t2B
        T_A = max(T_A + t_comm, T_B)
        T_A += t3A
        T_B += t3B
        iloop += 1
    T_A += tfinalA
    T_B += tfinalB
    T_parallel = T_overhead + max(T_A, T_B)
    # Calculate serial time
    T_serial = (tinitA + nloops*(t1A + t2A + t3A) + tfinalA
                + tinitB + nloops*(t1B + t2B + t3B) + tfinalB)
    # Calculate speedup
    S = T_serial/T_parallel
    print("T_serial   = %f s" % T_serial)
    print("T_parallel = %f s" % T_parallel)
    print("Speedup = %f" % S)
    return S


if __name__ == '__main__':
    src_lang = 'python'
    dst_lang = 'python'
    nloops = 100
    tinitA = 0.1
    tinitB = 0.2
    t1A = 1.0
    t1B = 0.3
    t2A = 1.2
    t2B = 2.0
    t3A = 0.1
    t3B = 0.05
    tfinalA = 0.1
    tfinalB = 0.1
    calculate_speedup(src_lang, dst_lang, nloops,
                      tinitA, t1A, t2A, t3A, tfinalA,
                      tinitB, t1B, t2B, t3B, tfinalB)
