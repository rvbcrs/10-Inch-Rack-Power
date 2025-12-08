import logging
from build123d import *
from ocp_vscode import *

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Dimensions & Constants ---

# Wall & Floor
wall_thickness = 1.6 # Reduced from 2.0 for faster print (4 perimeters)
floor_thickness = 1.6 # Reduced from 2.0
box_height = 35 # Reduced from 40 (USB-C is 30mm high)

# Component Dimensions (Hole Spacings)
# DC-DC Board
dcdc_hole_w = 91.5
dcdc_hole_d = 60
dcdc_board_w = 100.3 # Physical width
dcdc_board_d = 68.0  # Physical depth (approx)

# SATA Power Board
sata_hole_w = 50
sata_hole_d = 70
sata_board_w = 58 # Physical width (approx)
sata_board_d = 78 # Physical depth (approx)

# M.2 Adapter PCB (24x96mm)
m2_pcb_w = 24
m2_pcb_d = 96
m2_hole_dx = 20 # Width between holes (approx, 24 - 2*2)
m2_hole_dy = 92 # Depth between holes (approx, 96 - 2*2)

# USB-C Socket Mount (Reinforced V2 Design)
usbc_bracket_width = 35
usbc_bracket_thickness = 10
usbc_bracket_height = 30 # Increased to match hole
usbc_hole_dia = 17
usbc_hole_height = 22 # Raised from 18

# Standoffs
standoff_height = 5
standoff_radius = 3.5
screw_hole_radius = 1.4 # M3 pilot

# --- Layout Calculation ---
# Layout:
# DC-DC: Back Left (Connectors facing BACK)
# SATA Power: Right Side (Connectors facing RIGHT)
# M.2 Adapter: Front Left
# USB-C: Back Right

padding = 5
gap = 2 # Tight gap between boards

# Box Internal Dimensions
box_inner_w = 170 # Fixed width
box_inner_d = 140 # Increased to 140mm to resolve Cutout/USB-C overlap

print(f"Box Internal Dimensions: {box_inner_w:.1f} x {box_inner_d:.1f} mm")

# Component Positions (Relative to Box Origin 0,0)

# USB-C: Back Right (Fixed Anchor)
usbc_x = box_inner_w - usbc_bracket_width
usbc_y = box_inner_d - usbc_bracket_thickness

# DC-DC (100x68): Back Left (Fixed Anchor)
# Rotated 180 degrees
dcdc_rot = 180
dcdc_x = padding
dcdc_y = box_inner_d - dcdc_board_d - padding 

# SATA Power (58x78): Right Side
# Standard: 58 wide, 78 deep. Connectors on "Right".
sata_rot = 0
sata_x = box_inner_w - sata_board_w - padding 
# Maintain 35mm clearance at front for DC Jack
sata_y = 35 

# M.2 Adapter: Front Left, Tight against DC-DC
# DC-DC Front is dcdc_y. M.2 Back should be at dcdc_y - gap.
m2_x = padding
m2_y = dcdc_y - gap - 24  # 96x24. 24 is depth.

# --- Detailed Component Generators ---

def make_detailed_dcdc():
    """Generates DC-DC parts: (PCB, Terminals)."""
    # PCB
    pcb = Box(dcdc_board_w, dcdc_board_d, 2, align=(Align.MIN, Align.MIN, Align.MIN))
    
    # Components on PCB
    with BuildPart() as comps:
        with Locations((0, 0, 2)):
             Box(dcdc_board_w-20, dcdc_board_d-20, 5, align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((10,10)))
    pcb = pcb + comps.part
             
    # Terminals (Green)
    with BuildPart() as terms:
        with Locations((0, 0, 2)):
            term_w = 15
            term_d = 10 
            term_h = 10
            with Locations([(10 + i*22, 0, 0) for i in range(4)]):
                Box(term_w, term_d, term_h, align=(Align.MIN, Align.MIN, Align.MIN))
                
    return pcb, terms.part

def make_detailed_sata():
    """Generates SATA parts: (PCB, Connectors)."""
    # Base: 58 wide, 78 deep. Connectors on Right Edge (X=58).
    
    # PCB
    pcb = Box(sata_board_w, sata_board_d, 2, align=(Align.MIN, Align.MIN, Align.MIN))
    
    # Components on PCB
    with BuildPart() as comps:
        with Locations((0, 0, 2)):
             Box(sata_board_w-20, sata_board_d-10, 5, align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((5,5)))
    pcb = pcb + comps.part

    # Connectors (White) - On Right Edge (X=58)
    with BuildPart() as conns:
        with Locations((0, 0, 2)):
            # Large Molex
            conn_w = 10
            conn_l = 25
            conn_h = 12
            with Locations([(sata_board_w - conn_w, y, 0) for y in [25, 55]]): # Adjusted positions
                Box(conn_w, conn_l, conn_h, align=(Align.MIN, Align.MIN, Align.MIN))
    
            # DC Jack (Black) - Bottom Edge (Y=0)
            # Position: Center X approx 20-30?
            # From image: Bottom left-ish. Let's say X=20, Y=0.
            # Size: 10x15 (deep) x 10
            # Extends slightly off board? Or flush? Lets make it flush with edge.
            with Locations((15, 0, 0)):
                 Box(12, 14, 10, align=(Align.MIN, Align.MIN, Align.MIN))
                 
    return pcb, conns.part

# Generate Ghosts
dcdc_pcb_raw, dcdc_terms_raw = make_detailed_dcdc()
sata_pcb_raw, sata_conns_raw = make_detailed_sata()

# --- Builders ---

def make_box():
    """Generates the compact box with hex floor, mounts, and wall cutouts."""
    
    with BuildPart() as box:
        # 1. Floor with Hex Pattern
        with BuildSketch(Plane.XY):
            Rectangle(box_inner_w, box_inner_d, align=(Align.MIN, Align.MIN))
            
            # Hex Pattern
            with BuildSketch(mode=Mode.PRIVATE) as sk_hex:
                with Locations((box_inner_w/2, box_inner_d/2)):
                    # Increased radius for larger holes (less plastic)
                    # Adjusted counts for larger hexes
                    with HexLocations(radius=12, x_count=14, y_count=10):
                        RegularPolygon(radius=11, side_count=6)
            
            # Safe Zones
            # User wants 5mm visible border inside the walls.
            # Walls are 1.6mm thick. So we need 5 + 1.6 = 6.6mm border from the outer edge.
            # Use Center alignment to ensure symmetry and avoid shift errors.
            margin = 6.6
            with BuildSketch(mode=Mode.PRIVATE) as sk_allowed:
                with Locations((box_inner_w/2, box_inner_d/2)):
                    Rectangle(box_inner_w - 2*margin, box_inner_d - 2*margin, align=(Align.CENTER, Align.CENTER))
                
                with BuildSketch(mode=Mode.SUBTRACT):
                    # DC-DC Mounts
                    with Locations((dcdc_x + dcdc_board_w/2, dcdc_y + dcdc_board_d/2)):
                         with Locations([(x, y) for x in [-dcdc_hole_w/2, dcdc_hole_w/2] for y in [-dcdc_hole_d/2, dcdc_hole_d/2]]):
                            Circle(radius=standoff_radius + 4)

                    # SATA Mounts
                    with Locations((sata_x + sata_board_w/2, sata_y + sata_board_d/2)): 
                         with Locations([(x, y) for x in [-sata_hole_w/2, sata_hole_w/2] for y in [-sata_hole_d/2, sata_hole_d/2]]):
                            Circle(radius=standoff_radius + 4)
                            
                    # M.2 & USB-C 
                    with Locations((m2_x + 2, m2_y + 2)): Circle(radius=standoff_radius + 4)
                    with Locations((m2_x + 96 - 2, m2_y + 2)): Circle(radius=standoff_radius + 4)
                    with Locations((m2_x + 2, m2_y + 24 - 2)): Circle(radius=standoff_radius + 4)
                    with Locations((m2_x + 96 - 2, m2_y + 24 - 2)): Circle(radius=standoff_radius + 4)
                    with Locations((usbc_x - 2, usbc_y - 2)): Rectangle(usbc_bracket_width + 4, usbc_bracket_thickness + 4, align=(Align.MIN, Align.MIN))

            cutouts = sk_hex.sketch & sk_allowed.sketch
            add(cutouts, mode=Mode.SUBTRACT)
        
        extrude(amount=floor_thickness)
        
        # 2. Walls with Cutouts
        
        # Define Walls (Solids)
        # Use mode=Mode.PRIVATE to prevent the base Box from being added to the part at (0,0)
        
        # Back Wall (Top)
        top_wall = Location((0, box_inner_d, 0)) * Box(box_inner_w, wall_thickness, box_height, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.PRIVATE)
        # Front Wall (Bottom)
        bottom_wall = Location((0, -wall_thickness, 0)) * Box(box_inner_w, wall_thickness, box_height, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.PRIVATE)
        # Left Wall
        left_wall = Location((-wall_thickness, -wall_thickness, 0)) * Box(wall_thickness, box_inner_d + 2*wall_thickness, box_height, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.PRIVATE)
        # Right Wall
        right_wall = Location((box_inner_w, -wall_thickness, 0)) * Box(wall_thickness, box_inner_d + 2*wall_thickness, box_height, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.PRIVATE)
        
        walls = top_wall + bottom_wall + left_wall + right_wall
        
        # Define Cutouts (Solids)
        
        # DC-DC Cutout (Back Wall)
        dcdc_cutout = Location((dcdc_x + 50, box_inner_d + wall_thickness/2, 15)) * Box(90, wall_thickness + 10, 20, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.PRIVATE)
        
        # SATA Cutout (Right Wall)
        # Connectors span Y=25 to Y=80 relative to board origin.
        # Cutout should cover this range with some margin.
        # Center at 55 (avrg of 25 and 85ish). Height 70 extends 35 either side -> 20 to 90.
        sata_cutout = Location((box_inner_w + wall_thickness/2, sata_y + 55, 15)) * Box(wall_thickness + 10, 70, 20, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.PRIVATE)
        
        # M.2 Cutout (Left Wall)
        # Dynamic Y position based on m2_y
        # Widen by 2mm as requested (24 -> 26)
        m2_cutout = Location((-wall_thickness/2, m2_y + 12, 15)) * Box(wall_thickness + 10, 26, 20, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.PRIVATE)
        
        # Text "Powerbox" on FRONT Wall (Outside)
        # Front Wall is at Y = 0 (inner face). Outer face is Y = -wall_thickness.
        # Logo on FRONT Wall (Outside)
        # "Flash" Icon + "POWERBOX" Text
        with BuildSketch(Plane.XZ.offset(wall_thickness), mode=Mode.PRIVATE) as sk_logo:
             with Locations((box_inner_w/2, 20)): # Center of Front Wall
                
                # 1. Lightning Bolt Icon (Vector Shape)
                # Position: Left of text. Total width approx 160mm.
                # Let's center the whole group.
                # Bolt is approx 15mm wide x 25mm high.
                # Text is approx 120mm wide.
                # Total width ~ 145mm.
                # Start Bolt at X = -70 relative to center.
                
                with Locations((-75, 0)):
                    # Draw a cool lightning bolt
                    # Points relative to its specific center
                    Polygon([
                        (5, 12),   # Top Right tip
                        (-5, 4),   # Top Left inner
                        (-8, 12),  # Top Left tip
                        (-2, -2),  # Middle Left
                        (-6, -2),  # Bottom Left Ext
                        (4, -12),  # Bottom Tip
                        (0, 0),    # Middle Right
                        (6, 0)     # Top Right Ext
                    ], align=(Align.CENTER, Align.CENTER))
                
                # 2. Text "POWERBOX"
                # Use a strong font. "Impact" or "Futura" or "Arial Black".
                # Trying "Futura" (Mac standard).
                with Locations((10, 0)): # Shift right to make room for bolt
                    Text("POWERBOX", font_size=24, font="Futura", font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
        
        # Create solid for Logo (Private)
        # Extrude into the wall (-Y direction)
        text_solid = extrude(sk_logo.sketch, amount=-0.6, mode=Mode.PRIVATE)
        
        # Apply subtractions (Carve the socket)
        walls = walls - dcdc_cutout - sata_cutout - m2_cutout - text_solid
        
        add(walls)
            
        # 3. Standoffs (Updated)
        def add_standoffs(center_x, center_y, w_hole, d_hole):
             with Locations((center_x, center_y, floor_thickness)):
                with Locations([(x, y) for x in [-w_hole/2, w_hole/2] for y in [-d_hole/2, d_hole/2]]):
                    Cylinder(radius=standoff_radius, height=standoff_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

        add_standoffs(dcdc_x + dcdc_board_w/2, dcdc_y + dcdc_board_d/2, dcdc_hole_w, dcdc_hole_d)
        add_standoffs(sata_x + sata_board_w/2, sata_y + sata_board_d/2, sata_hole_w, sata_hole_d)
        
        # M.2 Standoffs (48, 12 offset relative to m2_x, m2_y)
        m2_hole_w = 96 - 4
        m2_hole_d = 24 - 4
        add_standoffs(m2_x + 48, m2_y + 12, m2_hole_w, m2_hole_d)

        # 4. USB-C Bracket
        with Locations((usbc_x, usbc_y, floor_thickness)):
            Box(usbc_bracket_width, usbc_bracket_thickness, usbc_bracket_height, align=(Align.MIN, Align.MIN, Align.MIN))
            with Locations((0, 0, usbc_bracket_height)):
                Box(usbc_bracket_width, usbc_bracket_thickness, 5, align=(Align.MIN, Align.MIN, Align.MIN))
                
        # 5. Holes (Subtractions)
        with BuildPart(mode=Mode.SUBTRACT):
            # Standoff Holes (M3 Pilot)
            def add_holes(center_x, center_y, w_hole, d_hole):
                with Locations((center_x, center_y, 0)):
                    with Locations([(x, y) for x in [-w_hole/2, w_hole/2] for y in [-d_hole/2, d_hole/2]]):
                        Cylinder(radius=screw_hole_radius, height=standoff_height + floor_thickness + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            add_holes(dcdc_x + dcdc_board_w/2, dcdc_y + dcdc_board_d/2, dcdc_hole_w, dcdc_hole_d)
            add_holes(sata_x + sata_board_w/2, sata_y + sata_board_d/2, sata_hole_w, sata_hole_d)
            add_holes(m2_x + 48, m2_y + 12, m2_hole_w, m2_hole_d)
             
            # USB-C Hole
            hole_y_center = usbc_y + usbc_bracket_thickness/2
            with Locations((usbc_x + usbc_bracket_width/2, hole_y_center, floor_thickness + usbc_hole_height)):
                with Locations(Rotation(90, 0, 0)):
                    Cylinder(radius=usbc_hole_dia/2, height=usbc_bracket_thickness + 10, align=(Align.CENTER, Align.CENTER, Align.CENTER))

    return box.part, text_solid

# --- Apply Rotations to Ghosts ---

# DC-DC: Rotate 180 around its center (50, 34)
# Then move to position (dcdc_x, dcdc_y, z)
# Translation first, then Rotate? No, Local Rotation.
# If we rotate the Part geometry 180, the headers at Y=0 move to Top (relative to part).
# Then we place the part.
# Center adjustment: simple rotate around (0,0) is fine if we generated centered? 
# Currently generated at 0,0 min corner. Rotating 180 moves it to negative coords.
# Correction: rotate around Z axis (origin).
# Raw: 0..W, 0..D. Rotated 180: -W..0, -D..0.
# We want to place it at dcdc_x..dcdc_x+W, dcdc_y..dcdc_y+D.
# So we need to translate by (dcdc_x + W, dcdc_y + D).
dcdc_pcb = dcdc_pcb_raw.rotate(Axis.Z, 180)
dcdc_terms = dcdc_terms_raw.rotate(Axis.Z, 180)

# Final Location includes the shift for the rotation
dcdc_shift = (dcdc_x + dcdc_board_w, dcdc_y + dcdc_board_d, standoff_height + floor_thickness)
dcdc_pcb_loc = Location(dcdc_shift) * dcdc_pcb
dcdc_terms_loc = Location(dcdc_shift) * dcdc_terms

# SATA: Rotate 0 (No change needed, connectors on Right Edge aligned with Right Wall)
sata_pcb_loc = Location((sata_x, sata_y, standoff_height + floor_thickness)) * sata_pcb_raw
sata_conn_loc = Location((sata_x, sata_y, standoff_height + floor_thickness)) * sata_conns_raw

# M.2
m2_ghost = Location((m2_x, m2_y, standoff_height + floor_thickness)) * Box(96, 24, 2, align=(Align.MIN, Align.MIN, Align.MIN))

# USB-C
usbc_ghost = Location((usbc_x + usbc_bracket_width/2, usbc_y + usbc_bracket_thickness, floor_thickness + usbc_hole_height)) * Rotation(90, 0, 0) * Cylinder(radius=15/2, height=40, align=(Align.CENTER, Align.CENTER, Align.MIN))

if __name__ == "__main__":
    box_part, text_part = make_box()
    
    # Create Assembly for Export
    # Compound allows exporting multiple solids in one file (recognized as parts by Slicers)
    final_assembly = Compound([box_part, text_part])
    
    export_step(final_assembly, "rack_v3_box.step")
    # STL usually flattens/merges flush faces, making text invisible.
    # So we export separate STLs for maximum compatibility.
    export_stl(box_part, "rack_v3_box_base.stl")
    export_stl(text_part, "rack_v3_text.stl")
    # Also keep the combined one just in case
    export_stl(final_assembly, "rack_v3_box_combined.stl")
    
    try:
        # Update visualization to show text in a contrasting color
        show(box_part, text_part, dcdc_pcb_loc, dcdc_terms_loc, sata_pcb_loc, sata_conn_loc, m2_ghost, usbc_ghost,
             names=["V3 Box", "Powerbox Text", "DC-DC PCB", "DC-DC Terms (Green)", "SATA PCB", "SATA Conns (White)", "M.2", "USB-C"],
             colors=["lightgray", "black", "red", "green", "blue", "white", "green", "purple"],
             transparent=True)
    except:
        pass
