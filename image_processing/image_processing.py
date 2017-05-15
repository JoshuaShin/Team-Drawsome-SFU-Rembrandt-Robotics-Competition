import cv2
import numpy as np
import random

# Main image processing function
# Returns filename of drawing instructions
def process_img(filename, is_bw=1):

    # Load image
    src = cv2.imread(filename)
    if src is None:
        print "File", filename, "does not exist!"
        return

    # Scale and crop image to appropriate proportions and size
    scaled = scale(src)

    blurred = blur(scaled)

    # Detect edges
    edges = detect_edges(blurred)

    # Use edges to detect lines
    lines = detect_lines(edges, 3)
    print "Number of lines:", len(lines)
    if lines is None:
        print "Error: No lines found"
        wait()
        return

    # ### DEBUG IMAGE for detected lines:
    lines_detected_img = debug_detect_lines(lines, scaled.shape)

    shading_lines = []
    if is_bw:
        shading_lines, shaded_img = shade_img_bw(blurred)
    else:
        shading_lines = shade_img_color(blurred)
    final = cv2.bitwise_and(shaded_img, lines_detected_img)

    cv2.imshow('Edges', edges)
    cv2.imshow('Lines drawn', lines_detected_img)
    cv2.imshow('Lines drawn with shade', final)
    wait()


# Scale image to targeted resolution while maintaining aspect ratio
def scale(img):

    target_length = 500.0
    img_h = img.shape[0]
    img_w = img.shape[1]
    ratio = 1.0
    if img_h >= img_w:
        ratio = target_length / img_h
    else:
        ratio = target_length / img_w

    new_h = int(img_h * ratio)
    new_w = int(img_w * ratio)
    scaled = cv2.resize(img, (new_w, new_h))

    print "Source dimension is", img.shape
    print "Scaled dimension is ", scaled.shape

    return scaled


# Blurs the image for edge detection
def blur(img):

    # Gaussian Blur
    blur_kernel_size = 5 # must be odd. larger -> more blur.
    blurred = cv2.GaussianBlur(img, (blur_kernel_size, blur_kernel_size), 0)

    blurred2 = cv2.bilateralFilter(blurred, 7, 75, 75)

    return blurred2


# Runs Canny edge detection
def detect_edges(blurred):

    # norm = normalize_brightness(blurred)
    # cv2.imshow('Normalized 2', norm)

    edges = cv2.Canny(blurred, 50, 150)
    #edges = cv2.Canny(gray,50,150,apertureSize = 3)
    return edges


# Given Canny output, returns lines represented as:
# [
#     [[x1, y1], [x2, y2], [x3,y3]],
#     [[x1, y1], [x2, y2], [x3,y3], [x4,y4]],
#     [[x1, y1], [x2, y2]],
#     [[x1, y1], [x2, y2], [x3,y3], [x4,y4], [x5,y5]],
# ]
# where each list element is a list of coordinates representing a continuous line that passes those coordinates
#
# TODO: implement new algo
def detect_lines(edges, min_line_length=1):
    lines = []
    adjacency = [(i, j) for i in (-1,0,1) for j in (-1,0,1) if not (i == j == 0)]

    print "Edges shape:", edges.shape

    max_y = edges.shape[0]
    max_x = edges.shape[1]

    # Scan the image from top to bottom for an "edge" pixel
    # Edge pixels are white in the Canny output
    for y in range(len(edges)):
        row = edges[y]
        for x in range(len(row)):
            pixel = row[x]
            # Skip pixels that are black (not an edge)
            if pixel == 0:
                continue

            # Once an edge pixel is found, make it black so it won't be drawn again
            edges[y][x] = 0

            # This is the start of a new line
            new_line = []
            new_line.append({'x': x, 'y': y})

            # Repeatedly find neighbors that are also edge pixels until no more are found
            cur_x = x
            cur_y = y
            while True:
                is_next_pixel_found = False
                for dx, dy in adjacency:
                    xp = cur_x + dx
                    yp = cur_y + dy

                    # Skip if out of bounds
                    if not (0 <= xp < max_x and 0 <= yp < max_y):
                        continue

                    # Skip black pixel (not an edge)
                    adjacent_pixel = edges[yp][xp]
                    if adjacent_pixel == 0:
                        continue

                    # This is an edge pixel
                    is_next_pixel_found = True

                    # Make it black so it doesn't get found again
                    edges[yp][xp] = 0

                    # Add coordinate to the line
                    new_line.append({'x': xp, 'y': yp})

                    # Update starting pixel for next iteration
                    cur_x = xp
                    cur_y = yp

                    # Don't need to check other neighbors
                    break

                # If no other edge pixel is found after checking neighbors, this is the end of the line
                if not is_next_pixel_found:
                    # Reject short lines
                    if len(new_line) > min_line_length:
                        lines.append(new_line)
                    break

                # Otherwise, continue looking for the next edge pixel

            # END WHILE TRUE LOOP
            # Repeat until no more nearby edge pixels
        # END for x loop
    # END for y loop

    return lines


# Do something by converting to another color space
# Not too useful
def normalize_brightness(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    for row in hsv:
        for pixel in row:
            pixel[1] = 255

    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    return bgr


# Return list of lines that shades the image
# Black and white only
def shade_img_bw(src):
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    print gray.shape

    # Reduce bit depth
    max_val = 255
    brightness_levels = 8
    diff = 256 / brightness_levels # difference between brightness levels
    gray = (gray / diff) * diff
    cv2.imshow('depth reduced', gray)

    all_hatches = np.zeros(gray.shape, np.uint8)
    all_hatches[:] = 0

    # For each brightness level, replace it with crosshatches
    for i in range(brightness_levels):

        # Isolate the current brightness level using thresholds
        brightness = i * diff
        if brightness != 0:
            # Change colors above the current brightness to 0
            ret, thresh = cv2.threshold(gray, brightness+1, max_val, cv2.THRESH_TOZERO_INV)
            # Reduce the rest brightness colors below
            ret, thresh2 = cv2.threshold(thresh, brightness-1, max_val, cv2.THRESH_BINARY)
        else:
            ret, thresh2 = cv2.threshold(gray, brightness + 1, max_val, cv2.THRESH_BINARY_INV)

        # Only crosshatch if it's not the brightest level
        if i < (brightness_levels - 1):
            # Increase hatch spacing quadratically by squaring
            hatch_spacing = ((i+1) ** 2) + 2
            crosshatch = gen_crosshatch(thresh2.shape, hatch_spacing, 0)

            # Shape the hatching using the shape of the brightness threshold
            # bitwise-AND the cross hatch and threshold brightness
            anded = cv2.bitwise_and(thresh2, crosshatch)
            all_hatches = cv2.bitwise_or(anded, all_hatches)

            #cv2.imshow("anded_" + str(brightness), anded)

    # end for-loop

    all_hatches = 255 - all_hatches
    all_hatches_bgr = cv2.cvtColor(all_hatches, cv2.COLOR_GRAY2BGR)
    cv2.imshow("all_hatches_" + str(brightness), all_hatches_bgr)

    lines = []
    return lines, all_hatches_bgr


# Return list of lines that shades the image
# BACKLOG: colored version
def shade_img_color(src):
    return []


# shape: shape of output
# spacing:  number of pixels between each line
# rotation: angle in radians to tilt the entire hatchingf
# Returns a picture
def gen_crosshatch(shape, spacing, rotation, is_bw=1):
    if spacing < 1:
        print "Crosshatch spacing too small!"
        return

    offset = spacing / 3

    # Make canvas
    canvas = np.zeros(shape, np.uint8)
    canvas[:,:] = 0

    # Draw the lines on a blank canvas
    for i in range(500/spacing):
        # horizontal lines
        x1 = 0
        y1 = i * spacing + random.randint(-offset, offset)
        x2 = 500
        y2 = i * spacing + random.randint(-offset, offset)
        cv2.line(canvas, (x1,y1), (x2,y2), 255, 1)

        # vertical lines
        y1 = i * spacing + random.randint(-offset, offset)
        y2 = i * spacing + random.randint(-offset, offset)
        cv2.line(canvas, (y1, x1), (y2, x2), 255, 1)

    # TODO: Rotate picture by random amount

    # save image as cache, so it doesn't have to be processed again?
    #cv2.imwrite('crosshatch_' + str(spacing) + ".jpg", canvas)

    return canvas

### DEBUG IMAGE for detected lines:
def debug_detect_lines(lines, shape):
    # Draw the lines on a blank canvas
    canvas = np.zeros(shape, np.uint8)
    canvas[:,:] = (255, 255, 255)

    for i, line in enumerate(lines):
        # Make a HSV color for the line
        hue = int( ( float(i) / len(lines) ) * 255 )
        #hue = random.randint(0, 255)
        val = 0
        sat = 255
        for j, coord in enumerate(line):
            #x, y = coord.x, coord.y
            #cv2.line(canvas, (x1,y1), (x2,y2), (0,0,0), 2)
            # Make the HSV color and convert to RGB
            col_hsv = (hue, sat, val)
            col_bgr = cv2.cvtColor(np.array([[col_hsv]], np.uint8), cv2.COLOR_HSV2BGR)[0][0]

            # Update the pixel
            canvas[coord['y']][coord['x']] = col_bgr

    return canvas

# Allows image to be displayed
def wait():
	cv2.waitKey()
	cv2.destroyAllWindows()
