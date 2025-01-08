import cv2
import numpy as np
import pyautogui
import os
import time

def capture_screenshot():
    # Capture the entire screen
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    # Convert RGB (PyAutoGUI default) to BGR (OpenCV format)
    return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

def save_screenshot(image, filename="screenshot.png"):
    cv2.imwrite(filename, image)

def find_board_boundaries(tile_variants_folder):
    # Capture the screenshot dynamically
    screenshot = capture_screenshot()
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Load all tile variants
    tile_variants = []
    for filename in os.listdir(tile_variants_folder):
        tile_path = os.path.join(tile_variants_folder, filename)
        tile_image = cv2.imread(tile_path, cv2.IMREAD_GRAYSCALE)
        if tile_image is not None:
            tile_variants.append(tile_image)

    # Template matching to find tiles
    matches = []
    for tile in tile_variants:
        result = cv2.matchTemplate(screenshot_gray, tile, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8  # Adjust as needed for accuracy
        loc = np.where(result >= threshold)

        for pt in zip(*loc[::-1]):  # Switch x and y
            matches.append(pt)

    # If matches are found, sort to find boundaries
    if matches:
        x_coords = [pt[0] for pt in matches]
        y_coords = [pt[1] for pt in matches]

        # Find the top-left and bottom-right points
        top_left = (min(x_coords), min(y_coords))
        bottom_right = (max(x_coords) + 48, max(y_coords) + 48)
        
        # Save the game board portion of the screenshot for debugging
        game_board = screenshot[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        save_screenshot(game_board, "game_board.png")
        
        return top_left, bottom_right

    return None, None

def click_center_of_board(top_left, bottom_right):
    center_x = ((top_left[0] + bottom_right[0]) // 2) + 24
    center_y = ((top_left[1] + bottom_right[1]) // 2) + 24
    pyautogui.click(center_x, center_y)

def get_block_colors(screenshot, top_left, bottom_right, block_size=48):
    board_colors = []
    for y in range(top_left[1], bottom_right[1], block_size):
        row_colors = []
        for x in range(top_left[0], bottom_right[0], block_size):
            center_x = x + block_size // 2
            center_y = y + block_size // 2
            color = screenshot[center_y, center_x].tolist()  # Convert to list for easier reading
            row_colors.append(color)
            print(f"{(y - top_left[1]) // block_size}, {(x - top_left[0]) // block_size}, {color}")
        board_colors.append(row_colors)
    return board_colors

def create_board_image(board_colors, filename="board_image.png"):
    height = len(board_colors)
    width = len(board_colors[0]) if height > 0 else 0
    board_image = np.zeros((height, width, 3), dtype=np.uint8)
    for y, row in enumerate(board_colors):
        for x, color in enumerate(row):
            board_image[y, x] = color
    save_screenshot(board_image, filename)

def map_colors_to_levels(board_colors):
    color_to_level = {
        (2, 133, 207): 4,
        (2, 186, 210): 3,
        (42, 197, 174): 2,
        (46, 153, 114): 1,
        (194, 192, 220): -1 # marked as mine
    }
    levels = []
    for row in board_colors:
        level_row = []
        for color in row:
            color_tuple = tuple(color)
            if color_tuple in color_to_level:
                level = color_to_level[color_tuple]
            elif 35 <= color[0] <= 50 and 55 <= color[1] <= 70 and 70 <= color[2] <= 90:
                level = -2  # Empty dirt block
            else:
                level = 0 # Grass block
            level_row.append(level)
        levels.append(level_row)
    return levels

def print_levels_matrix(levels):
    for row in levels:
        print(" ".join(map(str, row)))

tile_variants_folder = "tile_variants"

top_left, bottom_right = find_board_boundaries(tile_variants_folder)
if top_left and bottom_right:
    print(f"Board detected from {top_left} to {bottom_right}")
    click_center_of_board(top_left, bottom_right)
    time.sleep(4)  # Wait for the dust to settle
    screenshot = capture_screenshot()  # Capture the screenshot again to get the latest state
    board_colors = get_block_colors(screenshot, top_left, bottom_right)
    create_board_image(board_colors)
    save_screenshot(screenshot[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]], "game_board_latest.png")
    levels = map_colors_to_levels(board_colors)
    print_levels_matrix(levels)
else:
    print("Board not detected!")

