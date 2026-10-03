def bounded_step(value, delta, maximum):
    result = value + delta
    if result < 0:
        return 0
    elif result > maximum:
        return maximum
    else:
        return result
