import os
from PIL import Image, ImageDraw

def create_prairie_wealth_logo(output_path, size=512):
    """
    Generates a high-quality PNG version of the PrairieWealth logo.
    Uses supersampling for smooth edges.
    """
    render_scale = 4
    render_size = size * render_scale
    coord_scale = render_size / 200
    
    img = Image.new("RGBA", (render_size, render_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    def bezier_pts(p0, p1, p2, steps=60):
        return [
            (
                ((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]) * coord_scale,
                ((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]) * coord_scale
            )
            for t in [i/steps for i in range(steps + 1)]
        ]

    # Sun/Coin - Golden Yellow
    r = 50 * coord_scale
    draw.ellipse([100*coord_scale - r, 90*coord_scale - r, 
                  100*coord_scale + r, 90*coord_scale + r], fill="#FBC02D")
    
    # Prairie Hills - Shades of Green
    draw.polygon(bezier_pts((0, 200), (60, 120), (120, 200)), fill="#2E7D32")
    draw.polygon(bezier_pts((80, 200), (140, 130), (200, 200)), fill="#43A047")
    
    # Foundation Line - Deep Forest Green
    draw.rectangle([0, 195*coord_scale, render_size, render_size], fill="#1B5E20")

    # Resize with high-quality resampling for anti-aliasing
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Ensure directory exists and save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Logo created successfully: {output_path}")

if __name__ == "__main__":
    # Define the output path relative to project root
    target = os.path.join("bankapp", "static", "bankapp", "logo.png")
    create_prairie_wealth_logo(target)