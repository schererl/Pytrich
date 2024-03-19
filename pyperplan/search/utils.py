def create_result_dict(status, iterations, initial_heuristic, h_sum, start_time, end_time, memory_usage, s_size, o_size, solution=None):
    elapsed_time = end_time - start_time
    h_avg = h_sum / iterations if iterations > 0 else 0
    nodes_per_second = iterations / elapsed_time if elapsed_time > 0 else 0

    result = {
        'status': status,
        'nodes_expanded': iterations,
        'h_init': initial_heuristic,
        'h_avg': h_avg,
        'elapsed_time': elapsed_time,
        'nodes_per_second': nodes_per_second,
        's_size': s_size,
        'o_size': o_size,
        'memory_usage': memory_usage
    }
    
    if solution is not None:
        result['solution'] = solution

    return result