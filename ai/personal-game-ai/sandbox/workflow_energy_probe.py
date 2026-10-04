def consume_energy(energy, cost):
    """
    에너지를 소비합니다.

    Args:
        energy (int): 현재 에너지 수치 (0 이상)
        cost (int): 소비할 에너지 수치 (0 이상)

    Returns:
        int: 소비 후 남은 에너지 수치 (음수는 없음)
    """
    return max(energy - cost, 0)
