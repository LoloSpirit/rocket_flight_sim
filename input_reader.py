from rocket_flight_sim.stage import Stage


def read_staging_output(filename):
    with open(filename, 'r') as f:
        # Parse line by line, stripping units and converting kg to tons
        lines = f.readlines()
    stage1_dry = None
    stage2_dry = None
    stage1_prop = None
    stage2_prop = None
    c_1 = None
    c_2 = None
    MassFlow_1 = None
    MassFlow_2 = None
    engine_weight = None
    payload = None
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, val = line.split(':', 1)
        val = val.strip()
        # Remove units (e.g. 'kg', 'm/s', 'kg/s')
        val_num = val.split()[0]
        if key.lower().startswith("m_dry_1"):
            stage1_dry = float(val_num) / 1000
        elif key.lower().startswith("m_dry_2"):
            stage2_dry = float(val_num) / 1000
        elif key.lower().startswith("m_propellant_1"):
            stage1_prop = float(val_num) / 1000
        elif key.lower().startswith("m_propellant_2"):
            stage2_prop = float(val_num) / 1000
        elif key.strip() == "c_1":
            c_1 = float(val_num)
        elif key.strip() == "c_2":
            c_2 = float(val_num)
        elif key.strip() == "MassFlow_1":
            MassFlow_1 = float(val_num)
        elif key.strip() == "MassFlow_2":
            MassFlow_2 = float(val_num)
        elif key.lower().startswith("engine weight"):
            engine_weight = float(val_num) / 1000
        elif key.lower().startswith("payload"):
            payload = float(val_num) / 1000

    stage1 = Stage(stage1_dry, stage1_prop, c_1, MassFlow_1, 0)
    stage2 = Stage(stage2_dry, stage2_prop, c_2, MassFlow_2, payload)
    return stage1, stage2