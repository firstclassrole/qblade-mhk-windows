# Cross-flow routing and conventions

Read this when the user asks for transverse flow, VAWT, Darrieus, waterwheel, bucket or tangential-jet layouts. First identify the energy source, shaft direction, immersion and blade geometry; do not assume that every “cross-flow turbine” is the same machine.

| Layout | Geometry and analysis boundary |
|---|---|
| Axial HAWT | Shaft approximately parallel to current; blades extend radially. Use HAWT geometry/BEM. Radial span and hub radius set the nominal tip diameter. |
| Lift-driven Darrieus/H-rotor | Shaft perpendicular to current. In QBlade, use VAWT geometry with independent station Height, Radius, Chord, Twist and foil/polar selection, followed by DMS/AC preliminary analysis. For a straight constant-radius rotor, full-height projected area is 2RH; confirm the selected output normalization rather than applying πR². |
| Partial-immersion waterwheel | In/out-of-water loading and free surface are essential. A 90° HAWT rotation does not supply the correct blade motion, wet area or loads. Use an appropriate free-surface model and experiment; do not transplant BEM curves. |
| Savonius | Drag-driven/separated-flow rotor. QBlade's official developer says its methods are unsuitable; do not sell DMS/AC as Savonius validation. |
| Pelton / Banki–Michell | Head/nozzle-driven impulse machines, distinct from uniform-current Darrieus rotors. Establish net head, flow and nozzle conditions; a nozzle does not create available energy. |

For a VAWT conversion, make a separate blade/project variant and define height and radius independently from the available width/depth/clearance. Preserve the axial baseline. A specified 200 mm blade length may become axial height, not radial reach; retain the user's intent while making that dimension choice explicit. Do not introduce “optimized” chord, radius, pitch or TSR defaults without evidence.

Use [official VAWT geometry](https://docs.qblade.org/src/user/blade/blade.html#vawt-blade-design) and [DMS/AC documentation](https://docs.qblade.org/src/user/bem/dms.html). Inspect upstream/downstream passages, azimuth-varying angle of attack, local Reynolds number, instantaneous torque and mean torque, dynamic stall and strut/support effects when relevant. Positive mean torque at prescribed RPM does not establish self-starting; startup also needs static-angle torque, inertia and resisting torque.

The [official coordinate guide](https://docs.qblade.org/src/user/coordinates/coordinates.html) defines different HAWT and VAWT azimuth/pitch conventions. Do not transfer the axial twist sign or zero-pitch interpretation blindly: VAWT zero pitch uses a chord tangent to the rotation path. Confirm flow/axis/rotation directions and the current UI convention before editing geometry.

For water, check the [QBlade MHK settings](https://docs.qblade.org/src/user/turbine/marinehydrokinetic.html): fields retaining “Air” names may need water density and viscosity. The baseline fluid properties are assumptions unless temperature/water quality are known. Do not let the simulation's displayed wind terminology silently retain air properties.

The bundled binary extractor is limited to the verified HAWT Rotor BEM schema. Do not run it on DMS/AC/VAWT just because a QPR has the same archive header. Use native DMS exports and verify that module's reference area, coefficients and dimensional availability. If undocumented, inspect actual data and sources rather than forcing an axial mapping.

Primary sources checked on 2026-10-27:

- [QBlade DMS theory](https://docs.qblade.org/src/theory/aerodynamics/dms/dmst.html): separate upstream/downstream streamtube treatment.
- [DOE marine-energy glossary](https://www.energy.gov/cmei/water/marine-energy-glossary): axial versus current-driven cross-flow technology classes.
- [DOE hydropower turbine types](https://www.energy.gov/cmei/water/types-hydropower-turbines): Pelton and nozzle-fed Banki/Michell cross-flow impulse machines.
- [QBlade official Savonius reply, 2025-02-27](https://qblade.org/qblade-forum/topic/savonius-wind-turbine-simulation-in-qblade/): drag/separation mechanisms are outside its methodology; finite-volume methods are ordinarily used.
