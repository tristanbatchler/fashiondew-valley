from pathlib import Path
from PIL import Image
import numpy
import math
import blend_modes
from dyeing import dyeing_info

def map_between(value, start1, stop1, start2, stop2):
    return start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1))

def logistical_map(x, L, k, x0):
    return L / (1 + math.exp(-k*(x - x0)))

def tint_image(base_image_path: Path, color_name, strength):
    """
    Takes a transparent image and dyes it with the specified color. To do this, first the base 
    image is converted to grayscale, then a solid color image with the same size/edges is overlaid 
    on top of the grayscale image with a blend mode of "overlay". The result is saved to the output 
    path.
    """

    color = dyeing_info[color_name]["rgb"]

    output_path = base_image_path.parent / f"{color_name}_{strength}.png"

    if output_path.exists():
        # print(f"Skipping {output_path} (already exists)")
        return

    # Open base image
    base_image = Image.open(base_image_path)

    base_image_gray = numpy.array(base_image.convert('L').convert('RGBA')).astype('float')

    # Get the max value of the grayscale image (ignoring transparent pixels)
    max_value = 0
    for row in base_image_gray:
        for pixel in row:
            if pixel[3] > 0 and pixel[0] > max_value:
                max_value = pixel[0]

    # Lighten the grayscale image until its new max_value is 255 (careful to preserve transparency)
    lightened_base_image_gray = numpy.copy(base_image_gray)
    for i in range(len(lightened_base_image_gray)):
        for j in range(len(lightened_base_image_gray[i])):
            if lightened_base_image_gray[i][j][3] > 0:
                lightened_base_image_gray[i][j][0] = map_between(lightened_base_image_gray[i][j][0], 0, max_value, 0, 255)
    
    # Create a solid color image with the same size as the base image
    solid_color_raw = Image.new('RGBA', base_image.size, color)

    # Convert to float array (required for blend_modes)
    solid_color = numpy.array(solid_color_raw).astype('float')

    # Blend the grayscale image with the solid color image using the "overlay" blend mode
    lightness_score = logistical_map(max_value, 0.85, -0.07, 132) + 0.15
    strength_score = map_between(strength, 25, 100, 1.25, 2)

    opacity_0 = lightness_score * strength_score
    blend_opacity = opacity_0 + (strength / 25 - 1) * (1 - opacity_0) / 3

    # print(f"{base_image_path} got max value of {max_value}, so a lightness score of {lightness_score} resulting in a blend opacity of {blend_opacity}")

    result_image = numpy.uint8(blend_modes.multiply(base_image_gray, solid_color, min(blend_opacity, 1)))

    # Save the result image

    Image.fromarray(result_image).save(output_path)

