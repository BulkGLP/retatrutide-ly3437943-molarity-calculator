"""Theoretical net-parent-mass arithmetic, not an experimental protocol."""
from decimal import Decimal, InvalidOperation, localcontext

STANDARD_FINAL_VOLUMES_ML = ('1.0', '1.5', '2.0', '2.5')

def calculate(mass_mg, final_volume_ml, molar_mass_g_mol):
    try:
        mass, volume, molar_mass = (Decimal(str(x)) for x in (mass_mg, final_volume_ml, molar_mass_g_mol))
        if any(not n.is_finite() or n <= 0 for n in (mass, volume, molar_mass)):
            raise ValueError('Inputs must be finite positive numbers; unknown species have no molarity.')
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('A known species, positive net parent mass and final volume are required.') from exc
    with localcontext() as context:
        context.prec = 40
        concentration = mass / volume  # mg/mL is numerically equal to g/L
        molarity_mM = concentration * 1000 / molar_mass
        return dict(mass_concentration_mg_ml=f'{concentration:.8f}', molarity_mM=f'{molarity_mM:.8f}', molarity_uM=f'{molarity_mM * 1000:.8f}')
