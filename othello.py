# Flippy (an Othello or Reversi clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

# Based on the "reversi.py" code that originally appeared in "Invent
# Your Own Computer Games with Python", chapter 15:
#   http://inventwithpython.com/chapter15.html

# Modified to add the minimax algorithm by Sergi Magret Goy on 22/05/2020

import random, sys, pygame, time, copy, math
import os.path
from pygame.locals import *

FPS = 10  # frames per second to update the screen
WINDOWWIDTH = 640  # width of the program's window, in pixels
WINDOWHEIGHT = 480  # height in pixels
SPACESIZE = 50  # width & height of each space on the board, in pixels
BOARDWIDTH = 8  # how many columns of spaces on the game board
BOARDHEIGHT = 8  # how many rows of spaces on the game board
WHITE_TILE = 'WHITE_TILE'  # an arbitrary but unique value
BLACK_TILE = 'BLACK_TILE'  # an arbitrary but unique value
EMPTY_SPACE = 'EMPTY_SPACE'  # an arbitrary but unique value
HINT_TILE = 'HINT_TILE'  # an arbitrary but unique value
ANIMATIONSPEED = 50  # integer from 1 to 100, higher is faster animation

# Amount of space on the left & right side (XMARGIN) or above and below
# (YMARGIN) the game board, in pixels.
XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * SPACESIZE)) / 2)
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * SPACESIZE)) / 2)

#              R    G    B
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
GREEN      = (  0, 155,   0)
BRIGHTBLUE = (  0,  50, 255)
BROWN      = (174,  94,   0)

TEXTBGCOLOR1 = BRIGHTBLUE
TEXTBGCOLOR2 = GREEN
GRIDLINECOLOR = BLACK
TEXTCOLOR = WHITE
HINTCOLOR = BROWN


def main():
    global MAINCLOCK, DISPLAYSURF, FONT, BIGFONT, BGIMAGE

    pygame.init()
    MAINCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Othello')
    FONT = pygame.font.Font('freesansbold.ttf', 16)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 32)

    # Set up the background image.
    filepath = os.path.dirname(__file__)
    boardImage = pygame.image.load(os.path.join(filepath, 'flippyboard.png'))
    # boardImage = pygame.image.load('flippyboard.png')
    # Use smoothscale() to stretch the board image to fit the entire board:
    boardImage = pygame.transform.smoothscale(boardImage, (BOARDWIDTH * SPACESIZE, BOARDHEIGHT * SPACESIZE))
    boardImageRect = boardImage.get_rect()
    boardImageRect.topleft = (XMARGIN, YMARGIN)
    BGIMAGE = pygame.image.load(os.path.join(filepath, 'flippybackground.png'))
    # Use smoothscale() to stretch the background image to fit the entire window:
    BGIMAGE = pygame.transform.smoothscale(BGIMAGE, (WINDOWWIDTH, WINDOWHEIGHT))
    BGIMAGE.blit(boardImage, boardImageRect)

    # Run the main game.
    while True:
        if runGame() == False:
            break


def runGame():
    # Plays a single game of reversi each time this function is called.

    # Reset the board and game.
    mainBoard = getNewBoard()
    resetBoard(mainBoard)
    showHints = False

    # Draw the starting board and ask the player what color they want.
    drawBoard(mainBoard)
    playerTile, computerTile = enterPlayerTile()
    turn = 'player' if playerTile == BLACK_TILE else 'computer'

    # Make the Surface and Rect objects for the "New Game" and "Hints" buttons
    newGameSurf = FONT.render('New Game', True, TEXTCOLOR, TEXTBGCOLOR2)
    newGameRect = newGameSurf.get_rect()
    newGameRect.topright = (WINDOWWIDTH - 8, 10)
    hintsSurf = FONT.render('Hints', True, TEXTCOLOR, TEXTBGCOLOR2)
    hintsRect = hintsSurf.get_rect()
    hintsRect.topright = (WINDOWWIDTH - 8, 40)

    while True:  # main game loop
        # Keep looping for player and computer's turns.
        if turn == 'player':
            # Player's turn:
            if not getValidMoves(mainBoard, playerTile)[0]:
                # If it's the player's turn but they
                # can't move, then end the game.
                break
            movexy = None
            while movexy is None:
                # Keep looping until the player clicks on a valid space.

                # Determine which board data structure to use for display.
                if showHints:
                    boardToDraw = getBoardWithValidMoves(mainBoard, playerTile)
                else:
                    boardToDraw = mainBoard

                checkForQuit()
                for event in pygame.event.get():  # event handling loop
                    if event.type == MOUSEBUTTONUP:
                        # Handle mouse click events
                        mousex, mousey = event.pos
                        if newGameRect.collidepoint((mousex, mousey)):
                            # Start a new game
                            return True
                        elif hintsRect.collidepoint((mousex, mousey)):
                            # Toggle hints mode
                            showHints = not showHints
                        # movexy is set to a two-item tuple XY coordinate, or None value
                        movexy = getSpaceClicked(mousex, mousey)
                        if movexy != None and not isValidMove(mainBoard, playerTile, movexy[0], movexy[1]):
                            movexy = None

                # Draw the game board.
                drawBoard(boardToDraw)
                drawInfo(boardToDraw, playerTile, computerTile, turn)

                # Draw the "New Game" and "Hints" buttons.
                DISPLAYSURF.blit(newGameSurf, newGameRect)
                DISPLAYSURF.blit(hintsSurf, hintsRect)

                MAINCLOCK.tick(FPS)
                pygame.display.update()

            # Make the move and end the turn.
            print("next move by the human:", movexy[0], movexy[1])
            makeMove(mainBoard, playerTile, movexy[0], movexy[1], True)
            valid_moves = getValidMoves(mainBoard, computerTile)[0]
            print(len(valid_moves), "valid moves by the computer:", valid_moves)
            if valid_moves:
                # Only set for the computer's turn if it can make a move.
                turn = 'computer'

        else:
            # Computer's turn:
            possible_moves = getValidMoves(mainBoard, computerTile)[0]
            if not possible_moves:
                # If it was set to be the computer's turn but
                # they can't move, then end the game.
                break

            # Draw the board.
            drawBoard(mainBoard)
            drawInfo(mainBoard, playerTile, computerTile, turn)

            # Draw the "New Game" and "Hints" buttons.
            DISPLAYSURF.blit(newGameSurf, newGameRect)
            DISPLAYSURF.blit(hintsSurf, hintsRect)

            # Make it look like the computer is thinking by pausing a bit.
            pauseUntil = time.time() + random.randint(5, 15) * 0.1
            while time.time() < pauseUntil:
                pygame.display.update()

            # Make the move and end the turn.
            x, y = getComputerMove(mainBoard, computerTile)
            print("next move by the AI:", x, y)
            makeMove(mainBoard, computerTile, x, y, True)
            valid_moves = getValidMoves(mainBoard, playerTile)[0]
            print(len(valid_moves), "valid moves by the player:", valid_moves)
            if valid_moves:
                # Only set for the player's turn if they can make a move.
                turn = 'player'

    # Display the final score.
    drawBoard(mainBoard)
    scores = getScoreOfBoard(mainBoard)

    # Determine the text of the message to display.
    if scores[playerTile] > scores[computerTile]:
        text = 'You beat the computer by %s points! Congratulations!' % \
               (scores[playerTile] - scores[computerTile])
    elif scores[playerTile] < scores[computerTile]:
        text = 'You lost. The computer beat you by %s points.' % \
               (scores[computerTile] - scores[playerTile])
    else:
        text = 'The game was a tie!'

    textSurf = FONT.render(text, True, TEXTCOLOR, TEXTBGCOLOR1)
    textRect = textSurf.get_rect()
    textRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
    DISPLAYSURF.blit(textSurf, textRect)

    # Display the "Play again?" text with Yes and No buttons.
    text2Surf = BIGFONT.render('Play again?', True, TEXTCOLOR, TEXTBGCOLOR1)
    text2Rect = text2Surf.get_rect()
    text2Rect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 50)

    # Make "Yes" button.
    yesSurf = BIGFONT.render('Yes', True, TEXTCOLOR, TEXTBGCOLOR1)
    yesRect = yesSurf.get_rect()
    yesRect.center = (int(WINDOWWIDTH / 2) - 60, int(WINDOWHEIGHT / 2) + 90)

    # Make "No" button.
    noSurf = BIGFONT.render('No', True, TEXTCOLOR, TEXTBGCOLOR1)
    noRect = noSurf.get_rect()
    noRect.center = (int(WINDOWWIDTH / 2) + 60, int(WINDOWHEIGHT / 2) + 90)

    while True:
        # Process events until the user clicks on Yes or No.
        checkForQuit()
        for event in pygame.event.get():  # event handling loop
            if event.type == MOUSEBUTTONUP:
                mousex, mousey = event.pos
                if yesRect.collidepoint((mousex, mousey)):
                    return True
                elif noRect.collidepoint((mousex, mousey)):
                    return False
        DISPLAYSURF.blit(textSurf, textRect)
        DISPLAYSURF.blit(text2Surf, text2Rect)
        DISPLAYSURF.blit(yesSurf, yesRect)
        DISPLAYSURF.blit(noSurf, noRect)
        pygame.display.update()
        MAINCLOCK.tick(FPS)


def translateBoardToPixelCoord(x, y):
    return XMARGIN + x * SPACESIZE + int(SPACESIZE / 2), YMARGIN + y * SPACESIZE + int(SPACESIZE / 2)


def animateTileChange(tilesToFlip, tileColor, additionalTile):
    # Draw the additional tile that was just laid down. (Otherwise we'd
    # have to completely redraw the board & the board info.)
    if tileColor == WHITE_TILE:
        additionalTileColor = WHITE
    else:
        additionalTileColor = BLACK
    additionalTileX, additionalTileY = translateBoardToPixelCoord(additionalTile[0], additionalTile[1])
    pygame.draw.circle(DISPLAYSURF, additionalTileColor, (additionalTileX, additionalTileY), int(SPACESIZE / 2) - 4)
    pygame.display.update()

    for rgbValues in range(0, 255, int(ANIMATIONSPEED * 2.55)):
        if rgbValues > 255:
            rgbValues = 255
        elif rgbValues < 0:
            rgbValues = 0

        if tileColor == WHITE_TILE:
            color = tuple([rgbValues] * 3)  # rgbValues goes from 0 to 255
        elif tileColor == BLACK_TILE:
            color = tuple([255 - rgbValues] * 3)  # rgbValues goes from 255 to 0

        for x, y in tilesToFlip:
            centerx, centery = translateBoardToPixelCoord(x, y)
            pygame.draw.circle(DISPLAYSURF, color, (centerx, centery), int(SPACESIZE / 2) - 4)
        pygame.display.update()
        MAINCLOCK.tick(FPS)
        checkForQuit()


def drawBoard(board):
    # Draw background of board.
    DISPLAYSURF.blit(BGIMAGE, BGIMAGE.get_rect())

    # Draw grid lines of the board.
    for x in range(BOARDWIDTH + 1):
        # Draw the horizontal lines.
        startx = (x * SPACESIZE) + XMARGIN
        starty = YMARGIN
        endx = (x * SPACESIZE) + XMARGIN
        endy = YMARGIN + (BOARDHEIGHT * SPACESIZE)
        pygame.draw.line(DISPLAYSURF, GRIDLINECOLOR, (startx, starty), (endx, endy))
    for y in range(BOARDHEIGHT + 1):
        # Draw the vertical lines.
        startx = XMARGIN
        starty = (y * SPACESIZE) + YMARGIN
        endx = XMARGIN + (BOARDWIDTH * SPACESIZE)
        endy = (y * SPACESIZE) + YMARGIN
        pygame.draw.line(DISPLAYSURF, GRIDLINECOLOR, (startx, starty), (endx, endy))

    # Draw the black & white tiles or hint spots.
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            centerx, centery = translateBoardToPixelCoord(x, y)
            if board[x][y] == WHITE_TILE or board[x][y] == BLACK_TILE:
                if board[x][y] == WHITE_TILE:
                    tileColor = WHITE
                else:
                    tileColor = BLACK
                pygame.draw.circle(DISPLAYSURF, tileColor, (centerx, centery), int(SPACESIZE / 2) - 4)
            if board[x][y] == HINT_TILE:
                pygame.draw.rect(DISPLAYSURF, HINTCOLOR, (centerx - 4, centery - 4, 8, 8))


def getSpaceClicked(mousex, mousey):
    # Return a tuple of two integers of the board space coordinates where
    # the mouse was clicked. (Or returns None not in any space.)
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if mousex > x * SPACESIZE + XMARGIN and \
                    mousex < (x + 1) * SPACESIZE + XMARGIN and \
                    mousey > y * SPACESIZE + YMARGIN and \
                    mousey < (y + 1) * SPACESIZE + YMARGIN:
                return (x, y)
    return None


def drawInfo(board, playerTile, computerTile, turn):
    # Draws scores and whose turn it is at the bottom of the screen.
    scores = getScoreOfBoard(board)
    scoreSurf = FONT.render("Player Score: %s    Computer Score: %s    %s's Turn" % (
        str(scores[playerTile]), str(scores[computerTile]), turn.title()), True, TEXTCOLOR)
    scoreRect = scoreSurf.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 5)
    DISPLAYSURF.blit(scoreSurf, scoreRect)


def resetBoard(board):
    # Blanks out the board it is passed, and sets up starting tiles.
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            board[x][y] = EMPTY_SPACE

    # Add starting pieces to the center
    board[3][3] = WHITE_TILE
    board[3][4] = BLACK_TILE
    board[4][3] = BLACK_TILE
    board[4][4] = WHITE_TILE


def getNewBoard():
    # Creates a brand new, empty board data structure.
    board = []
    for i in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)

    return board


def isValidMove(board, tile, xstart, ystart):
    # Returns False if the player's move is invalid. If it is a valid
    # move, returns a list of spaces of the captured pieces.
    if board[xstart][ystart] != EMPTY_SPACE or not isOnBoard(xstart, ystart):
        return False

    board[xstart][ystart] = tile  # temporarily set the tile on the board.

    if tile == WHITE_TILE:
        otherTile = BLACK_TILE
    else:
        otherTile = WHITE_TILE

    tilesToFlip = []
    # check each of the eight directions:
    for xdirection, ydirection in [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]:
        x, y = xstart, ystart
        x += xdirection
        y += ydirection
        if isOnBoard(x, y) and board[x][y] == otherTile:
            # The piece belongs to the other player next to our piece.
            x += xdirection
            y += ydirection
            if not isOnBoard(x, y):
                continue
            while board[x][y] == otherTile:
                x += xdirection
                y += ydirection
                if not isOnBoard(x, y):
                    break  # break out of while loop, continue in for loop
            if not isOnBoard(x, y):
                continue
            if board[x][y] == tile:
                # There are pieces to flip over. Go in the reverse
                # direction until we reach the original space, noting all
                # the tiles along the way.
                while True:
                    x -= xdirection
                    y -= ydirection
                    if x == xstart and y == ystart:
                        break
                    tilesToFlip.append((x, y))

    board[xstart][ystart] = EMPTY_SPACE  # make space empty
    if len(tilesToFlip) == 0:  # If no tiles flipped, this move is invalid
        return False
    return tilesToFlip


def isOnBoard(x, y):
    # Returns True if the coordinates are located on the board.
    return x >= 0 and x < BOARDWIDTH and y >= 0 and y < BOARDHEIGHT


def getBoardWithValidMoves(board, tile):
    # Returns a new board with hint markings.
    dupeBoard = copy.deepcopy(board)

    for x, y in getValidMoves(dupeBoard, tile)[0]:
        dupeBoard[x][y] = HINT_TILE
    return dupeBoard


def getValidMoves(board, tile):
    # Returns a list of (x,y) tuples of all valid moves.
    validMoves = []
    tiles_to_flip = []
    reorder = False

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            flip = isValidMove(board, tile, x, y)
            if flip:
                validMoves.append((x, y))
                tiles_to_flip.append(len(flip))
                if not reorder and (isX(x, y) or isC(x, y) or isCorner(x, y)):  # If there is not a special tile to reorder and the current tile is special, then we set reorder to True
                    reorder = True

    return validMoves, tiles_to_flip, reorder


def getScoreOfBoard(board):
    # Determine the score by counting the tiles.
    xscore = 0
    oscore = 0
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if board[x][y] == WHITE_TILE:
                xscore += 1
            if board[x][y] == BLACK_TILE:
                oscore += 1
    return {WHITE_TILE: xscore, BLACK_TILE: oscore}


def enterPlayerTile():
    # Draws the text and handles the mouse click events for letting
    # the player choose which color they want to be.  Returns
    # [WHITE_TILE, BLACK_TILE] if the player chooses to be White,
    # [BLACK_TILE, WHITE_TILE] if Black.

    # Create the text.
    textSurf = FONT.render('Do you want to be white or black?', True, TEXTCOLOR, TEXTBGCOLOR1)
    textRect = textSurf.get_rect()
    textRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))

    xSurf = BIGFONT.render('White', True, TEXTCOLOR, TEXTBGCOLOR1)
    xRect = xSurf.get_rect()
    xRect.center = (int(WINDOWWIDTH / 2) - 60, int(WINDOWHEIGHT / 2) + 40)

    oSurf = BIGFONT.render('Black', True, TEXTCOLOR, TEXTBGCOLOR1)
    oRect = oSurf.get_rect()
    oRect.center = (int(WINDOWWIDTH / 2) + 60, int(WINDOWHEIGHT / 2) + 40)

    while True:
        # Keep looping until the player has clicked on a color.
        checkForQuit()
        for event in pygame.event.get():  # event handling loop
            if event.type == MOUSEBUTTONUP:
                mousex, mousey = event.pos
                if xRect.collidepoint((mousex, mousey)):
                    return [WHITE_TILE, BLACK_TILE]
                elif oRect.collidepoint((mousex, mousey)):
                    return [BLACK_TILE, WHITE_TILE]

        # Draw the screen.
        DISPLAYSURF.blit(textSurf, textRect)
        DISPLAYSURF.blit(xSurf, xRect)
        DISPLAYSURF.blit(oSurf, oRect)
        pygame.display.update()
        MAINCLOCK.tick(FPS)


def makeMove(board, tile, xstart, ystart, realMove=False):
    # Place the tile on the board at xstart, ystart, and flip tiles
    # Returns False if this is an invalid move, tilesToFlip if it is valid.
    tilesToFlip = isValidMove(board, tile, xstart, ystart)
    if not tilesToFlip:
        return False

    board[xstart][ystart] = tile

    if realMove:
        animateTileChange(tilesToFlip, tile, (xstart, ystart))

    for x, y in tilesToFlip:
        board[x][y] = tile
    return tilesToFlip


def undoMove(board, tile, xstart, ystart, tiles_to_flip):
    # This function is not used in the final program.
    # Remove a move from the board, [<xstart>,<ystart>] i assigned as empty
    # then all the tiles that have been flipped are flipped over to reassign them to the opponent of <tile>

    if not tiles_to_flip:
        return False

    board[xstart][ystart] = EMPTY_SPACE

    for x, y in tiles_to_flip:
        board[x][y] = opponent(tile)
    return True


def opponent(tile):
    # Returns the opponent of tile
    return WHITE_TILE if tile == BLACK_TILE else BLACK_TILE


def isCorner(x, y):
    # Check if a position is in any of the board's corners
    if x == 0 and y == 0:  # Top left corner
        return True
    elif x == 0 and y == 7:  # Top right corner
        return True
    elif x == 7 and y == 0:  # Bottom left corner
        return True
    elif x == 7 and y == 7:  # Bottom right corner
        return True
    else:
        return False


def isEdge(x, y):
    # Returns true if position [x,y] is on the edge of the board, false otherwise
    # Except when is a corner, then returns false
    if isCorner(x, y):
        return False
    elif x == 0 or y == 0 or x == BOARDWIDTH - 1 or y == BOARDHEIGHT - 1:
        return True
    else:
        return False


def surroundedBy(board, x, y, player):
    # Check if a position is surrounded by a lot of pieces of the same colour as <player>
    # A position is good if it's surrounded by a lot of pieces of the same colour as <player>
    # but it's also bad if it's surrounded by a lot of pieces owned by the opponent
    value = 0
    positions_to_check = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1), (x, y + 1),
                          (x - 1, y + 1), (x - 1, y)]
    for x_to_check, y_to_check in positions_to_check:
        if isOnBoard(x_to_check, y_to_check):
            if board[x_to_check][y_to_check] == player:
                value += 5
            elif board[x_to_check][y_to_check] == opponent(player):
                value -= 2
            else:
                value -= 2
    return value


def isC(x, y):
    # Check if the position [x,y] is a C as marked below
    #   0 1 2 3 4 5 6 7
    # 0 . C . . . . C .
    # 1 C X . . . . X C
    # 2 . . . . . . . .
    # 3 . . . . . . . .
    # 4 . . . . . . . .
    # 5 . . . . . . . .
    # 6 C X . . . . X C
    # 7 . C . . . . C .
    if y == 0 and (x == 1 or x == 6):
        return True
    elif y == 1 and (x == 0 or x == 7):
        return True
    elif y == 6 and (x == 0 or x == 7):
        return True
    elif y == 7 and (x == 1 or x == 6):
        return True
    else:
        return False


def isX(x, y):
    # Check if the position [x,y] is an X as marked below
    #   0 1 2 3 4 5 6 7
    # 0 . C . . . . C .
    # 1 C X . . . . X C
    # 2 . . . . . . . .
    # 3 . . . . . . . .
    # 4 . . . . . . . .
    # 5 . . . . . . . .
    # 6 C X . . . . X C
    # 7 . C . . . . C .
    if y == 1 and (x == 1 or x == 6):
        return True
    elif y == 6 and (x == 1 or x == 6):
        return True
    else:
        return False


def valueOfOpponentMoves(opponent_moves):
    # The less moves your opponent can perfom the better for the AI
    n_op_moves = len(opponent_moves)
    if n_op_moves == 0:
        return 50
    elif n_op_moves == 1:
        return 10
    elif n_op_moves <= 5:
        return 10
    elif n_op_moves <= 10:
        return -10
    else:
        return -50


def valueOfPossibleMoves(possible_moves):
    # The more moves you (AI) can perform the better
    n_moves = len(possible_moves)
    if n_moves == 0:
        return -50
    elif n_moves == 1:
        return -10
    elif n_moves <= 5:
        return 10
    elif n_moves <= 10:
        return 20
    else:
        return 50


def reorderMoves(moves_ordered):
    # Reorder the moves in <moves_ordered> so the it's in the next order: [corners, other_tiles, cs, xs]
    # It's sorted form most important moves to less important moves
    corners = []
    xs = []
    cs = []
    others = []
    for i in range(len(moves_ordered)):
        x, y = moves_ordered[i]
        if isCorner(x, y):
            corners.append((x, y))
        elif isC(x, y):
            cs.append((x, y))
        elif isX(x, y):
            xs.append((x, y))
        else:
            others.append((x, y))

    corners.extend(others)
    corners.extend(cs)
    corners.extend(xs)

    return corners


def cornerAroundBy(board, x, y, player):
    # Returns true if there is a corner around [x,y] position owned by <player>, otherwise false
    positions_to_check = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1), (x, y + 1),
                          (x - 1, y + 1), (x - 1, y)]
    for x_to_check, y_to_check in positions_to_check:
        if isOnBoard(x_to_check, y_to_check) and isCorner(x_to_check, y_to_check) and board[x_to_check][y_to_check] == player:
            return True

    return False


def h(board, computer_tile, possible_moves):
    opponent_moves = getValidMoves(board, opponent(computer_tile))[0]
    h_value = 0
    h_value += valueOfOpponentMoves(opponent_moves)
    h_value += valueOfPossibleMoves(possible_moves)

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            h_value += surroundedBy(board, x, y, computer_tile)
            if board[x][y] == computer_tile:
                h_value += 1
                if isCorner(x, y):
                    h_value += 100
                if isEdge(x, y):
                    h_value += 20
                if isC(x, y):
                    if cornerAroundBy(board, x, y, computer_tile):
                        h_value += 20
                    else:
                        h_value -= 50
                if isX(x, y):
                    if cornerAroundBy(board, x, y, computer_tile):
                        h_value += 20
                    else:
                        h_value -= 90
            elif board[x][y] == opponent(computer_tile):
                h_value -= 1
                if isCorner(x, y):
                    h_value -= 100
                if isEdge(x, y):
                    h_value -= 10
                if isC(x, y):
                    h_value += 50
                if isX(x, y):
                    h_value += 90

    return h_value


def minimax(board, depth, alfa, beta, player, computer_tile):
    possible_moves, number_of_tiles_to_flip, reorder = getValidMoves(board, computer_tile)
    if depth == 0: return h(board, computer_tile, possible_moves), None
    if not possible_moves: return h(board, computer_tile, possible_moves), None

    # Sort the moves by the number of tiles they would flip, the biggest the tiles to flip
    # are at front. To make it a little random and not to play always the same moves, when a
    # random number is 0, we shuffle randomly the moves instead on sorting them.
    random.seed()
    num = random.randint(0, 100)
    if num != 0:
        possible_moves = [move for _, move in sorted(zip(number_of_tiles_to_flip, possible_moves), reverse=True)]
        if reorder:  # Only if there's any special positions where to move next is necessary to reorder
            possible_moves = reorderMoves(possible_moves)
    else:
        random.shuffle(possible_moves)

    if player == computer_tile:  # IA turn
        best_move = possible_moves[0]
        # To prune and make it run faster, we only check for 2/3 of the possible moves
        for x, y in possible_moves[:math.floor(2 * len(possible_moves) / 3)]:
            dupeBoard = copy.deepcopy(board)
            makeMove(dupeBoard, computer_tile, x, y)
            move_value, _ = minimax(dupeBoard, depth - 1, alfa, beta, opponent(player), computer_tile)
            if move_value > alfa:
                alfa = move_value
                best_move = [x, y]

            if alfa >= beta:
                break  # Tall beta

        return alfa, best_move
    else:  # Human player turn
        best_move = possible_moves[0]
        # To prune and make it run faster, we only check for 2/3 of the possible moves
        for x, y in possible_moves[:math.floor(2 * len(possible_moves) / 3)]:
            dupeBoard = copy.deepcopy(board)
            makeMove(dupeBoard, computer_tile, x, y)
            move_value, _ = minimax(dupeBoard, depth - 1, alfa, beta, opponent(player), computer_tile)
            if move_value < beta:
                beta = move_value
                best_move = [x, y]
            if alfa >= beta:
                break  # Tall alfa

        return beta, best_move


def getComputerMove(board, computer_tile):
    _, best_move = minimax(board, 10, -1000, 1000, computer_tile, computer_tile)
    return best_move


def checkForQuit():
    for event in pygame.event.get((QUIT, KEYUP)):  # event handling loop
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            pygame.quit()
            sys.exit()


if __name__ == '__main__':
    main()
