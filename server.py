import socket
import sys
from collections import OrderedDict
from pickle import loads
from random import randint
from threading import Thread
from time import time

import config


class Server:
    __sock = "socket.socket()"
    __quantity_users = 0
    __pairs_port = OrderedDict()
    __is_ready_field = {}
    __still_waiting = {}

    def __init__(self):
        self.__sock = socket.socket()
        self.__sock.bind((config.HOST, config.PORT))
        self.__sock.listen()
        self.__endless_loop()

    def __endless_loop(self):
        while True:
            client1, address = self.__sock.accept()
            print('connected:', address)
            self.__quantity_users += 1
            self.__still_waiting[client1] = "waiting"
            if self.__quantity_users % 2 == 0:
                client2, _ = self.__pairs_port.popitem()
                self.__pairs_port[client2] = client1
                self.__pairs_port[client1] = client2
                is_first = bool(randint(0, 1))
                self.__is_ready_field[client1] = False
                self.__is_ready_field[client2] = False
                t = Thread(target=self.__recv_state_waiting, args=(client1,))
                t.start()
                thread1 = Thread(target=self.__run, args=(client1, is_first))
                thread2 = Thread(target=self.__run, args=(client2, not is_first))
                thread1.start()
                thread2.start()
            else:
                self.__pairs_port[client1] = 0
                thread = Thread(target=self.__waiting_opponent, args=(client1,))
                thread.start()

    def __waiting_opponent(self, conn):
        number = self.__quantity_users
        t = Thread(target=self.__recv_state_waiting, args=(conn,))
        t.start()
        while number == self.__quantity_users and self.__still_waiting[conn] != "connect":
            if self.__still_waiting[conn] == "disconnect":
                print("disconnected:", conn.getpeername())
                self.__pairs_port.popitem()
                self.__quantity_users -= 1
                break

    def __recv_state_waiting(self, conn):
        conn.settimeout(1)
        start_time = time()
        mem_lim = 128
        data = bytes("", encoding="UTF-8")
        while not data.decode("UTF-8"):
            if time() - start_time >= config.TIME_WAITING_OPPONENT + 1:
                self.__still_waiting[conn] = "disconnect"
                return
            try:
                data = conn.recv(mem_lim)
            except TimeoutError:
                pass
        self.__still_waiting[conn] = data.decode("UTF-8")
        print(self.__still_waiting[conn])

    @staticmethod
    def __recv_str(conn):
        mem_lim = 128
        conn.settimeout(1)
        try:
            print(0)
            data = 0
            while not data:
                print(1)
                data = conn.recv(mem_lim)
        except TimeoutError:
            return 0
        except ConnectionResetError:
            return 0
        return data.decode("UTF-8")

    @staticmethod
    def __recv_tuple(conn):
        mem_lim = 256
        time_wait = config.TIME_WAITING_MOVE
        print(2)
        conn.settimeout(time_wait)
        print(3)
        try:
            data = 0
            print(4)
            while not data:
                print(5)
                data = conn.recv(mem_lim)
            print(6)
        except TimeoutError:
            return 0
        except ConnectionResetError:
            return 0
        print(7)
        return tuple(data)

    def __request(self, conn, data):
        print(8)
        conn.send(bytes(data))
        print(9)
        return self.__recv_str(conn)

    @staticmethod
    def __recv_field(conn):
        mem_lim = 2048
        time_wait = config.TIME_WAITING_CONSTRUCTOR_FIELD + config.TIME_WAITING_LOADING_WINDOW
        conn.settimeout(time_wait)
        try:
            data = 0
            while not data:
                print("field")
                data = conn.recv(mem_lim)
                print("done")
            return data
        except TimeoutError:
            return 0
        except ValueError:
            return 0
        except EOFError:
            return 0
        except ConnectionResetError:
            return 0

    def __run(self, client, is_first):
        number_player = 2 - is_first
        client.send(bytes(number_player))
        while self.__still_waiting[client] == "waiting":
            print(10)
            pass
        data = self.__recv_field(client)
        print(11)
        self.__is_ready_field[client] = True
        print(12)
        try:
            while not self.__is_ready_field[self.__pairs_port[client]]:
                pass
            self.__pairs_port[client].send(data)
            print(13)
            if loads(data):
                print(14)
                print(sys.getsizeof(data))
                print(15)
            else:
                # print("ROUND")
                print(16)
                self.__remove_client(client)
                print(17)
                return
            if is_first:
                is_my_turn = is_first
                while True:
                    print(18)
                    if is_my_turn:
                        print(19)
                        data = self.__recv_tuple(client)
                        req = self.__request(self.__pairs_port[client], data)
                    else:
                        print(20)
                        data = self.__recv_tuple(self.__pairs_port[client])
                        print(20.5)
                        req = self.__request(client, data)
                        print(20.9)
                    if not req:
                        print(21)
                        self.__remove_client(client)
                        # print("ROUND")
                        break
                    elif req == "same":
                        print(22)
                        is_my_turn = is_my_turn
                    elif req == "other":
                        print(23)
                        is_my_turn = not is_my_turn
        except KeyError:
            print(24)
            pass
        except TimeoutError:
            print(25)
            try:
                self.__remove_client(self.__pairs_port[client])
            except KeyError:
                pass
            try:
                self.__remove_client(client)
            except KeyError:
                pass

    def __remove_client(self, client):
        if client in self.__is_ready_field.keys():
            self.__is_ready_field.pop(client)
        if client in self.__pairs_port.keys():
            self.__pairs_port.pop(client)


Server()
