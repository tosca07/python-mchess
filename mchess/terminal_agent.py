import logging
import time
import sys
import platform
import threading
import queue

import chess


class TerminalAgent:
    def __init__(self, appque):
        self.name = 'TerminalAgent'
        self.log = logging.getLogger("TerminalAgent")
        self.appque = appque
        self.orientation = True
        self.active = False
        self.max_plies = 6

        self.kbd_moves = []
        self.figrep = {"int": [1, 2, 3, 4, 5, 6, 0, -1, -2, -3, -4, -5, -6],
                       "pythc": [(chess.PAWN, chess.WHITE), (chess.KNIGHT, chess.WHITE), (chess.BISHOP, chess.WHITE), (chess.ROOK, chess.WHITE), (chess.QUEEN, chess.WHITE), (chess.KING, chess.WHITE),
                                 (chess.PAWN, chess.BLACK), (chess.KNIGHT, chess.BLACK), (chess.BISHOP, chess.BLACK), (chess.ROOK, chess.BLACK), (chess.QUEEN, chess.BLACK), (chess.KING, chess.BLACK)],
                       "unic": "♟♞♝♜♛♚ ♙♘♗♖♕♔",
                       "ascii": "PNBRQK.pnbrqk"}
        self.chesssym = {"unic": ["-", "×", "†", "‡", "½"],
                         "ascii": ["-", "x", "+", "#", "1/2"]}

        # TODO: this seems to set windows terminal to Unicode. There should be a better way.
        if platform.system().lower() == 'windows':
            from ctypes import windll, c_int, byref
            stdout_handle = windll.kernel32.GetStdHandle(c_int(-11))
            mode = c_int(0)
            windll.kernel32.GetConsoleMode(c_int(stdout_handle), byref(mode))
            mode = c_int(mode.value | 4)
            windll.kernel32.SetConsoleMode(c_int(stdout_handle), mode)

        self.keyboard_handler()

    def agent_ready(self):
        return self.active

    def position_to_text(self, board, use_unicode_chess_figures=True):
        tpos = []
        tpos.append(
            "  +------------------------+")
        for y in reversed(range(8)):
            ti = "{} |".format(y+1)
            for x in range(8):
                f = board.piece_at(chess.square(x, y))
                if (x+y) % 2 == 0 and use_unicode_chess_figures is True:
                    invinv = False
                else:
                    invinv = True
                c = '?'
                # for i in range(len(self.figrep['int'])):
                if f == None:
                    c = ' '
                else:
                    if use_unicode_chess_figures is True:
                        c = f.unicode_symbol(invert_color=invinv)
                    else:
                        c = f.symbol()
                    # if ((self.figrep['pythc'][i][1] == f.color) == inv) and self.figrep['pythc'][i][0] == f.piece_type:
                    #     if use_unicode_chess_figures is True:
                    #         c = self.figrep['unic'][i]
                    #     else:
                    #         c = self.figrep['ascii'][i]
                    # break
                if (x+y) % 2 == 0:
                    ti += "\033[7m {} \033[m".format(c)
                else:
                    ti += " {} ".format(c)
            ti += "|"
            tpos.append(ti)
        tpos.append(
            "  +------------------------+")
        tpos.append("    A  B  C  D  E  F  G  H  ")
        return tpos

    def moves_to_text(self, board, score=None, use_unicode_chess_figures=True, lines=11):
        ams = ["" for _ in range(11)]
        mc = len(board.move_stack)
        if board.turn == chess.BLACK:
            mmc = 2*lines-1
        else:
            mmc = 2*lines
        if mc > mmc:
            mc = mmc
        move_store = []

        amsi = lines-1
        for i in range(mc):
            if amsi < 0:
                logging.error("bad amsi index! {}".format(amsi))
            if board.is_checkmate() is True:
                if use_unicode_chess_figures is True:
                    chk = self.chesssym['unic'][3]
                else:
                    chk = self.chesssym['ascii'][3]
            elif board.is_check() is True:
                if use_unicode_chess_figures is True:
                    chk = self.chesssym['unic'][2]
                else:
                    chk = self.chesssym['ascii'][2]
            else:
                chk = ""
            l1 = len(board.piece_map())
            mv = board.pop()
            l2 = len(board.piece_map())
            move_store.append(mv)
            if l1 != l2:  # capture move, piece count changed :-/
                if use_unicode_chess_figures is True:
                    sep = self.chesssym['unic'][1]
                else:
                    sep = self.chesssym['ascii'][1]
            else:
                if use_unicode_chess_figures is True:
                    sep = self.chesssym['unic'][0]
                else:
                    sep = self.chesssym['ascii'][0]
            if mv.promotion is not None:
                fig = chess.Piece(chess.PAWN, board.piece_at(
                    mv.from_square).color).unicode_symbol(invert_color=True)
                if use_unicode_chess_figures is True:
                    pro = chess.Piece(mv.promotion, board.piece_at(
                        mv.from_square).color).unicode_symbol(invert_color=True)
                else:
                    pro = mv.promotion.symbol()
            else:
                pro = ""
                if use_unicode_chess_figures is True:
                    fig = board.piece_at(mv.from_square).unicode_symbol(
                        invert_color=True)
                else:
                    fig = board.piece_at(mv.from_square).symbol()
            move = '{:10s}'.format(
                fig+" "+chess.SQUARE_NAMES[mv.from_square]+sep+chess.SQUARE_NAMES[mv.to_square]+pro+chk)
            if amsi == lines-1 and score != None:
                move = '{} ({})'.format(move, score)
                score = ''

            ams[amsi] = move + ams[amsi]
            if board.turn == chess.WHITE:
                ams[amsi] = "{:3d}. ".format(board.fullmove_number) + ams[amsi]
                amsi = amsi-1

        for i in reversed(range(len(move_store))):
            board.push(move_store[i])

        return ams

    def display_board(self, board):
        txa = self.position_to_text(board)
        ams = self.moves_to_text(board, lines=len(txa))
        for i in range(len(txa)):
            print('{}  {}'.format(txa[i], ams[i]))

    def display_info(self, board, info):
        st = '['
        if 'score' in info:
            st += 'Eval: {} '.format(info['score'])
        if 'nps' in info:
            st += 'Nps: {} '.format(info['nps'])
        if 'depth' in info:
            d = 'Depth: {}'.format(info['depth'])
            if 'seldepth' in info:
                d += '/{} '.format(info['seldepth'])
            else:
                d += ' '
            st += d
        if 'variant' in info:
            moves = info['variant']
            mvs = len(moves)
            if mvs > self.max_plies:
                mvs = self.max_plies
            for i in range(mvs):
                st += moves[i].uci()+' '
        print(st, end='\r')

    def set_valid_moves(self, board, vals):
        self.kbd_moves = []
        if vals != None:
            for v in vals:
                self.kbd_moves.append(vals[v])

    def kdb_event_worker_thread(self, appque, log, std_in):
        while self.kdb_thread_active:
            self.active = True
            cmd = ""
            try:
                # cmd = input()
                # with open(std_in) as inp:
                cmd = std_in.readline().strip()
            except Exception as e:
                log.info("Exception in input() {}".format(e))
                time.sleep(1.0)
            if cmd == "":
                continue
            log.debug("keyboard: <{}>".format(cmd))
            if len(cmd) >= 1:
                if cmd in self.kbd_moves:
                    self.kbd_moves = []
                    appque.put(
                        {'move': {'uci': cmd, 'actor': self.name}})
                elif cmd == 'n':
                    log.debug('requesting new game')
                    appque.put({'new game': '', 'actor': self.name})
                elif cmd == 'b':
                    log.debug('move back')
                    appque.put({'back': '', 'actor': self.name})
                elif cmd == 'c':
                    log.debug('change board orientation')
                    appque.put(
                        {'turn eboard orientation': '', 'actor': self.name})
                elif cmd == 'a':
                    log.debug('analyze')
                    appque.put({'analyze': '', 'actor': self.name})
                elif cmd == 'ab':
                    log.debug('analyze black')
                    appque.put({'analyze': 'black', 'actor': self.name})
                elif cmd == 'aw':
                    log.debug('analyze white')
                    appque.put({'analyze': 'white', 'actor': self.name})
                elif cmd == 'e':
                    log.debug('board encoding switch')
                    appque.put({'encoding': '', 'actor': self.name})
                elif cmd[:2] == 'l ':
                    log.debug('level')
                    movetime = float(cmd[2:])
                    appque.put({'level': '', 'movetime': movetime})
                elif cmd[:2] == 'm ':
                    log.debug('max ply look-ahead display')
                    n = int(cmd[2:])
                    appque.put({'max_ply': n})
                elif cmd == 'p':
                    log.debug('position')
                    appque.put({'position': '', 'actor': self.name})
                elif cmd == 'g':
                    log.debug('go')
                    appque.put({'go': 'current', 'actor': self.name})
                elif cmd == 'gw':
                    log.debug('go')
                    appque.put({'go': 'white', 'actor': self.name})
                elif cmd == 'gb':
                    log.debug('go, black')
                    appque.put({'go': 'black', 'actor': self.name})
                elif cmd == 'w':
                    appque.put({'write_prefs': ''})
                elif cmd[:2] == 'h ':
                    log.debug('show analysis for n plies (max 4) on board.')
                    ply = int(cmd[2:])
                    if ply < 0:
                        ply = 0
                    if ply > 4:
                        ply = 4
                    appque.put({'hint': '', 'ply': ply})

                elif cmd == 's':
                    log.debug('stop')
                    appque.put({'stop': '', 'actor': self.name})
                elif cmd[:4] == 'fen ':
                    appque.put({'fen': cmd[4:], 'actor': self.name})
                elif cmd == 'help':
                    log.info(
                        'a - analyze current position, ab: analyze black, aw: analyses white')
                    log.info(
                        'c - change cable orientation (eboard cable left/right')
                    log.info('b - take back move')
                    log.info('g - go, current player (default white)')
                    log.info('gw - go, force white move')
                    log.info('gb - go, force black move')
                    log.info('h <ply> - show hints for <ply> levels on board')
                    log.info('l <n> - level: engine think-time in sec (float)')
                    log.info('m <n> - max plies shown during look-ahead')
                    log.info('n - new game')
                    log.info('p - import eboard position')
                    log.info('s - stop')
                    log.info('w - write current prefences as default')
                    log.info('e2e4 - valid move')
                else:
                    log.info(
                        'Unknown keyboard cmd <{}>, enter "help" for a list of valid commands.'.format(cmd))

    def keyboard_handler(self):
        self.kdb_thread_active = True
        self.kbd_event_thread = threading.Thread(
            target=self.kdb_event_worker_thread, args=(self.appque, self.log, sys.stdin))
        self.kbd_event_thread.setDaemon(True)
        self.kbd_event_thread.start()