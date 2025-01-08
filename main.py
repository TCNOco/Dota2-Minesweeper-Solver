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
        (194, 192, 220): 99 # marked as mine
    }
    levels = []
    for row in board_colors:
        level_row = []
        for color in row:
            color_tuple = tuple(color)
            if color_tuple in color_to_level:
                level = color_to_level[color_tuple]
            elif 35 <= color[0] <= 50 and 55 <= color[1] <= 70 and 70 <= color[2] <= 90:
                level = 0  # Empty dirt block
            else:
                level = -1 # Grass block
            level_row.append(level)
        levels.append(level_row)
    return levels

def print_levels_matrix(levels):
    for row in levels:
        ## print(" ".join(map(str, row)))
        # Pad each number to 2 spaces
        print(" ".join([f"{num:2}" for num in row]))


def  get_unknown_neighbors(known_unknown, y, x, threatlevel):
    # if at board ends, just use 0 as the imaginary neighbors
    # Get the number of neigbors that are unknown (0)
    known = 0
    unknown = 0
    
    upper_left = known_unknown[y - 1][x - 1] if y - 1 >= 0 and x - 1 >= 0 else 0
    upper = known_unknown[y - 1][x] if y - 1 >= 0 else 0
    upper_right = known_unknown[y - 1][x + 1] if y - 1 >= 0 and x + 1 < len(known_unknown[y]) else 0
    left = known_unknown[y][x - 1] if x - 1 >= 0 else 0
    right = known_unknown[y][x + 1] if x + 1 < len(known_unknown[y]) else 0
    lower_left = known_unknown[y + 1][x - 1] if y + 1 < len(known_unknown) and x - 1 >= 0 else 0
    lower = known_unknown[y + 1][x] if y + 1 < len(known_unknown) else 0
    lower_right = known_unknown[y + 1][x + 1] if y + 1 < len(known_unknown) and x + 1 < len(known_unknown[y]) else 0

    neighbors = [upper_left, upper, upper_right, left, right, lower_left, lower, lower_right]

    for neighbor in neighbors:
        if neighbor == 0:
            unknown += 1
        else:
            known += 1
        
    # print neighboring board
    if unknown == threatlevel:
        print(f"Neighbors ({x} {y}): ")
        print(f"{upper_left}, {upper}, {upper_right}\n{left}, {threatlevel}, {right}\n{lower_left}, {lower}, {lower_right}")

    # # X - 1, Y - 1 to X + 1, Y + 1
    # # known if outside of bounds, or known_unknown[y][x] == 1
    # for y_window in range(y - 1, y + 2):
    #     for x_window in range(x - 1, x + 2):
    #         if y_window < 0 or x_window < 0 or y_window >= len(known_unknown) or x_window >= len(known_unknown[y_window]):
    #             known += 1
    #         elif known_unknown[y_window][x_window] == 1:
    #             known += 1
    #         else:
    #             unknown += 1

    print(f"{x}, {y} - Known: {known}, Unknown: {unknown}, Threat: {threatlevel}")
    return unknown

def right_click_on_bomb(x, y):
    # Right click
    pyautogui.rightClick(x, y)

def mark_bombs(levels, top_left, bottom_right):
    # -1 is unchecked ground
    # 0 is already cleared ground
    # 99 is marked as a mine
    marked_levels = [row[:] for row in levels]  # Create a copy of the levels matrix
    
    # Set known_unknown to the same matrix, but -1 is 0, and 1 is everything else:
    known_unknown = [[0 if cell == -1 else 1 for cell in row] for row in levels] # 0 is unknown, 1 is known
    
    # print unknown board
    print("Known Unknown:")
    print_levels_matrix(known_unknown)

    while True:
        found_match = False
        for y in range(len(levels)):
            for x in range(len(levels[y])):
                if levels[y][x] in range(1, 9):  # If is number: Check around
                    # Check the 3x3 window around the cell
                    known = get_unknown_neighbors(known_unknown, y, x, levels[y][x])
                    if known == levels[y][x]:  # If the same number of unknowns as the number of mines: All are mines
                        # Set all unknowns to mines (X) in marked_levels. Set all unknowns to known in known_unknown
                        for y_window in range(y - 1, y + 2):
                            for x_window in range(x - 1, x + 2):
                                if 0 <= y_window < len(levels) and 0 <= x_window < len(levels[y_window]):
                                    if known_unknown[y_window][x_window] == 0:
                                        marked_levels[y_window][x_window] = 99
                                        known_unknown[y_window][x_window] = 1
                                        # Click on the bomb
                                        right_click_on_bomb(top_left[0] + x_window * 48 + 24, top_left[1] + y_window * 48 + 24)
                                        found_match = True
                                        break
                        if found_match:
                            break
            if found_match:
                break
        if not found_match:
            break
        # Wait for a second and capture a new screenshot
        time.sleep(1)
        screenshot = capture_screenshot()
        board_colors = get_block_colors(screenshot, top_left, bottom_right)
        levels = map_colors_to_levels(board_colors)
        marked_levels = [row[:] for row in levels]  # Update marked_levels with the new levels
        known_unknown = [[0 if cell == -1 else 1 for cell in row] for row in levels]  # Update known_unknown with the new levels

    # Click that point on the screen
    print_levels_matrix(marked_levels)

    return marked_levels

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
    marked_levels = mark_bombs(levels, top_left, bottom_right)
    #print("Marked Levels:")
    #print_levels_matrix(marked_levels)
else:
    print("Board not detected!")

