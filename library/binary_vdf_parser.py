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

    def parse_shortcut(self, path: str):
        ''' parses a vdf shortcut '''
        with open(path, "rb") as f:
            self.file = f
            return self._read_dict()

    def _write_string(self, s: str):
        self.file.write(s.encode('utf-8') + b'\x00')

    def _write_entry(self, key: str, value):
        if isinstance(value, dict):
            self.file.write(b'\x00')  # nested dict
            self._write_string(key)
            self._write_dict(value)
        elif isinstance(value, str):
            self.file.write(b'\x01')  # string
            self._write_string(key)
            self._write_string(value)
        elif isinstance(value, int):
            if value <= 0xFFFFFFFF:
                self.file.write(b'\x02')  # uint32
                self._write_string(key)
                self.file.write(struct.pack("<I", value))
            else:
                self.file.write(b'\x07')  # uint64
                self._write_string(key)
                self.file.write(struct.pack("<Q", value))
        else:
            raise TypeError(f"Unsupported value type for key '{key}': {type(value)}")

    def _write_dict(self, d: dict):
        for key, value in d.items():
            self._write_entry(key, value)
        self.file.write(b'\x08')  # end of dict marker

    def save_shortcut(self, path: str, data: dict):
        '''Write back to the shortcuts.vdf file'''
        with open(path, "wb") as f:
            self.file = f
            self._write_dict(data)
