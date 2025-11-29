// ==============================================================================
// 10" Rack - V106 (Wide Stance & Spaced Boards Edition)
// Fix: Shelf is 190mm breed (past over PCIe). Bordjes maximaal uit elkaar.
// Fix: Gaten voor kabels zijn enorm. Tray schroefgaten blijven 3.2mm.
// ==============================================================================

/* [Render Mode] */
part_to_render = "assembly"; // ["tray", "shelf", "spacers", "assembly"]
show_ghost_boards = true; 

/* [Global Settings] */
wall_thickness = 2;   
floor_thickness = 2;  
shelf_height = 35;     // VERHOOGD naar 35mm voor PCIe clearance
shelf_width = 190;     // EXTRA BREED (Wijdbeens)
shelf_depth_len = 115;
shelf_start_y = 5;
shelf_thickness = 3;
dc_jack_dia = 8.2; 
safe_border = 10; 

// Schroeven
screw_hole_dia = 3.2;  // M3 Tray
screw_pilot_dia = 2.8; // M3 Shelf Poot

/* [Rack Dimensions] */
rack_inner_width = 220; 
tray_depth = 130; 
tray_height = 44.45;    
ear_thickness = 3;         
EPS = 0.01;

/* [Positioning Legs] */
leg_inset = 6; // Poten dicht op de rand voor maximale binnenruimte
sh_off_x = (rack_inner_width - shelf_width)/2;

lx_left = sh_off_x + leg_inset;
lx_right = sh_off_x + shelf_width - leg_inset;
ly_front = shelf_start_y + leg_inset;
ly_back = shelf_start_y + shelf_depth_len - leg_inset;

/* [Component Dimensions & Position] */
pcie_w = 154.3; pcie_d = 67.3; pcie_hole_dist = 47.1; pcie_offset_y = 3.4;
// PCIe (X-As, Gecentreerd onder de 190mm shelf)
// Midden van tray = 110. Kaart is 154. Start = 110 - 77 = 33.
pcie_x = 33; 
pcie_y = 30; 
pcie_standoff_height = 6; 

// --- POWER BOARDS (MAXIMAAL UIT ELKAAR) ---
dcdc_w = 68.5; dcdc_d = 100.3; dcdc_offset = 3.5;
// Helemaal Links (X=5)
dcdc_x = 5; 
dcdc_y = 5; 

sata_real_w = 60; sata_real_d = 80; sata_offset = 4.2;
// Helemaal Rechts (190 - 60 - 5 = 125)
sata_x = 125; 
sata_y = 15; 


// ================== Logic Selector ==================

if (part_to_render == "tray") {
    generate_tray();
    if (show_ghost_boards) visualize_pcie();
} else if (part_to_render == "shelf") {
    rotate([180,0,0]) {
        generate_shelf();
        if (show_ghost_boards) visualize_power_boards();
    }
} else if (part_to_render == "spacers") {
    generate_spacers();
} else {
    generate_tray();
    color("cyan") translate([sh_off_x, shelf_start_y, floor_thickness]) generate_shelf();
    if (show_ghost_boards) {
        visualize_pcie();
        translate([sh_off_x, shelf_start_y, floor_thickness]) visualize_power_boards();
    }
}

// ================== Parts Generators ==================

module generate_tray() {
    difference() {
        union() {
            clean_frame_structure(); 
            skeleton_floor_final(); 
            
            // PCIe Mount Eiland
            translate([pcie_x - 5, pcie_y - 5, 0])
                 cube([20, pcie_d + 10, floor_thickness]);
            
            // PCIe Support Balk
            translate([pcie_x + pcie_w - 10, pcie_y, 0])
                cube([10, pcie_d, floor_thickness + pcie_standoff_height]);

            // Poot Bases
            translate([lx_left, ly_front, 0]) poot_base();
            translate([lx_left, ly_back, 0]) poot_base();
            translate([lx_right, ly_front, 0]) poot_base();
            translate([lx_right, ly_back, 0]) poot_base();

            // Standoffs PCIe
            translate([pcie_x + 7.4, pcie_y + pcie_offset_y, floor_thickness - EPS])
                pcie_mounts_shape_left();
        }

        union() {
            rack_slots_cutter_dual(); 
            
            // DC Jack Gat
            translate([15, tray_depth + 5, 8]) 
                rotate([90,0,0]) cylinder(h=10, d=dc_jack_dia, $fn=30);
            
            // PCIe Schroefgaten
            translate([pcie_x + 7.4, pcie_y + pcie_offset_y, 0])
                pcie_mounts_holes_left();
                
            // SHELF SCHROEFGATEN (3.2mm)
            translate([lx_left, ly_front, -10]) cylinder(h=50, d=screw_hole_dia, $fn=20);
            translate([lx_left, ly_back, -10]) cylinder(h=50, d=screw_hole_dia, $fn=20);
            translate([lx_right, ly_front, -10]) cylinder(h=50, d=screw_hole_dia, $fn=20);
            translate([lx_right, ly_back, -10]) cylinder(h=50, d=screw_hole_dia, $fn=20);
        }
    }
}

module generate_shelf() {
    difference() {
        union() {
            // Dek
            translate([0, 0, shelf_height])
                rounded_plate(shelf_width, shelf_depth_len, shelf_thickness, 2);
            
            // Poten
            translate([leg_inset, leg_inset, 0]) leg_for_screw();
            translate([leg_inset, shelf_depth_len - leg_inset, 0]) leg_for_screw();
            translate([shelf_width - leg_inset, leg_inset, 0]) leg_for_screw();
            translate([shelf_width - leg_inset, shelf_depth_len - leg_inset, 0]) leg_for_screw();
            
            // Ribben
            hull() {
                translate([leg_inset, leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
                translate([shelf_width-leg_inset, leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
            }
            hull() {
                translate([leg_inset, shelf_depth_len-leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
                translate([shelf_width-leg_inset, shelf_depth_len-leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
            }
            hull() {
                translate([leg_inset, leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
                translate([leg_inset, shelf_depth_len-leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
            }
            hull() {
                translate([shelf_width-leg_inset, leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
                translate([shelf_width-leg_inset, shelf_depth_len-leg_inset, shelf_height]) cylinder(h=shelf_thickness, d=12);
            }
            
            // Bosses (Onderkant)
            translate([dcdc_x, dcdc_y, shelf_height - 4]) 
                board_mounts_bosses(dcdc_w, dcdc_d, dcdc_offset);
            translate([sata_x, sata_y, shelf_height - 4])
                board_mounts_bosses(sata_real_w, sata_real_d, sata_offset);
        }
        
        union() {
            // Gaten
            translate([dcdc_x, dcdc_y, shelf_height - 10]) 
                board_mounts_holes(dcdc_w, dcdc_d, dcdc_offset);
            translate([sata_x, sata_y, shelf_height - 10])
                board_mounts_holes(sata_real_w, sata_real_d, sata_offset);
            
            // KABELGATEN (MAXIMAAL!)
            // Links (Onder DC-DC) - Maximaal binnen de mounts
            // Board: 68.5 breed. Mounts op 3.5. Boss radius ~4. Safe start ~8.
            translate([dcdc_x + 9, dcdc_y + 9, shelf_height - 5]) simple_rounded_rect(50, 82, 20); 
            
            // MIDDEN SPEED HOLE (Printtijd besparing)
            // Aangepast: Moet tussen de boards blijven!
            // DC-DC eindigt op ~74 (boss). SATA begint op ~125 (boss).
            // Gat: X=76 tot 123 (Width 47).
            translate([76, 15, shelf_height - 5]) simple_rounded_rect(47, 85, 20);

            // Rechts (Onder SATA) - Maximaal binnen de mounts
            // Board: 60 breed. Mounts op 4.2. Boss radius ~4. Safe start ~9.
            translate([sata_x + 10, sata_y + 10, shelf_height - 5]) simple_rounded_rect(40, 60, 20); 
            
            // Poot kernen
            translate([leg_inset, leg_inset, 0]) leg_screw_core();
            translate([leg_inset, shelf_depth_len - leg_inset, 0]) leg_screw_core();
            translate([shelf_width - leg_inset, leg_inset, 0]) leg_screw_core();
            translate([shelf_width - leg_inset, shelf_depth_len - leg_inset, 0]) leg_screw_core();
        }
    }
}

module generate_spacers() {
    for(i=[0:7]) {
        translate([i*12, 0, 0]) 
        difference() {
            cylinder(h=4, r=3.5, $fn=20);
            translate([0,0,-1]) cylinder(h=6, r=1.6, $fn=20);
        }
    }
}

// ================== Helpers ==================

module skeleton_floor_final() {
    linear_extrude(floor_thickness) {
        difference() {
            square([rack_inner_width, tray_depth]);
            difference() {
                intersection() {
                    hex_pattern_2d(); 
                    translate([safe_border, safe_border])
                        square([rack_inner_width - 2*safe_border, tray_depth - 2*safe_border]);
                }
                union() {
                    translate([pcie_x - 5, pcie_y - 5]) square([20, pcie_d + 10]);
                    translate([pcie_x + pcie_w - 10, pcie_y]) square([10, pcie_d]);

                    translate([lx_left, ly_front]) circle(d=22, $fn=40);
                    translate([lx_left, ly_back]) circle(d=22, $fn=40);
                    translate([lx_right, ly_front]) circle(d=22, $fn=40);
                    translate([lx_right, ly_back]) circle(d=22, $fn=40);
                }
            }
        }
    }
}

module clean_frame_structure() {
    ear_w_total = (254 - rack_inner_width) / 2;
    
    // Faceplate
    translate([0, 0, 0]) cube([rack_inner_width, ear_thickness, tray_height]); 
    // Achterwand
    translate([0, tray_depth-wall_thickness, 0]) cube([rack_inner_width, wall_thickness, 22]);

    // Zijwanden (Schuin)
    translate([-ear_w_total, 0, 0]) {
        hull() {
            translate([2, ear_thickness, tray_height - 2]) rotate([90,0,0]) cylinder(h=ear_thickness, r=2, $fn=20);
            translate([2, ear_thickness, 2]) rotate([90,0,0]) cylinder(h=ear_thickness, r=2, $fn=20);
            translate([ear_w_total, 0, 0]) cube([0.1, ear_thickness, tray_height]);
        }
        hull() {
            translate([ear_w_total, ear_thickness, 0]) cube([wall_thickness, 0.1, tray_height]);
            translate([ear_w_total, 15, 0]) cube([wall_thickness, 0.1, 22]);
            translate([ear_w_total, ear_thickness, 0]) cube([wall_thickness, 15, floor_thickness]);
        }
        translate([ear_w_total, 15, 0]) 
            cube([wall_thickness, tray_depth - 15, 22]);
    }
    
    translate([rack_inner_width + ear_w_total, 0, 0]) mirror([1,0,0]) {
        hull() {
            translate([2, ear_thickness, tray_height - 2]) rotate([90,0,0]) cylinder(h=ear_thickness, r=2, $fn=20);
            translate([2, ear_thickness, 2]) rotate([90,0,0]) cylinder(h=ear_thickness, r=2, $fn=20);
            translate([ear_w_total, 0, 0]) cube([0.1, ear_thickness, tray_height]);
        }
        hull() {
            translate([ear_w_total, ear_thickness, 0]) cube([wall_thickness, 0.1, tray_height]);
            translate([ear_w_total, 15, 0]) cube([wall_thickness, 0.1, 22]);
            translate([ear_w_total, ear_thickness, 0]) cube([wall_thickness, 15, floor_thickness]);
        }
        translate([ear_w_total, 15, 0]) 
            cube([wall_thickness, tray_depth - 15, 22]);
    }
}

module hex_pattern_2d() {
    hole_r = 16; 
    step_x = hole_r * 1.732;
    step_y = hole_r * 1.5;
    for (x = [0 : step_x : 220]) { 
        for (y = [0 : step_y : tray_depth]) {
            translate([x + ((y/step_y)%2) * (step_x/2), y])
                rotate(30) circle(r=hole_r - 2, $fn=6);
        }
    }
}

module poot_base() { cylinder(h=floor_thickness, d=18, $fn=40); }
module board_mounts_bosses(w, d, offset) {
    h_boss = 4; 
    translate([offset, offset, 0]) cylinder(h=h_boss, r=4, $fn=20); 
    translate([w-offset, offset, 0]) cylinder(h=h_boss, r=4, $fn=20);
    translate([offset, d-offset, 0]) cylinder(h=h_boss, r=4, $fn=20); 
    translate([w-offset, d-offset, 0]) cylinder(h=h_boss, r=4, $fn=20);
}
module leg_for_screw() { cylinder(h=shelf_height, d=12, $fn=30); }
module leg_screw_core() { translate([0,0,-1]) cylinder(h=30, d=screw_pilot_dia, $fn=20); }
module rounded_plate(w, d, h, r) {
    hull() {
        translate([r, r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([w-r, r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([r, d-r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([w-r, d-r, 0]) cylinder(h=h, r=r, $fn=20);
    }
}
module simple_rounded_rect(w, d, h) {
    r = 3;
    hull() {
        translate([r, r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([w-r, r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([r, d-r, 0]) cylinder(h=h, r=r, $fn=20);
        translate([w-r, d-r, 0]) cylinder(h=h, r=r, $fn=20);
    }
}
module rack_slots_cutter_dual() {
    x_left = (220 - 236.5) / 2; x_right = 220 + abs(x_left); z_center = 44.45 / 2;
    module cutter() { hull() { translate([-(12-7)/2, 0, 0]) cylinder(h=40, d=7, $fn=30, center=true); translate([(12-7)/2, 0, 0]) cylinder(h=40, d=7, $fn=30, center=true); } }
    translate([x_left, 0, z_center + (30/2)]) rotate([-90, 0, 0]) cutter();
    translate([x_left, 0, z_center - (30/2)]) rotate([-90, 0, 0]) cutter();
    translate([x_right, 0, z_center + (30/2)]) rotate([-90, 0, 0]) cutter();
    translate([x_right, 0, z_center - (30/2)]) rotate([-90, 0, 0]) cutter();
}
module board_mounts_holes(w, d, offset) {
    translate([offset, offset, 0]) cylinder(h=50, r=1.6, $fn=20); 
    translate([w-offset, offset, 0]) cylinder(h=50, r=1.6, $fn=20);
    translate([offset, d-offset, 0]) cylinder(h=50, r=1.6, $fn=20); 
    translate([w-offset, d-offset, 0]) cylinder(h=50, r=1.6, $fn=20);
}
module pcie_mounts_shape_left() {
    cylinder(h=pcie_standoff_height, r=4, $fn=20);
    translate([0, pcie_hole_dist, 0]) cylinder(h=pcie_standoff_height, r=4, $fn=20);
}
module pcie_mounts_holes_left() {
    translate([0,0,-10]) cylinder(h=50, r=1.4, $fn=20);
    translate([0, pcie_hole_dist, -10]) cylinder(h=50, r=1.4, $fn=20);
}
// Visualizers
module visualize_pcie() {
    translate([pcie_x, pcie_y, floor_thickness + pcie_standoff_height]) 
        color("green", 0.6) {
            difference() {
                cube([pcie_w, pcie_d, 1.6]); 
                translate([0, 0, -1]) cube([5, pcie_d, 10]); 
            }
        }
}
module visualize_power_boards() {
    translate([dcdc_x, dcdc_y, shelf_height + shelf_thickness + 2])
        color("red", 0.6) cube([dcdc_w, dcdc_d, 1.6]);
    translate([sata_x, sata_y, shelf_height + shelf_thickness + 2])
        color("blue", 0.6) cube([sata_real_w, sata_real_d, 1.6]);
}
