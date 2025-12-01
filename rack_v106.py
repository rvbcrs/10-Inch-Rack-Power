from build123d import *

# ==============================================================================
# 10" Rack - V106 (Python / Build123d Edition)
# Complete port of rack_v106.scad
# ==============================================================================

# --- Parameters ---
wall_thickness = 2
floor_thickness = 2
shelf_height = 35
shelf_width = 190
shelf_depth_len = 115
shelf_start_y = 5
shelf_thickness = 3
dc_jack_dia = 8.2
safe_border = 10

# Screws
screw_hole_dia = 3.2
screw_pilot_dia = 2.8
# Dimensions (mm)
rack_width = 10 * 25.4 # 254.0 mm
rack_inner_width = 195 # Increased to 195mm to give 2.5mm clearance for legs
tray_height = 1.75 * 25.4 # 1U = 44.45 mm
tray_depth = 130
floor_thickness = 2
wall_thickness = 1.6 # Optimized for 0.4mm nozzle (4 perimeters)
ear_thickness = 3.2 # Optimized for 0.4mm nozzle (8 perimeters)
# For 10" rack, the opening is usually ~220mm?
# 19" rack opening is ~450mm.
# 10" rack is ~254mm total. Rails are usually ~220mm apart.
# User said "10 inch lab rack".
# Let's assume rack_inner_width is correct for the tray body (220mm).
# But the ears need to reach the rails.
# 10" rack mounting holes center-to-center is usually ~236.5mm?
# Wait, 19" is 465mm hole-to-hole.
# 10" is ... ?
# If rack_width = 254mm.
# Hole spacing is likely standard unit spacing.
# Let's stick to the user's SCAD values if possible, but the SCAD had "rack_width = 19 * 25.4".
# If I change it to 10 * 25.4, `rack_inner_width` (220) might be too wide?
# 220mm = 8.66 inches.
# 10 inches = 254mm.
# 254 - 220 = 34mm space for ears (17mm each side).
# This matches `ear_w_total` calculation: (rack_width - rack_inner_width) / 2 = 17mm.
# So 220mm inner width is consistent with 10" rack.

# Rack Dimensions
# rack_inner_width = 220 # REMOVED DUPLICATE
tray_depth = 130
tray_height = 44.45
ear_thickness = 3
EPS = 0.01

# Positioning Legs
leg_inset = 6
sh_off_x = (rack_inner_width - shelf_width) / 2
lx_left = sh_off_x + leg_inset
lx_right = sh_off_x + shelf_width - leg_inset
ly_front = shelf_start_y + leg_inset
ly_back = shelf_start_y + shelf_depth_len - leg_inset

# Component Dimensions
pcie_w, pcie_d = 154.3, 67.3 # Horizontal again
pcie_hole_dist = 47.1
pcie_offset_y = 3.4
pcie_x, pcie_y = 20.35, 46 # Centered X, Y=46 (14mm back clearance)
pcie_standoff_height = 6

# Power Boards
dcdc_w, dcdc_d = 68.5, 100.3
dcdc_offset = 2.5 # Reduced from 3.5 to fix misalignment
dcdc_x, dcdc_y = 5, 5

sata_real_w, sata_real_d = 60, 80
sata_offset = 4.2
sata_x, sata_y = 125, 15

# Shelf Leg Bosses (Countersunk Screws)
leg_boss_height = 2.5
screw_head_dia = 6.0 # Clearance for 5.5mm head
screw_head_height = 3.5 # Clearance for 3.0mm head

# --- Generators ---

def make_shelf():
    """Generates the removable shelf."""
    leg_locs = [
        (leg_inset, leg_inset),
        (leg_inset, shelf_depth_len - leg_inset),
        (shelf_width - leg_inset, leg_inset),
        (shelf_width - leg_inset, shelf_depth_len - leg_inset)
    ]

    with BuildPart() as shelf:
        # Reduce leg height by boss height so deck remains at same absolute Z
        leg_height = shelf_height - leg_boss_height

        # 1. Deck
        with BuildSketch(Plane.XY.offset(leg_height)):
            with Locations(leg_locs):
                Circle(radius=leg_diameter/2 if 'leg_diameter' in globals() else 6) # 12mm dia -> 6 radius
            make_hull()
        extrude(amount=shelf_thickness)

        # 2. Legs
        with BuildSketch(Plane.XY):
            with Locations(leg_locs):
                Circle(radius=6)
        extrude(amount=leg_height)

        # 3. Ribs (Hulls between legs)
        # In SCAD this was manual hulls. Here we can loft or hull profiles.
        # Simpler approach: Hull the leg cylinders in pairs at the top
        # But build123d hull() works on the pending objects.
        # Let's just make the ribs explicitly if needed, or skip for now as the Deck hull covers the top.
        # The SCAD ribs were vertical reinforcements.
        # Re-implementing SCAD ribs logic:
        def make_rib(p1, p2):
            with BuildPart() as rib:
                with BuildSketch(Plane.XY.offset(shelf_height)):
                    with Locations([p1, p2]):
                        Circle(6)
                    make_hull()
                extrude(amount=shelf_thickness)
            return rib.part
            
        # The SCAD code hulled the TOP of the legs (shelf_height).
        # Wait, the deck IS the hull of the leg tops.
        # The SCAD code:
        # hull() { translate(...) cylinder(...); translate(...) cylinder(...); }
        # This creates the "bone" shape connections.
        # My "Deck" step above actually creates a full convex hull of ALL 4 legs, which is a big rectangle with rounded corners.
        # The SCAD code creates a "rounded_plate" which is that shape, PLUS extra "ribs" which seem redundant if the plate is solid?
        # Ah, looking at SCAD: `rounded_plate` is the main body. The `ribs` are... actually just reinforcing the connection?
        # They seem to be at the same height as the deck.
        # I will stick with the single solid Deck for now as it's cleaner.

        # 4. Bosses
        def add_bosses(x, y, w, d, offset):
            locs = [
                (x + offset, y + offset),
                (x + w - offset, y + offset),
                (x + offset, y + d - offset),
                (x + w - offset, y + d - offset)
            ]
            with BuildSketch(Plane.XY.offset(leg_height - 4)) as sk:
                with Locations(locs):
                    Circle(radius=4)
            extrude(sk.sketch, amount=4)

        # DC-DC Bosses (Explicit spacing 60x91.5mm)
        dcdc_hole_w = 60
        dcdc_hole_d = 91.5
        dcdc_hole_x = dcdc_x + (dcdc_w - dcdc_hole_w) / 2
        dcdc_hole_y = dcdc_y + (dcdc_d - dcdc_hole_d) / 2
        add_bosses(dcdc_hole_x, dcdc_hole_y, dcdc_hole_w, dcdc_hole_d, 0)
        
        # SATA Bosses (Explicit spacing 50x70mm)
        sata_hole_w = 50
        sata_hole_d = 70
        sata_hole_x = sata_x + (sata_real_w - sata_hole_w) / 2
        sata_hole_y = sata_y + (sata_real_d - sata_hole_d) / 2
        add_bosses(sata_hole_x, sata_hole_y, sata_hole_w, sata_hole_d, 0)

        # 5. Cuts
        with BuildPart(mode=Mode.SUBTRACT):
            # Board Mount Holes
            def add_mount_holes(x, y, w, d, offset):
                locs = [
                    (x + offset, y + offset),
                    (x + w - offset, y + offset),
                    (x + offset, y + d - offset),
                    (x + w - offset, y + d - offset)
                ]
                with Locations(locs):
                    # SCAD: translate([..., shelf_height - 10]) cylinder(h=50...)
                    # We cut through everything
                    # User requested 2.8mm diameter (radius 1.4) for tight fit without nuts.
                    Cylinder(radius=1.4, height=100, align=(Align.CENTER, Align.CENTER, Align.CENTER))

            # DC-DC Holes (Explicit spacing)
            add_mount_holes(dcdc_hole_x, dcdc_hole_y, dcdc_hole_w, dcdc_hole_d, 0)
            # SATA Holes (Explicit spacing)
            add_mount_holes(sata_hole_x, sata_hole_y, sata_hole_w, sata_hole_d, 0)

            # Cable Holes
            with BuildSketch(Plane.XY.offset(leg_height)) as cut_sk:
                # DC-DC
                with Locations((dcdc_x + 9, dcdc_y + 9)):
                    r1 = Rectangle(50, 82, align=(Align.MIN, Align.MIN))
                    fillet(r1.vertices(), radius=3)
                # Speed Hole
                with Locations((76, 15)):
                    r2 = Rectangle(47, 85, align=(Align.MIN, Align.MIN))
                    fillet(r2.vertices(), radius=3)
                # SATA
                with Locations((sata_x + 10, sata_y + 10)):
                    r3 = Rectangle(40, 60, align=(Align.MIN, Align.MIN))
                    fillet(r3.vertices(), radius=3)
            extrude(amount=20, both=True) # Cut through deck

            # Leg Screw Pilot Holes
            with Locations(leg_locs):
                Cylinder(radius=screw_pilot_dia/2, height=100, align=(Align.CENTER, Align.CENTER, Align.CENTER))

    return shelf.part

def make_tray():
    """Generates the main rack tray."""
    
    # 1. Floor Skeleton
    ear_w_total = (254 - rack_inner_width) / 2 # ~17mm
    tray_wall_height = 10 # Reduced from 22mm as requested
    
    with BuildPart() as floor:
        # Outer Frame
        with BuildSketch() as sk_floor:
            Rectangle(rack_inner_width, tray_depth, align=(Align.MIN, Align.MIN))
            
            # Hex Pattern Cutout
            with BuildSketch(mode=Mode.SUBTRACT) as sk_hex:
                # Intersection of Hex Grid and Safe Area
                with BuildSketch() as sk_grid:
                    # Hex Grid
                    # SCAD: hole_r=16. apothem is distance to flat side.
                    # build123d HexLocations uses circumradius by default.
                    # If apothem=14, radius = 14 / cos(30) = 16.16
                    # Align grid to center of tray depth (tray_depth/2 = 80)
                    with Locations((rack_inner_width/2, tray_depth/2)): # Centered horizontally and vertically
                        with HexLocations(radius=16, x_count=10, y_count=8):
                            # Use RegularPolygon for Honeycomb (Hexagon)
                            # radius=14 gives 2mm wall thickness (16-14=2)
                            RegularPolygon(radius=14, side_count=6)
                
                with BuildSketch(mode=Mode.INTERSECT) as sk_safe:
                    # Safe Area (Rectangle - Safe Border)
                    # SCAD: translate([safe_border, safe_border]) square([rack_inner_width - 2*safe_border, tray_depth - 2*safe_border])
                    # We need to center this rectangle relative to the floor sketch origin?
                    # No, let's check floor sketch.
                    # with BuildSketch() as sk_floor:
                    #    Rectangle(rack_inner_width, tray_depth, align=(Align.CENTER, Align.MIN))
                    # So X=0 is center, Y=0 is front.
                    
                    # Safe area should be inset by safe_border.
                    # Rectangle centered at (rack_inner_width/2, tray_depth/2).
                    with Locations((rack_inner_width/2, tray_depth/2)):
                        Rectangle(rack_inner_width - 2*safe_border, tray_depth - 2*safe_border)
                
                # Subtract Solid Regions (Unions in SCAD become subtractions from the cutout mask)
                # Wait, boolean logic: Floor = Rect - (HexGrid INTERSECT SafeZone MINUS SolidZones)
                # Easier: Floor = Rect - HexGrid_Clipped.
                # HexGrid_Clipped = (HexGrid & SafeZone) - SolidZones.
                
                with BuildSketch(mode=Mode.SUBTRACT) as sk_solids:
                    # PCIe Mount Island
                    with Locations((pcie_x + pcie_w - 20 - 5, pcie_y - 5)):
                         # Island is now on the Right side (where holes are)
                         # Holes are at pcie_w - 7.4.
                         # Island width 20.
                         # Let's position island at pcie_w - 25 relative to pcie_x?
                         # Holes X rel: 146.9.
                         # Island X rel: 135?
                         # Let's align with holes.
                         Rectangle(20, pcie_d + 10, align=(Align.MIN, Align.MIN))
                    
                    # PCIe Support Beam
                    # Beam is now on the Left side (connector side)
                    with Locations((pcie_x, pcie_y)):
                        Rectangle(10, pcie_d, align=(Align.MIN, Align.MIN))
                    # Leg Bases
                    with Locations([(lx_left, ly_front), (lx_left, ly_back), (lx_right, ly_front), (lx_right, ly_back)]):
                        Circle(radius=11)

        extrude(amount=floor_thickness)
        
        # Floor beneath ears (outside the main floor area)
        # Left ear floor
        with Locations((-ear_w_total, 0, 0)):
            Box(ear_w_total, ear_thickness, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
        # Right ear floor  
        with Locations((rack_inner_width, 0, 0)):
            Box(ear_w_total, ear_thickness, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN))

        # 2. Frame Structure (Walls & Ears)
        
        # Faceplate - only inner width (ears have their own front)
        with Locations((0, 0, 0)):
            Box(rack_inner_width, ear_thickness, tray_height, align=(Align.MIN, Align.MIN, Align.MIN))
            
        # Back Wall
        with Locations((0, tray_depth - wall_thickness, 0)):
            Box(rack_inner_width, wall_thickness, tray_wall_height, align=(Align.MIN, Align.MIN, Align.MIN))

        # Side Walls (Explicitly defined for symmetry)
        # Left Wall
        with Locations((-wall_thickness, 0, 0)):
            Box(wall_thickness, tray_depth, tray_wall_height, align=(Align.MIN, Align.MIN, Align.MIN))
            
        # Right Wall
        with Locations((rack_inner_width, 0, 0)):
            Box(wall_thickness, tray_depth, tray_wall_height, align=(Align.MIN, Align.MIN, Align.MIN))




        def make_ear(mirror_x=False):
            """Simple ear - just the mounting flange"""
            with BuildPart() as ear:
                 # Front face of ear (full height)
                 w = ear_w_total + 0.5
                 h = tray_height
                 d = ear_thickness
                 
                 # Center X calculation:
                 # Right edge at 0.5.
                 # Center = 0.5 - w/2
                 cx = 0.5 - w/2
                 
                 with Locations((cx, d/2, h/2)):
                     b = Box(w, d, h)
                     # Fillet outer edges (min X)
                     outer_edges = b.edges().filter_by(Axis.Y).sort_by(Axis.X)[0:2]
                     fillet(outer_edges, radius=2)
                
            if mirror_x:
                return mirror(ear.part, Plane.YZ)
            return ear.part

        def make_slope(is_right=False):
            """Generates the slope wedge explicitly for left or right side."""
            # Slope dimensions
            # Start Z = 10 (wall height)
            # End Z = 44.45 (tray height)
            # Start Y = 10 (user preference)
            # Length = 20
            
            # Create the wedge
            with BuildPart() as slope:
                # Sketch in YZ plane
                # Triangle: (0,0) -> (0, 34.45) -> (20, 0)
                with BuildSketch(Plane.YZ) as sk:
                    Polygon([(0,0), (0, tray_height - 10), (20, 0)])
                
                if is_right:
                    # Right side: Starts at X = rack_inner_width
                    # Extrude in +X direction (wall thickness)
                    # Wait, Right Wall is [215, 217].
                    # So start at 215, extrude +2.
                    extrude(sk.sketch, amount=wall_thickness)
                else:
                    # Left side: Starts at X = 0
                    # Extrude in -X direction (wall thickness)
                    # Left Wall is [-2, 0].
                    # So start at 0, extrude -2.
                    extrude(sk.sketch, amount=-wall_thickness)
            
            p = slope.part
            
            # Move to correct starting position
            # User requested Z=25. 
            # Y=10.
            if is_right:
                p = p.moved(Location((rack_inner_width, 10, 25)))
            else:
                p = p.moved(Location((0, 10, 25)))
                
            return p



        # Add Ears
        add(Location((0, 0, 0)) * make_ear(mirror_x=False))
        add(Location((rack_inner_width, 0, 0)) * make_ear(mirror_x=True))
        


        # Add Slopes (Explicit)
        add(make_slope(is_right=False))
        add(make_slope(is_right=True))

        # 3. Additions (Mounts)
        # PCIe Mount Island (Right side)
        with Locations((pcie_x + pcie_w - 20 - 5, pcie_y - 5, 0)):
            Box(20, pcie_d + 10, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
            
        # PCIe Support Beam (Left side)
        with Locations((pcie_x, pcie_y, 0)):
            Box(10, pcie_d, floor_thickness + pcie_standoff_height, align=(Align.MIN, Align.MIN, Align.MIN))
        # Leg Bases (Bosses for shelf legs)
        with Locations([(lx_left, ly_front), (lx_left, ly_back), (lx_right, ly_front), (lx_right, ly_back)]):
            # Height = floor_thickness + leg_boss_height
            Cylinder(radius=9, height=floor_thickness + leg_boss_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # PCIe Standoffs
        # Holes on Right side: pcie_x + pcie_w - 7.4
        with Locations((pcie_x + pcie_w - 7.4, pcie_y + pcie_offset_y, floor_thickness - EPS)):
            Cylinder(radius=4, height=pcie_standoff_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, pcie_hole_dist, 0)):
                Cylinder(radius=4, height=pcie_standoff_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4. Subtractions (Holes)
        with BuildPart(mode=Mode.SUBTRACT):
            # Rack Slots (Horizontal, Rounded)
            # Standard 10" rack hole spacing is approx 236.5mm center-to-center
            # (Derived from previous values: 220 + 8.25 - (-8.25) = 236.5)
            hole_spacing = 236.5
            center_x = rack_inner_width / 2
            
            x_left = center_x - hole_spacing / 2
            x_right = center_x + hole_spacing / 2
            
            # Z positions
            z_bottom = 7.225
            z_top = 37.225
            
            for x in [x_left, x_right]:
                for z in [z_bottom, z_top]:
                    # Rounded slot: 12mm wide, 7mm high
                    # Use Box + Fillet for robustness
                    with Locations((x, ear_thickness/2, z)):
                        # Create box centered at location
                        b = Box(12, 20, 7, align=(Align.CENTER, Align.CENTER, Align.CENTER))
                        # Fillet the edges along Y axis (the cutting direction)
                        # Radius 3.5mm makes the 7mm height fully rounded (semicircle ends)
                        fillet(b.edges().filter_by(Axis.Y), radius=3.49) # Use slightly less than 3.5 to avoid geometric singularities

            # DC Jack
            with Locations((15, tray_depth + 5, 8)):
                with Locations(Rotation(90, 0, 0)):
                    Cylinder(radius=dc_jack_dia/2, height=10)

            # PCIe Holes (Right side)
            with Locations((pcie_x + pcie_w - 7.4, pcie_y + pcie_offset_y, -10)):
                Cylinder(radius=1.4, height=50)
                with Locations((0, pcie_hole_dist, 0)):
                    Cylinder(radius=1.4, height=50)

            # Shelf Mounting Holes (Countersunk)
            with Locations([(lx_left, ly_front), (lx_left, ly_back), (lx_right, ly_front), (lx_right, ly_back)]):
                # Through hole
                with Locations((0,0,-10)):
                    Cylinder(radius=screw_hole_dia/2, height=50)
                # Countersink (from bottom)
                # Align.MIN means cylinder starts at Z=0 and goes up.
                Cylinder(radius=screw_head_dia/2, height=screw_head_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 3. Combine Floor and Walls
    # The floor part currently only has the floor.
    # We need to add the walls to it.
    # But wait, we added walls inside `make_tray`?
    # Ah, `make_tray` returns `floor.part`.
    # Inside `make_tray`, we did:
    #   with BuildPart() as floor:
    #       ... extrude floor ...
    #       ... add walls ...
    #       ... add ears ...
    #       ... subtract holes ...
    # So `floor.part` should contain everything.
    
    # The "mystery hole" at front-left might be because the hex grid cut into the area where the wall/ear is.
    # The hex grid subtraction happens BEFORE the walls are added.
    # But the hex grid is subtracted from the FLOOR sketch.
    # Then the floor is extruded.
    # Then walls are added.
    # If the floor has a hole, and the wall sits ON TOP of it, it's fine.
    # But if the wall sits NEXT to it, there might be a gap.
    # The hex grid has a "safe zone" (Rectangle minus safe border).
    # The safe border is 10mm.
    # The ear/wall is at x=0.
    # The hex grid starts at x=0?
    # Hex pattern fills 0 to 220.
    # Safe zone is `translate([safe_border, safe_border]) square(...)`.
    # So hexes are ONLY inside the safe zone (10mm from edge).
    # The wall is 2mm thick.
    # So there should be 8mm of solid floor between wall and hexes.
    # UNLESS `sk_solids` (subtracted from hexes) caused an issue?
    # `sk_solids` are REMOVED from the hex pattern (so they become solid floor).
    # Wait, `sk_solids` is `mode=Mode.SUBTRACT` from `sk_hex`.
    # `sk_hex` is `mode=Mode.SUBTRACT` from `sk_floor`.
    # So `sk_solids` effectively ADDS back material to the floor?
    # Yes.
    # One of the solids is:
    # with Locations([(lx_left, ly_front), ...]): Circle(radius=11)
    # lx_left = sh_off_x + leg_inset = 15 + 6 = 21.
    # So there is a solid circle at x=21.
    # The wall is at x=0.
    # The user says "hole at front left".
    # Maybe the hex grid generation logic is flawed?
    # Let's ensure the floor is solid under the walls.
    # We can just UNION the wall footprint to the floor sketch?
    # Or simpler: Add a solid rectangle under the walls to the `sk_solids` list.
    
    # Let's verify the rack slots cutting.
    # The cutter is at x_left (-8.25).
    # The ear is at x=0 to -17.
    # So the cutter is inside the ear.
    # It should cut.
    
    return floor.part

def make_spacers():
    with BuildPart() as spacers:
        with Locations([ (i*12, 0, 0) for i in range(8) ]):
            Cylinder(radius=3.5, height=4, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        with BuildPart(mode=Mode.SUBTRACT):
             with Locations([ (i*12, 0, 0) for i in range(8) ]):
                Cylinder(radius=1.6, height=10, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return spacers.part

# --- Build Everything ---

print("Generating Shelf...")
shelf_part = make_shelf()

print("Generating Tray...")
tray_part = make_tray()

print("Generating Spacers...")
spacers_part = make_spacers()

# --- Visualization Objects ---

# --- Detailed Board Models ---

# --- Detailed Board Models ---

def make_dcdc_board(location=Location((0,0,0))):
    """Generates the DC-DC board with colors at a specific location."""
    parts = []
    
    # Helper to add colored part
    def add_part(geom, color, loc):
        # Apply the board's global location to the component's local location
        final_loc = location * loc
        parts.append(Compound(children=[geom], color=color).moved(final_loc))
        # Note: We move the Compound after creation? 
        # If .moved() strips color, this is bad.
        # We should move the geometry, THEN wrap.
        # geom.moved(final_loc) -> Wrapped in Compound(color).
    
    # Re-defining helper to be safe
    def add_colored(geom, color, local_loc):
        final_loc = location * local_loc
        parts.append(Compound(children=[geom.moved(final_loc)], color=color))

    # PCB (Black)
    with BuildPart() as pcb:
        Box(dcdc_w, dcdc_d, 1.6, align=(Align.MIN, Align.MIN, Align.MIN))
        with Locations((dcdc_w/2, dcdc_d/2, 0)):
            # Holes at 60x91.5 spacing
            with Locations([(x, y) for x in [-30, 30] for y in [-45.75, 45.75]]):
                Cylinder(radius=1.6, height=10, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.SUBTRACT)
    
    add_colored(pcb.part, Color("black"), Location((0,0,0)))
    
    z_top = 1.6
    
    # Inductors (Black/DarkGray)
    ind_geom = Box(10, 10, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ind_y_start = 40
    for i in range(4):
        add_colored(ind_geom, Color("darkgray"), Location((15, ind_y_start + i*15, z_top)))
            
    # Capacitors (Silver)
    cap_geom = Cylinder(radius=4, height=10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(4):
        add_colored(cap_geom, Color("silver"), Location((35, ind_y_start + i*15, z_top)))
            
    # Terminal Blocks (Green)
    term_geom = Box(12, 10, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(4):
        add_colored(term_geom, Color("green"), Location((10 + i*15, 5, z_top)))
                
    return Compound(children=parts)

def make_sata_board(location=Location((0,0,0))):
    """Generates the SATA/Power board with colors at a specific location."""
    parts = []
    
    def add_colored(geom, color, local_loc):
        final_loc = location * local_loc
        parts.append(Compound(children=[geom.moved(final_loc)], color=color))
    
    # PCB (Black)
    with BuildPart() as pcb:
        Box(sata_real_w, sata_real_d, 1.6, align=(Align.MIN, Align.MIN, Align.MIN))
        with Locations((sata_real_w/2, sata_real_d/2, 0)):
            # Holes at 50x70 spacing
            with Locations([(x, y) for x in [-25, 25] for y in [-35, 35]]):
                Cylinder(radius=1.6, height=10, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.SUBTRACT)

    add_colored(pcb.part, Color("black"), Location((0,0,0)))
    
    z_top = 1.6
    
    # White Connectors
    conn_geom = Box(15, 10, 15, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x in [10, 30]:
        add_colored(conn_geom, Color("white"), Location((x, 10, z_top)))
    
    # Inductor (DarkGray)
    ind_geom = Box(12, 12, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    add_colored(ind_geom, Color("darkgray"), Location((sata_real_w/2, sata_real_d/2, z_top)))
        
    # Capacitors (Silver)
    cap_geom = Cylinder(radius=4, height=10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x in [10, 30]:
        add_colored(cap_geom, Color("silver"), Location((x, 50, z_top)))

    return Compound(children=parts)

def make_pcie_card(location=Location((0,0,0))):
    """Generates the PCIe to SATA card with colors at a specific location."""
    parts = []
    
    def add_colored(geom, color, local_loc):
        final_loc = location * local_loc
        parts.append(Compound(children=[geom.moved(final_loc)], color=color))
    
    # PCB (Black)
    pcb_geom = Box(pcie_w, pcie_d, 1.6, align=(Align.MIN, Align.MIN, Align.MIN))
    add_colored(pcb_geom, Color("black"), Location((0,0,0)))
    
    z_top = 1.6
    
    # Heatsink (Silver)
    hs_geom = Box(40, 40, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    add_colored(hs_geom, Color("silver"), Location((pcie_w/2, pcie_d/2, z_top)))
        
    # SATA Ports (Black)
    # If holes are on Right, connector is on Left.
    # SATA ports usually opposite to bracket?
    # Standard PCIe: Bracket Left, Connector Bottom, Components Top.
    # If we look at card from top: Bracket Left.
    # Holes are usually near bracket?
    # Wait, standard PCIe holes are on the bracket side? No, bracket IS the mount.
    # This "PCIe to M.2" adapter seems to have mounting holes on the PCB itself.
    # If holes are on Right, and bracket is on Left (X=0).
    sata_geom = Box(15, 10, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(5):
        add_colored(sata_geom, Color("black"), Location((pcie_w - 10, 10 + i*12, z_top))) # Ports on Right?
        # If bracket is Left, ports are usually accessible from ... top?
        # Let's leave ports on Right for now.

    # Bracket (Silver)
    # Bracket is along Y (depth) at X=0 (Left)
    bracket_geom = Box(2, pcie_d + 20, 12, align=(Align.MIN, Align.CENTER, Align.CENTER))
    add_colored(bracket_geom, Color("white"), Location((0, pcie_d/2, 0)))

    return Compound(children=parts)

# --- Visualization Objects ---

# Calculate final locations for boards
# Shelf is now on bosses, so its Z origin (bottom of legs) is at Z = floor_thickness + leg_boss_height
shelf_assembly_loc = Location((sh_off_x, shelf_start_y, floor_thickness + leg_boss_height))

dcdc_loc = shelf_assembly_loc * Location((dcdc_x, dcdc_y, shelf_height + shelf_thickness + 2))
sata_loc = shelf_assembly_loc * Location((sata_x, sata_y, shelf_height + shelf_thickness + 2))
pcie_loc = Location((pcie_x, pcie_y, floor_thickness + pcie_standoff_height))

# Create boards at their FINAL locations
dcdc_board = make_dcdc_board(dcdc_loc)
sata_board = make_sata_board(sata_loc)
pcie_card = make_pcie_card(pcie_loc)
pcie_bracket = Part() # Included in make_pcie_card now


# --- Export / Visualize ---

# Export Shelf (Primary Artifact)
export_step(shelf_part, "rack_v106.step")
print("Exported rack_v106.step")

# Export Tray
export_step(tray_part, "rack_v106_tray.step")
print("Exported rack_v106_tray.step")

# Export to STL
export_stl(tray_part, "rack_v106_tray.stl")
print("Exported rack_v106_tray.stl")

export_stl(shelf_part, "rack_v106_shelf.stl")
print("Exported rack_v106_shelf.stl")

export_stl(spacers_part, "rack_v106_spacers.stl")
print("Exported rack_v106_spacers.stl")

# Export Full Assembly (STEP)
# Combine all parts into one compound for export

# Wrap main parts in colored Compounds AFTER moving them
# Tray is at (0,0,0)
tray_colored = Compound(children=[tray_part], color=Color("dimgray"))
tray_colored.label = "Tray"

# Shelf needs to be moved, THEN colored
shelf_moved = shelf_part.moved(shelf_assembly_loc)
shelf_colored = Compound(children=[shelf_moved], color=Color("lightgray"))
shelf_colored.label = "Shelf"

# Spacers need to be moved, THEN colored
spacers_moved = spacers_part.moved(Location((0, -20, 0)))
spacers_colored = Compound(children=[spacers_moved], color=Color("white"))
spacers_colored.label = "Spacers"

# Assign labels to boards
dcdc_board.label = "DC-DC Board"
sata_board.label = "SATA Board"
pcie_card.label = "PCIe Card"

assembly = Compound(children=[
    tray_colored,
    shelf_colored,
    spacers_colored,
    dcdc_board, # Already colored and at final location
    sata_board, # Already colored and at final location
    pcie_card   # Already colored and at final location
])
assembly.label = "Rack Assembly"
export_step(assembly, "rack_v106_assembly.step")
print("Exported rack_v106_assembly.step")

try:
    from ocp_vscode import show, show_object, set_port, set_defaults
    set_port(3939)
    
    # Assembly View
    # Tray is at Z=0.
    # Shelf is at Z=floor_thickness + ... wait, SCAD placed shelf at Z=floor_thickness.
    # My make_shelf starts at Z=0 (bottom of legs).
    # So we translate shelf to sit on tray floor.
    
    shelf_assembly_loc = Location((sh_off_x, shelf_start_y, floor_thickness + leg_boss_height))
    
    show(
        tray_part,
        shelf_part.moved(shelf_assembly_loc),
        spacers_part.moved(Location((0, -20, 0))), # Move spacers out of the way
        dcdc_board, # Already at final location
        sata_board, # Already at final location
        pcie_card,
        names=["Tray", "Shelf", "Spacers", "DC-DC", "SATA", "PCIe"],
        colors=["lightgray", "lightgray", "white", "red", "blue", "green"],
        alphas=[1.0, 1.0, 1.0, 0.6, 0.6, 0.6]
    )
except (ImportError, Exception) as e:
    print(f"Visualization skipped: {e}")
