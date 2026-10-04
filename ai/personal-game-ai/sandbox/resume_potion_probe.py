from resume_health_probe import heal

def use_potion(hp, maximum, count):
    if count == 0 or hp == maximum:
        return (hp, count)
    else:
        new_hp = heal(hp, 4, maximum)
        new_count = count - 1
        return (new_hp, new_count)
