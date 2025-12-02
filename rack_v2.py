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
rack_inner_width = 220 # Updated to match SCAD reference (was 195)
tray_height = 1.75 * 25.4 # 1U = 44.45 mm
tray_depth = 200  # Reduced from 220 to minimize excess space beyond DC-DC board

floor_thickness = 2
wall_thickness = 1.6
ear_thickness = 3.0 # Updated to 3.0mm to match make_ear and avoid step
EPS = 0.01

# Positioning Legs (Removed Shelf)
# leg_inset = 6 ...

# Component Dimensions
pcie_w, pcie_d = 154.3, 67.3
pcie_hole_dist = 47.1
pcie_offset_y = 3.4
pcie_x, pcie_y = 20.35, 46 # Front (44mm clearance)
pcie_standoff_height = 10  # Increased from 6mm for better riser card clearance


# Power Boards
# Rotated 90 degrees: Width becomes 100.3, Depth becomes 68.5
dcdc_w, dcdc_d = 100.3, 68.5 # DC-DC is stacked on Bridge (Rotated: 100.3 x 68.5)
dcdc_offset = 2.5
dcdc_x, dcdc_y = 10, 115  # Moved 5mm forward for connector clearance # Moved to Left Wall (10mm gap)

sata_real_w, sata_real_d = 60, 80
sata_offset = 4.2
# SATA is stacked on DC-DC (Rotated)
# Center SATA on DC-DC:
sata_x, sata_y = dcdc_x + (dcdc_w - sata_real_w)/2, dcdc_y + (dcdc_d - sata_real_d)/2

# Bridge Dimensions
bridge_height = 15  # Reduced to 15mm per user request
bridge_leg_dia = 6  # Reduced from 8 to avoid crowding DC-DC

# Shelf Leg Bosses (Countersunk Screws)
leg_boss_height = 2.5
screw_head_dia = 6.0 # Clearance for 5.5mm head
screw_head_height = 3.5 # Clearance for 3.0mm head




# --- Generators ---

def make_bridge():
    """Generates the minimalist bridge for the SATA board."""
    # Bridge sits on DC-DC mounting holes (Rotated: 91.5 x 60)
    # Holds SATA board (50x70)
    
    dcdc_hole_w = 91.5
    dcdc_hole_d = 60
    
    sata_hole_w = 50
    sata_hole_d = 70
    
    # Bridge Plate Size
    plate_w = max(dcdc_hole_w, sata_hole_w) + 10
    plate_d = max(dcdc_hole_d, sata_hole_d) + 10
    
    with BuildPart() as bridge:
        # Build bottom-up: Start with frame at Z=0, legs extend downward
        
        # 1. Top Frame/Plate (at Z=0, this will be the reference point)
        # Create solid plate with 4mm border and cutout center with support bars
        # 1. Top Frame/Plate (at Z=0, this will be the reference point)
        with BuildSketch(Plane.XY):
            # 1. Base Plate
            Rectangle(plate_w, plate_d)
            
            # 2. Hexagon Pattern (to be subtracted)
            with BuildSketch(mode=Mode.PRIVATE) as sk_hex:
                with HexLocations(radius=8, x_count=8, y_count=6):
                    RegularPolygon(radius=7.5, side_count=6)
            
            # 3. Safe Zone (Inner Rectangle where hexes are allowed)
            with BuildSketch(mode=Mode.PRIVATE) as sk_safe:
                Rectangle(plate_w - 8, plate_d - 8)
                
            # 4. Support Areas (Bars + Circles that must remain solid)
            with BuildSketch(mode=Mode.PRIVATE) as sk_supports:
                # SATA bars
                with Locations([(x, 0) for x in [-25, 25]]):
                    Rectangle(10, plate_d)
                # Center bar
                Rectangle(plate_w, 10)
                # Leg circles
                with Locations([(x, y) for x in [-dcdc_hole_w/2, dcdc_hole_w/2] for y in [-dcdc_hole_d/2, dcdc_hole_d/2]]):
                    Circle(radius=7)

            # 5. Combine to create the cutouts
            # Cutouts = (Hexagons INTERSECT SafeZone) MINUS SupportAreas
            # We want to SUBTRACT these Cutouts from the Base Plate.
            cutouts = (sk_hex.sketch & sk_safe.sketch) - sk_supports.sketch
            add(cutouts, mode=Mode.SUBTRACT)
            
        extrude(amount=2)  # Frame is 2mm thick
        
        # 2. Legs extending DOWN from the frame
        # Legs are at the DC-DC hole locations, extending down by bridge_height
        with Locations([(x, y, 0) for x in [-dcdc_hole_w/2, dcdc_hole_w/2] for y in [-dcdc_hole_d/2, dcdc_hole_d/2]]):
            Cylinder(radius=bridge_leg_dia/2, height=bridge_height, align=(Align.CENTER, Align.CENTER, Align.MAX))

        # 3. Holes
        with BuildPart(mode=Mode.SUBTRACT):
            # Leg Holes (through-holes for screws - only through LEGS, not frame top)
            # Reduced to 2.5mm for tighter self-tapping fit (was 2.8mm)
            with Locations([(x, y, -1) for x in [-dcdc_hole_w/2, dcdc_hole_w/2] for y in [-dcdc_hole_d/2, dcdc_hole_d/2]]):
                Cylinder(radius=2.5/2, height=bridge_height + 1, align=(Align.CENTER, Align.CENTER, Align.MAX))
            
            # SATA Mounting Holes (top of frame)
            # Reduced to 2.5mm
            with Locations([(x, y, 2) for x in [-sata_hole_w/2, sata_hole_w/2] for y in [-sata_hole_d/2, sata_hole_d/2]]):
                Cylinder(radius=2.5/2, height=5, align=(Align.CENTER, Align.CENTER, Align.MAX))

    return bridge.part

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
                            # radius=16 gives 0mm wall thickness - hexagons touch for maximum material savings
                            RegularPolygon(radius=16, side_count=6)
                
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
                    # Leg Bases (Removed)


        extrude(amount=floor_thickness)
        
        # Floor beneath ears (REMOVED to prevent protrusion artifact)
        # The ear itself acts as the structure.

        # 2. Frame Structure (Walls & Ears)
        # Create unified front profile (faceplate + ears) to avoid overlap artifacts
        
        # Unified Front Face (Faceplate + Both Ears)
        with BuildSketch(Plane.XZ.offset(0)) as sk_front:
            # Ear dimensions
            ear_w = 17
            slot_center_x_left = -8.25  # Relative to X=0
            slot_center_x_right = rack_inner_width + 8.25  # Relative to X=rack_inner_width
            slot_width = 9
            slot_height = 6
            hole_z_offset = 15.88
            slot_z_center = tray_height / 2
            
            # Main faceplate rectangle (inner width only)
            with Locations((rack_inner_width/2, tray_height/2)):
                Rectangle(rack_inner_width, tray_height)
            
            # Left ear
            with Locations((-ear_w/2, tray_height/2)):
                Rectangle(ear_w, tray_height)
            
            # Right ear
            with Locations((rack_inner_width + ear_w/2, tray_height/2)):
                Rectangle(ear_w, tray_height)
            
            # Fillet outer corners of ears
            # Left ear outer corners (at X = -17)
            left_outer_verts = sk_front.vertices().filter_by(lambda v: abs(v.X + ear_w) < 0.1)
            fillet(left_outer_verts, radius=5.0)
            
            # Right ear outer corners (at X = 237)
            right_outer_verts = sk_front.vertices().filter_by(lambda v: abs(v.X - (rack_inner_width + ear_w)) < 0.1)
            fillet(right_outer_verts, radius=5.0)
            
            # Cut slots in left ear
            with Locations([(slot_center_x_left, slot_z_center + hole_z_offset), 
                          (slot_center_x_left, slot_z_center - hole_z_offset)]):
                SlotOverall(width=slot_width, height=slot_height, rotation=0, mode=Mode.SUBTRACT)
            
            # Cut slots in right ear
            with Locations([(slot_center_x_right, slot_z_center + hole_z_offset), 
                          (slot_center_x_right, slot_z_center - hole_z_offset)]):
                SlotOverall(width=slot_width, height=slot_height, rotation=0, mode=Mode.SUBTRACT)
        
        # Extrude the unified front face
        extrude(sk_front.sketch, amount=ear_thickness)
        
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
                # Triangle: (0,0) -> (0, tray_height - 10), (20, 0)
                with BuildSketch(Plane.YZ) as sk:
                    Polygon([(0,0), (0, tray_height - 10), (20, 0)])
                
                if is_right:
                    # Right side: Starts at X = rack_inner_width
                    # Extrude in +X direction (wall thickness)
                    extrude(sk.sketch, amount=wall_thickness)
                else:
                    # Left side: Starts at X = 0
                    # Extrude in -X direction (wall thickness)
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
        
        # DC-DC Support Strips (2 strips along X direction for the 4 bosses)
        # Creates solid floor support under DC-DC bosses to prevent floating in hexagons
        dcdc_strip_width = 100.3  # Full width of DC-DC board
        dcdc_strip_thickness = 10  # 10mm wide strips
        
        # Calculate hole positions to center strips on them
        dcdc_hole_w = 91.5
        dcdc_hole_d = 60
        dcdc_hole_x = dcdc_x + (dcdc_w - dcdc_hole_w) / 2
        dcdc_hole_y = dcdc_y + (dcdc_d - dcdc_hole_d) / 2
        
        # Front strip (centered on front holes)
        with Locations((dcdc_x, dcdc_hole_y - dcdc_strip_thickness/2, 0)):
            Box(dcdc_strip_width, dcdc_strip_thickness, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
        
        # Rear strip (centered on rear holes)
        with Locations((dcdc_x, dcdc_hole_y + dcdc_hole_d - dcdc_strip_thickness/2, 0)):
            Box(dcdc_strip_width, dcdc_strip_thickness, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
        
        # USB-C Socket Mount Bracket (Right rear corner) - REINFORCED
        usbc_bracket_width = 30  # Increased from 20 to 30mm for thicker walls
        usbc_bracket_thickness = 15  # 15mm deep into tray
        usbc_bracket_height = 25  # Height for vertical mount
        usbc_hole_dia = 17  # Reduced from 19 to 17mm for thicker walls (14.5mm socket + 2.5mm clearance)
        usbc_hole_height = 18  # Center height
        
        # Bracket position: right edge of tray
        usbc_x = rack_inner_width - usbc_bracket_width - 2
        usbc_y = tray_depth - usbc_bracket_thickness
        
        # Main bracket body
        with Locations((usbc_x, usbc_y, 0)):
            Box(usbc_bracket_width, usbc_bracket_thickness, usbc_bracket_height, 
                align=(Align.MIN, Align.MIN, Align.MIN))
        
        # Top cap (thicker for strength)
        cap_thickness = 5  # Increased from 3 to 5mm for better strength
        with Locations((usbc_x, usbc_y, usbc_bracket_height)):
            Box(usbc_bracket_width, usbc_bracket_thickness, cap_thickness, 
                align=(Align.MIN, Align.MIN, Align.MIN))
        
        # USB-C hole (centered in bracket width)
        with BuildPart(mode=Mode.SUBTRACT):
            hole_y_center = usbc_y + usbc_bracket_thickness/2
            hole_x_center = usbc_x + usbc_bracket_width/2
            with Locations((hole_x_center, hole_y_center, usbc_hole_height)):
                with Locations(Rotation(90, 0, 0)):
                    Cylinder(radius=usbc_hole_dia/2, height=usbc_bracket_thickness + 5, 
                           align=(Align.CENTER, Align.CENTER, Align.CENTER))
        
        # Leg Bases (Removed)

        # Helper: Add Bosses
        def add_bosses(x, y, w, d, offset):
            locs = [
                (x + offset, y + offset),
                (x + w - offset, y + offset),
                (x + offset, y + d - offset),
                (x + w - offset, y + d - offset)
            ]
            with BuildSketch(Plane.XY.offset(floor_thickness)) as sk:
                with Locations(locs):
                    Circle(radius=4)
            extrude(sk.sketch, amount=2.5) # 2.5mm boss height

        # DC-DC Bosses (Rotated: 91.5 x 60)
        dcdc_hole_w = 91.5
        dcdc_hole_d = 60
        dcdc_hole_x = dcdc_x + (dcdc_w - dcdc_hole_w) / 2
        dcdc_hole_y = dcdc_y + (dcdc_d - dcdc_hole_d) / 2
        add_bosses(dcdc_hole_x, dcdc_hole_y, dcdc_hole_w, dcdc_hole_d, 0)
        
        # SATA Bosses (Removed - SATA is on Bridge)
        # sata_hole_w = 50
        # sata_hole_d = 70
        # sata_hole_x = sata_x + (sata_real_w - sata_hole_w) / 2
        # sata_hole_y = sata_y + (sata_real_d - sata_hole_d) / 2
        # add_bosses(sata_hole_x, sata_hole_y, sata_hole_w, sata_hole_d, 0)

        # PCIe Standoffs (NOW IN CORRECT SCOPE!)
        standoff_x = pcie_x + pcie_w - 7.4
        standoff_y1 = pcie_y + pcie_offset_y
        standoff_y2 = standoff_y1 + pcie_hole_dist
        print(f"PCIe Standoffs: X={standoff_x:.2f}, Y1={standoff_y1:.2f}, Y2={standoff_y2:.2f}")
        
        with Locations((standoff_x, standoff_y1, floor_thickness - EPS)):
            Cylinder(radius=4, height=pcie_standoff_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, pcie_hole_dist, 0)):
                Cylinder(radius=4, height=pcie_standoff_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4. Subtractions (Holes)
        with BuildPart(mode=Mode.SUBTRACT):
            # Helper: Add Mount Holes
            def add_mount_holes(x, y, w, d, offset):
                locs = [
                    (x + offset, y + offset),
                    (x + w - offset, y + offset),
                    (x + offset, y + d - offset),
                    (x + w - offset, y + d - offset)
                ]
                with Locations(locs):
                    Cylinder(radius=1.4, height=50, align=(Align.CENTER, Align.CENTER, Align.CENTER))

            # DC Jack
            with Locations((15, tray_depth + 5, 8)):
                with Locations(Rotation(90, 0, 0)):
                    Cylinder(radius=dc_jack_dia/2, height=10)

            # PCIe Holes (Right side)
            with Locations((pcie_x + pcie_w - 7.4, pcie_y + pcie_offset_y, -10)):
                Cylinder(radius=1.4, height=50)
                with Locations((0, pcie_hole_dist, 0)):
                    Cylinder(radius=1.4, height=50)

            # DC-DC Holes (3mm with countersink for M3 screws, like v106)\n            dcdc_hole_w = 91.5
            dcdc_hole_d = 60
            dcdc_hole_x = dcdc_x + (dcdc_w - dcdc_hole_w) / 2
            dcdc_hole_y = dcdc_y + (dcdc_d - dcdc_hole_d) / 2
            
            # 4 corners: countersink from BOTTOM like v106
            with Locations([(dcdc_hole_x, dcdc_hole_y), 
                           (dcdc_hole_x + dcdc_hole_w, dcdc_hole_y),
                           (dcdc_hole_x, dcdc_hole_y + dcdc_hole_d),
                           (dcdc_hole_x + dcdc_hole_w, dcdc_hole_y + dcdc_hole_d)]):
                # Through hole (3mm for M3)
                with Locations((0, 0, -10)):
                    Cylinder(radius=3.0/2, height=50, align=(Align.CENTER, Align.CENTER, Align.CENTER))
                # Countersink from bottom (starts at Z=0, goes up)
                Cylinder(radius=screw_head_dia/2, height=screw_head_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            # SATA Holes (Removed - SATA is on Bridge)
            # add_mount_holes(sata_hole_x, sata_hole_y, sata_hole_w, sata_hole_d, 0)


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

print("Generating Bridge...")
bridge_part = make_bridge()


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
    # Rotated: Spread along X (0 to 100), Y fixed/small range
    ind_geom = Box(10, 10, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Place in a grid 2x2 or line?
    # Board is 100x68.
    # Terminals at Y=5.
    # Components at Y=30, Y=50.
    for i in range(4):
        add_colored(ind_geom, Color("darkgray"), Location((20 + i*20, 30, z_top)))
            
    # Capacitors (Silver)
    cap_geom = Cylinder(radius=4, height=10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(4):
        add_colored(cap_geom, Color("silver"), Location((20 + i*20, 50, z_top)))
            
    # Terminal Blocks (Green)
    term_geom = Box(12, 10, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(4):
        add_colored(term_geom, Color("green"), Location((20 + i*20, 10, z_top)))
                
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
# Z-Stacking Logic (CORRECTED):
# 1. Tray Floor: Z = 0 to 2.5 (floor_thickness)
# 2. Bosses: Z = 2.5 to 5.0 (boss_height = 2.5)
# 3. DC-DC Board: Z = 5.0 to 6.6 (thickness = 1.6)
# 4. Bridge:
#    - Legs extend DOWN from frame
#    - Frame (local Z=0) needs to be at global Z where SATA sits
#    - Frame bottom at: 5.0 + 1.6 + 20 = 26.6
#    - Frame is 2mm thick, top at 28.6
# 5. SATA Board: Z = 28.6 (sits ON TOP of 2mm frame)

dcdc_z = floor_thickness + 2.5  # DC-DC sits on bosses: Z=5.0
bridge_frame_z = dcdc_z + 1.6 + bridge_height  # Bridge frame bottom: Z=26.6
sata_z = bridge_frame_z + 2  # SATA sits on top of 2mm frame: Z=28.6

# Bridge frame (local Z=0) is placed at frame bottom
# Legs extend DOWN from there
bridge_loc = Location((dcdc_x + dcdc_w/2, dcdc_y + dcdc_d/2, bridge_frame_z))

dcdc_loc = Location((dcdc_x, dcdc_y, dcdc_z))
sata_loc = Location((sata_x, sata_y, sata_z))
pcie_loc = Location((pcie_x, pcie_y, floor_thickness + pcie_standoff_height))


# Create boards at their FINAL locations
dcdc_board = make_dcdc_board(dcdc_loc)
sata_board = make_sata_board(sata_loc)
pcie_card = make_pcie_card(pcie_loc)
pcie_bracket = Part() # Included in make_pcie_card now


# --- Export / Visualize ---

# Export Bridge (Primary Artifact)
export_step(bridge_part, "rack_v2_bridge.step")
print("Exported rack_v2_bridge.step")

# Export Tray
export_step(tray_part, "rack_v2_tray.step")
print("Exported rack_v2_tray.step")

# Export to STL
export_stl(tray_part, "rack_v2_tray.stl")
print("Exported rack_v2_tray.stl")

export_stl(bridge_part, "rack_v2_bridge.stl")
print("Exported rack_v2_bridge.stl")


export_stl(spacers_part, "rack_v106_spacers.stl")
print("Exported rack_v106_spacers.stl")

# Export Full Assembly (STEP)
# Combine all parts into one compound for export

# Wrap main parts in colored Compounds AFTER moving them
# Tray is at (0,0,0)
tray_colored = Compound(children=[tray_part], color=Color("dimgray"))
tray_colored.label = "Tray"

# Bridge
bridge_colored = Compound(children=[bridge_part.moved(bridge_loc)], color=Color("lightgray"))
bridge_colored.label = "Bridge"


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
    bridge_colored,
    spacers_colored,
    dcdc_board, # Already colored and at final location
    sata_board, # Already colored and at final location
    pcie_card   # Already colored and at final location
])
assembly.label = "Rack Assembly V2"
export_step(assembly, "rack_v2_assembly.step")
print("Exported rack_v2_assembly.step")

try:
    from ocp_vscode import show, show_object, set_port, set_defaults
    set_port(3939)
    
    # Assembly View
    show(
        tray_part,
        bridge_part.moved(bridge_loc),
        spacers_part.moved(Location((0, -20, 0))), # Move spacers out of the way
        dcdc_board, # Already at final location
        sata_board, # Already at final location
        pcie_card,
        names=["Tray", "Bridge", "Spacers", "DC-DC", "SATA", "PCIe"],
        colors=["lightgray", "lightgray", "white", "red", "blue", "green"],
        alphas=[1.0, 1.0, 1.0, 0.6, 0.6, 0.6]
    )
except (ImportError, Exception) as e:
    print(f"Visualization skipped: {e}")
