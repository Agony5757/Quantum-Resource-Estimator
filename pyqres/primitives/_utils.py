def mcx_t_count(ncontrols):
    """T-count for multi-controlled X gate."""
    if ncontrols <= 1:
        return 0
    if ncontrols == 2:
        return 7
    return 16 * 7 * ncontrols
