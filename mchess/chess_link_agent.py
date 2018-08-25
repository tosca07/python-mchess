import logging
import queue
import time

import chess
import chess_link as cl


class ChessLinkAgent:
    def __init__(self, appque, timeout=30):
        self.name = 'ChessLinkAgent'
        self.appque = appque
        self.log = logging.getLogger(self.name)
        self.cl_brd = cl.ChessLink(appque, self.name)

        self.cl_brd.get_version()
        self.cl_brd.set_debounce(4)
        self.cl_brd.get_scan_time_ms()
        self.cl_brd.set_scan_time_ms(100.0)
        self.cl_brd.get_scan_time_ms()
        self.init_position = False
        self.cl_brd.get_position()
        self.max_plies = 3

        self.log.debug("waiting for board position")
        start = time.time()
        while time.time()-start < timeout and self.init_position is False:
            self.init_position = self.cl_brd.position_initialized()
            time.sleep(0.1)

        if self.init_position is True:
            self.log.debug("board position received, init ok.")
        else:
            self.log.error(
                "no board position received within timeout {}".format(timeout))

    def agent_ready(self):
        return self.init_position

    def variant_to_positions(self, board, moves, plies):
        pos = []
        mvs = len(moves)
        if mvs > plies:
            mvs = plies

        pos.append(self.cl_brd.fen_to_position(board.fen()))
        for i in range(mvs):
            board.push(moves[i])
            pos.append(self.cl_brd.fen_to_position(board.fen()))
        for i in range(mvs):
            board.pop()
        return pos

    def color(self, col):
        if col == chess.WHITE:
            col = self.cl_brd.WHITE
        else:
            col = self.cl_brd.BLACK
        return col

    def visualize_variant(self, board, moves, plies=1, freq=80):
        if plies > 4:
            plies = 4
        pos = self.variant_to_positions(board, moves, plies)
        self.cl_brd.show_deltas(pos, freq)

    def display_info(self, board, info):
        if 'variant' in info:
            self.visualize_variant(
                board, info['variant'], plies=self.max_plies)

    def set_valid_moves(self, board, val):
        if board.turn == chess.WHITE:
            col = self.cl_brd.WHITE
        else:
            col = self.cl_brd.BLACK
        self.cl_brd.move_from(board.fen(), val, col)