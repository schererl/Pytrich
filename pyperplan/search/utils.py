def create_result_dict(h_name, status, iterations, h_init, h_avg, start_time, end_time, memory_usage, dist_to_goal, plan_lenght, solution=None):
    elapsed_time = end_time - start_time
    nodes_per_second = iterations / elapsed_time if elapsed_time > 0 else 0

    result = {
        'h_name': h_name,
        'status': status,
        'nodes_expanded': iterations,
        'h_init': h_init,
        'h_avg': h_avg,
        'elapsed_time': elapsed_time,
        'nodes_per_second': nodes_per_second,
        'dtg_lenght': dist_to_goal,
        'plan_lenght': plan_lenght,
        'memory_usage': memory_usage
    }
    
    if solution is not None:
        result['solution'] = solution

    return result