# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Library for parsing valve data files (vdf) '''
import struct

class BinaryVDFParser:
    ''' Class used to parse VDF files '''
    def __init__(self, file):
        self.file = file

    def _read_uint32(self):
        return struct.unpack("<I", self.file.read(4))[0]

    def _read_uint64(self):
        return struct.unpack("<Q", self.file.read(8))[0]

    def _read_string(self):
        chars = []
        while True:
            byte = self.file.read(1)
            if byte == b'\x00' or byte == b'':
                break
            chars.append(byte)
        return b''.join(chars).decode("utf-8", errors="replace")

    def _read_entry(self):
        entry_type = self.file.read(1)
        if not entry_type or entry_type == b'\x08':  # end marker
            return None, None, True

        name = self._read_string()

        if entry_type == b'\x00':  # nested dictionary
            value = self._read_dict()
        elif entry_type == b'\x01':  # string
            value = self._read_string()
        elif entry_type == b'\x02':  # uint32
            value = self._read_uint32()
        elif entry_type == b'\x07':  # uint64
            value = self._read_uint64()
        else:
            raise ValueError(f"Unknown type: {entry_type}")

        return name, value, False

    def _read_dict(self):
        result = {}
        while True:
            name, value, done = self._read_entry()
            if done:
                break
            result[name] = value
        return result

    def parse_shortcut(self, path):
        ''' parses a vdf shortcut '''
        with open(path, "rb") as f:
            self.file = f
            return self._read_dict()
    