"""Single lumped-load gravity estimate, not a robot or actuator qualification."""
import math


def estimate(mass_kg,lever_m,angle_deg=90,gear_ratio=1,efficiency=1,design_factor=2,motor_continuous_nm=None):
    values=(mass_kg,lever_m,angle_deg,gear_ratio,efficiency,design_factor)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
        raise ValueError('Finite numeric inputs required')
    if mass_kg<0 or lever_m<0 or not 0<=angle_deg<=180 or gear_ratio<=0 or not 0<efficiency<=1 or design_factor<1:
        raise ValueError('Invalid physical parameters')
    torque=mass_kg*9.80665*lever_m*abs(math.sin(math.radians(angle_deg)))
    required=torque*design_factor/(gear_ratio*efficiency)
    if not math.isfinite(torque) or not math.isfinite(required):raise ValueError('Derived torque overflow')
    result=dict(gravity_joint_nm=torque,factored_joint_nm=torque*design_factor,required_motor_nm=required,
        state='MOTOR_MEASUREMENT_REQUIRED',angle_convention='Angle from gravity direction; 90 degrees is maximum lever torque',
        scope='One static lumped load. Excludes acceleration, impact, friction, stiffness, backlash, temperature and support geometry.')
    if motor_continuous_nm is not None:
        if isinstance(motor_continuous_nm,bool) or not isinstance(motor_continuous_nm,(int,float)) or not math.isfinite(motor_continuous_nm) or motor_continuous_nm<0:
            raise ValueError('Invalid measured continuous torque')
        available=motor_continuous_nm*gear_ratio*efficiency
        if not math.isfinite(available):raise ValueError("Available torque overflow")
        result.update(available_joint_nm=available,
            static_margin_nm=motor_continuous_nm*gear_ratio*efficiency-torque*design_factor,
            meets_static_estimate=motor_continuous_nm>=required,state='STATIC_COMPARISON_ONLY')
    return result
