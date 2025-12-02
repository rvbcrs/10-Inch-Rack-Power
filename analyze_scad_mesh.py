import re
import statistics

def analyze_scad(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Regex to find all numbers inside the points list
    # Assuming format: points = [[x,y,z], [x,y,z], ...]
    # We just grab all numbers and group them by 3
    
    # First, try to locate the "points" section if possible, to avoid faces
    # But usually points come first.
    # Let's just find all floats.
    
    floats = [float(x) for x in re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', content)]
    
    # This might include face indices which are integers.
    # Points are usually floats.
    # But face indices can be large integers.
    # Let's try to be smarter.
    
    # Look for "points=[" or "points = ["
    start = content.find("points=[")
    if start == -1:
        start = content.find("points = [")
    
    if start == -1:
        print("Could not find 'points=['")
        return

    # Find the end of the points list. It should end with "]," or "]]" before "faces"
    # But finding the matching bracket is safer.
    # Let's just grab a large chunk or find "faces"
    faces_start = content.find("faces", start)
    if faces_start == -1:
        faces_start = len(content)
        
    points_str = content[start:faces_start]
    
    # Extract all numbers
    coords = [float(x) for x in re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+', points_str)]
    
    points = []
    # The first match might be garbage if we are not careful, but usually it's fine.
    # The points are triplets.
    for i in range(0, len(coords), 3):
        if i+2 < len(coords):
            points.append((coords[i], coords[i+1], coords[i+2]))
            
    if not points:
        print("No points found")
        return

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    
    # Analyze Ear Region (X > 110)
    ear_points = [p for p in points if p[0] > 110]
    print(f"\nEar Points (X > 110): {len(ear_points)}")
    
    points_110_115 = [p for p in ear_points if 110 < p[0] < 115]
    print(f"Points in 110-115 range: {len(points_110_115)}")
    
    if points_110_115:
        zs = [p[2] for p in points_110_115]
        print(f"  Z range in 110-115: {min(zs):.2f} to {max(zs):.2f}")
        ys = [p[1] for p in points_110_115]
        print(f"  Y range in 110-115: {min(ys):.2f} to {max(ys):.2f}")

    # Analyze Z levels to find holes
    # Holes along Y axis will appear as circles in X-Z plane.
    # We can look for "rings" of points.
    # Let's bin Z values and see where we have "gaps" or "densities".
    # Actually, let's just look at the points in the middle of the ear depth?
    # Ear thickness is likely small (3mm).
    # So Y is likely 0 to 3.
    ear_front_points = [p for p in ear_points if 0 <= p[1] <= 5]
    print(f"Ear Front Points (Y 0-5): {len(ear_front_points)}")
    
    # Project to X-Z and find circles?
    # Let's just print some sample points to see the structure.
    # Or better, iterate through Z slices and find min/max X.
    
    # Check for Corner Radius
    # Look at points near Top-Right (Max X, Max Z)
    max_x = max([p[0] for p in ear_front_points])
    max_z = max([p[2] for p in ear_front_points])
    print(f"Ear Max X: {max_x:.2f}, Max Z: {max_z:.2f}")
    
    corner_points = [p for p in ear_front_points if p[0] > max_x - 5 and p[2] > max_z - 5]
    print(f"Points in Top-Right Corner (5x5mm): {len(corner_points)}")
    for p in corner_points[:10]:
        print(f"  {p}")
        
    # Check for Holes
    # Holes will be voids in the X-Z plane.
    # Let's look for vertices that have "internal" normals? No normals here.
    # Let's look for Z values that are "inside" the ear but have points.
    # If we have a hole, we will have points on the hole circumference.
    # Let's try to find circles.
    # A hole at (Cx, Cz) with radius R.
    # Points will satisfy (x-Cx)^2 + (z-Cz)^2 ~ R^2.
    # Common screw sizes: M6 (R=3), M5 (R=2.5), M3 (R=1.5).
    # Rack holes are usually 6mm or 7mm diameter?
    # Let's check for points that might form a circle.
    # We can iterate over potential centers and radii? Too slow.
    # Visual inspection of Z-levels might be best.
    
    z_values = sorted([p[2] for p in ear_front_points])
    # Histogram of Z
    from collections import Counter
    z_hist = Counter([round(z, 1) for z in z_values])
    print("\nZ Histogram (peaks might indicate horizontal edges):")
    for z, count in sorted(z_hist.items()):
        if count > 10: # Filter noise
            print(f"  Z={z}: {count}")

    # Pinpoint Hole X
    # We suspect hole is at Z = 15.875.
    # Let's look at points with Z between 15.8 and 16.0.
    # Their X values should be the hole walls (min X and max X of the hole).
    hole_slice_points = [p for p in ear_front_points if 15.5 < p[2] < 16.5]
    if hole_slice_points:
        xs = [p[0] for p in hole_slice_points]
        print(f"\nPoints at Z~15.9 (Hole Center Level):")
        print(f"  Min X: {min(xs):.2f}")
        print(f"  Max X: {max(xs):.2f}")
        print(f"  Avg X: {sum(xs)/len(xs):.2f}")
        # If it's a hole, we might see points at X_center - Radius and X_center + Radius.
        # But since it's a mesh of the *solid*, we might see points *on the cylinder surface*.
        # At Z=Center, the cylinder is vertical in X-Z plane? No, hole is along Y.
        # So in X-Z plane, the hole is a circle.
        # At Z=Center, we are at the "equator" of the circle.
        # So we should see points at X_min and X_max of the circle.
        
    # Check Bottom Slot Dimensions
    # Look for points in the slot region (X 113-123, Z -20 to -12)
    # We want to find the edges of the hole.
    # The points on the hole wall will have Y between 0 and 3.
    # And X/Z on the perimeter.
    
    print(f"\nBottom Slot Analysis:")
    slot_pts = [p for p in ear_front_points if 113 < p[0] < 123 and -20 < p[2] < -12]
    if slot_pts:
        zs = [p[2] for p in slot_pts]
        xs = [p[0] for p in slot_pts]
        print(f"  Z Range: {min(zs):.2f} to {max(zs):.2f}")
        print(f"  X Range: {min(xs):.2f} to {max(xs):.2f}")
        
        # Check for points at the bottom of the slot
        min_z = min(zs)
        bottom_pts = [p for p in slot_pts if p[2] < min_z + 0.2]
        print(f"  Points at Slot Bottom (Z<{min_z+0.2:.2f}):")
        for p in bottom_pts:
            print(f"    ({p[0]:.2f}, {p[2]:.2f})")

    # Check Full Bottom Edge (Z < -22.0)
    print(f"\nFull Bottom Edge Points (Z < -22.0):")
    bottom_edge_pts = [p for p in ear_front_points if p[2] < -22.0]
    if bottom_edge_pts:
        xs = [p[0] for p in bottom_edge_pts]
        print(f"  X range: {min(xs):.2f} to {max(xs):.2f}")
        # Histogram of X to see if it's flat
        x_hist = Counter([round(x, 1) for x in xs])
        print("  X Histogram:")
        for x, count in sorted(x_hist.items()):
            if count > 5:
                print(f"    X={x}: {count}")

analyze_scad("1U-10inch-2-5hdd-SSD-x4-v2.scad")
