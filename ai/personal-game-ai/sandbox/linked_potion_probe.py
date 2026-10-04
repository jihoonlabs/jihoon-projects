from linked_health_probe import heal

def use_potion(hp, maximum, count):
    if count <= 0 or hp >= maximum:
        return (hp, count)
    else:
        new_hp = heal(hp, 4, maximum)
        return (new_hp, count - 1)
