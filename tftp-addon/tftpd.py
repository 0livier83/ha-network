#!/usr/bin/env python3
"""Minimal TFTP read-only server (RFC 1350)."""
import socket, struct, os

TFTP_DIR = "/share"
BLOCK_SIZE = 512


def send_data(sock, addr, block, data):
    sock.sendto(struct.pack("!HH", 3, block) + data, addr)


def send_error(sock, addr, code, msg):
    sock.sendto(struct.pack("!HH", 5, code) + msg.encode() + b"\x00", addr)


def handle_rrq(sock, addr, filename):
    filepath = os.path.join(TFTP_DIR, filename)
    print(f"[TFTP] RRQ '{filename}' from {addr[0]}:{addr[1]}")
    if not os.path.isfile(filepath):
        print(f"[TFTP] File not found: {filepath}")
        send_error(sock, addr, 1, "File not found")
        return
    with open(filepath, "rb") as f:
        block = 1
        while True:
            data = f.read(BLOCK_SIZE)
            send_data(sock, addr, block, data)
            try:
                sock.settimeout(5)
                ack, _ = sock.recvfrom(1024)
                opcode, ack_block = struct.unpack("!HH", ack[:4])
                if opcode == 4 and ack_block == block:
                    if len(data) < BLOCK_SIZE:
                        print(f"[TFTP] Done: {block} blocks sent")
                        break
                    block += 1
                else:
                    print(f"[TFTP] Bad ACK: opcode={opcode} block={ack_block}")
                    break
            except socket.timeout:
                print(f"[TFTP] Timeout at block {block}")
                break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 69))
    print(f"[TFTP] Listening on 0.0.0.0:69")
    print(f"[TFTP] Files: {os.listdir(TFTP_DIR)}")
    while True:
        sock.settimeout(None)
        data, addr = sock.recvfrom(1024)
        opcode = struct.unpack("!H", data[:2])[0]
        if opcode == 1:
            filename = data[2:].split(b"\x00")[0].decode()
            handle_rrq(sock, addr, filename)


if __name__ == "__main__":
    main()
