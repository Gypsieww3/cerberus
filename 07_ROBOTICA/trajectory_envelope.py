"""Single-axis torque envelope, preliminary only; no hardware-control output."""
import math

def _finite_nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return float(value)

def estimate_dynamic(mass_kg, center_of_mass_m, inertia_kg_m2, samples,
                     *, gear_ratio, efficiency, friction_nm=0.0, safety_factor=2.0,
                     measured_motor_continuous_nm=None):
    mass = _finite_nonnegative("mass", mass_kg)
    lever = _finite_nonnegative("center_of_mass", center_of_mass_m)
    inertia = _finite_nonnegative("inertia", inertia_kg_m2)
    friction = _finite_nonnegative("friction", friction_nm)
    gear = _finite_nonnegative("gear", gear_ratio)
    eff = _finite_nonnegative("efficiency", efficiency)
    factor = _finite_nonnegative("factor", safety_factor)
    if gear <= 0 or not 0 < eff <= 1 or factor < 1:
        raise ValueError("Invalid transmission or safety factor")
    series = list(samples)
    if not series or len(series) > 10000:
        raise ValueError("1..10000 motion samples required")
    motor_torques = []
    for item in series:
        angle = item["angle_rad"]
        accel = item["acceleration_rad_s2"]
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (angle, accel)):
            raise ValueError("Invalid motion sample")
        joint = mass * 9.80665 * lever * math.sin(angle) + inertia * accel
        # Conservative bound: add friction in either direction.
        motor = (abs(joint) + friction) * factor / (gear * eff)
        if not math.isfinite(motor):
            raise ValueError("Torque overflow")
        motor_torques.append(motor)
    peak = max(motor_torques)
    result = {"peak_motor_nm": peak, "samples": len(series), "status": "MEASUREMENT_REQUIRED",
              "scope": "Single axis estimate only; excludes impact, thermal duty, backlash, deformation and controls."}
    if measured_motor_continuous_nm is not None:
        continuous = _finite_nonnegative("continuous torque", measured_motor_continuous_nm)
        result["static_continuous_comparison"] = continuous >= peak
        result["status"] = "PRELIMINARY_COMPARISON_ONLY"
    return result
