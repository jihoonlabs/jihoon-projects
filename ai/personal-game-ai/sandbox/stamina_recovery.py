def calculate_stamina_recovery(current_stamina, max_stamina, recovery_amount):
    if current_stamina < 0 or max_stamina < 0 or recovery_amount < 0:
        raise ValueError("Inputs must be non-negative.")
    
    new_stamina = current_stamina + recovery_amount
    return min(new_stamina, max_stamina)
